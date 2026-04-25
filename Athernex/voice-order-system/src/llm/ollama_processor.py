"""
Ollama LLM processor for local LLaMA 3.1 8B model.

Connects to Ollama server running on port 11434.
Handles intent detection and structured data extraction.
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any

import httpx
from pydantic import ValidationError

from .base import LLMProcessor, LLMResponse, StructuredOrderData, Intent, OrderItem

logger = logging.getLogger(__name__)


class OllamaLLMProcessor(LLMProcessor):
    """
    Client for Ollama API running LLaMA 3.1 8B (or compatible models).
    
    Start Ollama with: ollama serve
    Pull model with: ollama pull llama3.1:8b-instruct-q4_K_M
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b-instruct-q4_K_M",
        timeout: float = 30.0,
        max_tokens: int = 1000,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self._client = httpx.AsyncClient(timeout=timeout)
        self._few_shot_examples = self._get_default_examples()

    @property
    def name(self) -> str:
        return f"Ollama-{self.model}"

    def _get_default_examples(self) -> Dict[str, List[str]]:
        """Default few-shot examples for each intent."""
        return {
            "place_order": [
                "I want to order 2 pizzas for delivery at 7pm",
                "Can I get 3 burgers and 2 cokes delivered in 30 minutes?",
                "मुझे 2 डोसा चाहिए 6 बजे तक",  # Hindi
                "ನನಗೆ 1 ಬಿರಿಯಾನಿ ಬೇಕು",  # Kannada
            ],
            "modify_order": [
                "Change my order to 3 pizzas instead of 2",
                "Add one more burger to order #123",
                "मेरे ऑर्डर में एक और आइटम जोड़ दो",  # Hindi
            ],
            "cancel_order": [
                "Cancel my order please",
                "I want to cancel order number 456",
                "मेरा ऑर्डर कैंसल कर दो",  # Hindi
            ],
            "confirm_order": [
                "Yes, confirm my order",
                "That's correct, place the order",
                "हाँ, ऑर्डर कन्फर्म करो",  # Hindi
            ],
            "check_status": [
                "What's the status of my order?",
                "Where is order #789?",
                "मेरा ऑर्डर कहाँ है?",  # Hindi
            ],
            "request_information": [
                "What's on the menu?",
                "Do you have vegetarian options?",
                "क्या आपके पास वेज खाना है?",  # Hindi
            ],
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt with few-shot examples."""
        examples_text = ""
        for intent, examples in self._few_shot_examples.items():
            examples_text += f"\n{intent.upper()}:\n"
            for ex in examples:
                examples_text += f"- {ex}\n"

        return f"""You are an AI assistant for a multilingual voice order system. Extract structured order information from user utterances in Hindi, Kannada, Marathi, or English.

SUPPORTED INTENTS:
{examples_text}

RESPONSE FORMAT:
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

RULES:
1. Always respond with valid JSON only
2. Set confidence based on clarity of the utterance
3. List missing_fields if intent requires more information
4. Convert relative times to absolute ISO 8601 timestamps
5. Handle code-mixed speech (multiple languages in one utterance)
6. Extract quantities and units accurately
7. Preserve special instructions in the original language"""

    async def process_utterance(
        self, 
        text: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Process utterance through Ollama and extract structured data."""
        start_time = time.time()
        
        # Build the user prompt
        user_prompt = f"Extract order information from: '{text}'"
        if context:
            user_prompt += f"\nContext: {json.dumps(context, ensure_ascii=False)}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "num_predict": self.max_tokens,
                "temperature": 0.1,  # Low temperature for consistent JSON
            }
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            
            processing_time = time.time() - start_time
            raw_response = result.get("message", {}).get("content", "{}")
            
            # Parse the JSON response
            try:
                parsed_data = json.loads(raw_response)
                structured_data = self._parse_structured_data(parsed_data)
                
                return LLMResponse(
                    structured_data=structured_data,
                    raw_response=raw_response,
                    processing_time=processing_time,
                    model_used=self.model,
                    confidence=structured_data.confidence,
                )
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error("Failed to parse LLM response: %s", e)
                # Return fallback response
                return self._create_fallback_response(text, raw_response, processing_time)
                
        except httpx.HTTPStatusError as e:
            logger.error("Ollama HTTP error: %s - %s", e.response.status_code, e.response.text)
            raise
        except httpx.RequestError as e:
            logger.error("Ollama connection error: %s", e)
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
        """Check if Ollama server is reachable."""
        try:
            response = await self._client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def add_intent(self, intent: str, examples: List[str]) -> bool:
        """Add new intent with examples to the few-shot prompt."""
        if len(examples) < 3:
            logger.warning("Need at least 3 examples for new intent")
            return False
        
        self._few_shot_examples[intent] = examples
        logger.info("Added intent '%s' with %d examples", intent, len(examples))
        return True

    async def close(self):
        await self._client.aclose()