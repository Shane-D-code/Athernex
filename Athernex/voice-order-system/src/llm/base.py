"""Abstract base class for LLM processors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class Intent(str, Enum):
    """Supported order intents."""
    PLACE_ORDER = "place_order"
    MODIFY_ORDER = "modify_order"
    CANCEL_ORDER = "cancel_order"
    CONFIRM_ORDER = "confirm_order"
    CHECK_STATUS = "check_status"
    REQUEST_INFORMATION = "request_information"


@dataclass
class OrderItem:
    """A single item in an order."""
    name: str
    quantity: int
    unit: Optional[str] = None
    special_instructions: Optional[str] = None


@dataclass
class StructuredOrderData:
    """Structured data extracted from user utterance."""
    intent: Intent
    items: List[OrderItem] = field(default_factory=list)
    delivery_time: Optional[str] = None  # ISO 8601 timestamp
    special_instructions: Optional[str] = None
    order_id: Optional[str] = None  # For modify/cancel/check operations
    confidence: float = 0.0
    missing_fields: List[str] = field(default_factory=list)


@dataclass
class LLMResponse:
    """Response from LLM processor."""
    structured_data: StructuredOrderData
    raw_response: str
    processing_time: float
    model_used: str
    confidence: float = 0.0


class LLMProcessor(ABC):
    """Abstract interface for Language Model processors."""

    @abstractmethod
    async def process_utterance(
        self, 
        text: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Process user utterance and extract structured order data.

        Args:
            text: Transcribed user utterance
            context: Optional dialogue context (previous turns, session info)

        Returns:
            LLMResponse with structured data and metadata
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the LLM service is reachable and healthy."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable processor name."""

    @abstractmethod
    async def add_intent(self, intent: str, examples: List[str]) -> bool:
        """
        Add a new intent with few-shot examples.
        
        Args:
            intent: New intent name
            examples: 3-5 example utterances for this intent
            
        Returns:
            True if successfully added
        """