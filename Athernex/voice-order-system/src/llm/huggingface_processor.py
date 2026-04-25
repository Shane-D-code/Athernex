"""
Hugging Face Inference API processor (fallback LLM).

Uses the free tier of Hugging Face Inference API when Ollama is unavailable.
Rate limited to 30 requests/hour on free tier.
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any

import httpx

from .base import LLMProcessor, LLMResponse, StructuredOrderData, Intent, OrderItem

logger = logging.getLogger(__name__)


class HuggingFaceLLMProcessor(LLMProcessor):
    """
    Client for Hugging Face Inference API using LLaMA 3.1 8B.
    
    Requires HF_API_KEY environment variable or explicit api_key parameter.
    Free tier: 30 requests/hour, 1000 requests/month.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "meta-llama/Llama-3.1-8B-Instruct",
        base_url: str = "https://api-inference.huggingface.co",
        timeout: float = 30.0,
        max_tokens: int = 1000,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_tokens = max_tokens
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        self._few_shot_examples = self._get_default_examples()

    @property
    def name(self) -> str:
        return f"HuggingFace-{self.model.split('/')[-1]}"

    def _get_default_examples(self) -> Dict[str, List[str]]:
        """Default few-shot examples for each intent."""
        return {
            "place_order": [
                "I want to order 2 pizzas for delivery at 7pm",
                "Can I get 3 burgers and 2 cokes delivered in 30 minutes?",
                "मुझे 2 डोसा चाहिए 6 बजे तक",  # Hindi
            ],
            "modify_order": [
                "Change my order to 3 pizzas instead of 2",
                "Add one more burger to order #123",
            ],
            "cancel_order": [
                "Cancel my order please",
                "I want to cancel order number 456",
            ],
            "confirm_order": [
                "Yes, confirm my order",
                "That's correct, place the order",
            ],
            "check_status": [
                "What's the status of my order?",
                "Where is order #789?",
            ],
            "request_information": [
                "What's on the menu?",
                "Do you have vegetarian options?",
            ],
        }

    def _build_prompt(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build the complete prompt for HF Inference API."""
        examples_text = ""
        for intent, examples in self._few_shot_examples.items():
            examples_text += f"\n{intent.upper()}:\n"
            for ex in examples[:2]:  # Limit examples for API length
                examples_text += f"- {ex}\n"

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an AI assistant for a multilingual voice order system. Extract structured order information from user utterances in Hindi, Kannada, Marathi, or English.

SUPPORTED INTENTS:
{examples_text}

Always respond with valid JSON in this exact structure:
{{
  "intent": "place_order|modify_order|cancel_order|confirm_order|check_status|request_information",
  "items": [
    {{
      "name": "item name",
      "quantity": number,
      "unit": "pieces|kg|liters|null",
      "special_instructions": "any special notes or null"
    }}
  ],
  "delivery_time": "ISO 8601 timestamp or null",
  "special_instructions": "overall order instructions or null",
  "order_id": "order ID for modify/cancel/check or null",
  "confidence": 0.0-1.0,
  "missing_fields": ["list of missing required fields"]
}}

Respond with JSON only.<|eot_id|><|start_header_id|>user<|end_header_id|>

Extract order information from: '{text}'"""

        if context:
            prompt += f"\nContext: {json.dumps(context, ensure_ascii=False)}"

        prompt += "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        return prompt

    async def process_utterance(
        self, 
        text: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Process utterance through HF Inference API."""
        start_time = time.time()
        
        prompt = self._build_prompt(text, context)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": self.max_tokens,
                "temperature": 0.1,
                "do_sample": True,
                "return_full_text": False,
            }
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/models/{self.model}",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            
            processing_time = time.time() - start_time
            
            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                raw_response = result[0].get("generated_text", "{}")
            else:
                raw_response = result.get("generated_text", "{}")
            
            # Extract JSON from response (may have extra text)
            try:
                # Find JSON in the response
                json_start = raw_response.find("{")
                json_end = raw_response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_text = raw_response[json_start:json_end]
                    parsed_data = json.loads(json_text)
                    structured_data = self._parse_structured_data(parsed_data)
                else:
                    raise json.JSONDecodeError("No JSON found", raw_response, 0)
                
                return LLMResponse(
                    structured_data=structured_data,
                    raw_response=raw_response,
                    processing_time=processing_time,
                    model_used=self.model,
                    confidence=structured_data.confidence,
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.error("Failed to parse HF response: %s", e)
                return self._create_fallback_response(text, raw_response, processing_time)
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("HF API rate limit exceeded")
            else:
                logger.error("HF HTTP error: %s - %s", e.response.status_code, e.response.text)
            raise
        except httpx.RequestError as e:
            logger.error("HF connection error: %s", e)
            raise

    def _parse_structured_data(self, data: Dict[str, Any]) -> StructuredOrderData:
        """Parse JSON response into StructuredOrderData."""
        # Parse items
        items = []
        for item_data in data.get("items", []):
            items.append(OrderItem(
                name=item_data.get("name", ""),
                quantity=item_data.get("quantity", 1),
                unit=item_data.get("unit"),
                special_instructions=item_data.get("special_instructions"),
            ))

        # Parse intent
        intent_str = data.get("intent", "request_information")
        try:
            intent = Intent(intent_str)
        except ValueError:
            intent = Intent.REQUEST_INFORMATION

        return StructuredOrderData(
            intent=intent,
            items=items,
            delivery_time=data.get("delivery_time"),
            special_instructions=data.get("special_instructions"),
            order_id=data.get("order_id"),
            confidence=data.get("confidence", 0.5),
            missing_fields=data.get("missing_fields", []),
        )

    def _create_fallback_response(
        self, text: str, raw_response: str, processing_time: float
    ) -> LLMResponse:
        """Create a fallback response when JSON parsing fails."""
        return LLMResponse(
            structured_data=StructuredOrderData(
                intent=Intent.REQUEST_INFORMATION,
                confidence=0.1,
                missing_fields=["intent", "items"],
            ),
            raw_response=raw_response,
            processing_time=processing_time,
            model_used=self.model,
            confidence=0.1,
        )

    async def health_check(self) -> bool:
        """Check if HF Inference API is reachable."""
        try:
            # Simple test request
            response = await self._client.post(
                f"{self.base_url}/models/{self.model}",
                json={"inputs": "test", "parameters": {"max_new_tokens": 1}},
                timeout=5.0
            )
            return response.status_code in [200, 429]  # 429 = rate limited but working
        except Exception:
            return False

    async def add_intent(self, intent: str, examples: List[str]) -> bool:
        """Add new intent with examples to the few-shot prompt."""
        if len(examples) < 3:
            logger.warning("Need at least 3 examples for new intent")
            return False
        
        self._few_shot_examples[intent] = examples[:3]  # Limit for API length
        logger.info("Added intent '%s' with %d examples", intent, len(examples))
        return True

    async def close(self):
        await self._client.aclose()