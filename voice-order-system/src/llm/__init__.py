"""LLM processor package — Ollama (primary) + HuggingFace (fallback)."""

from .base import (
    LLMProcessor,
    LLMResponse,
    StructuredOrderData,
    OrderItem,
    Intent,
)
from .ollama_processor import OllamaLLMProcessor
from .huggingface_processor import HuggingFaceLLMProcessor

__all__ = [
    "LLMProcessor",
    "LLMResponse",
    "StructuredOrderData",
    "OrderItem",
    "Intent",
    "OllamaLLMProcessor",
    "HuggingFaceLLMProcessor",
]