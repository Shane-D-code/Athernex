"""Test script for LLM processors."""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm import OllamaLLMProcessor


async def test_ollama():
    """Test Ollama processor with available model."""
    # Try with the smaller Phi3 model first
    processor = OllamaLLMProcessor(model="phi3:latest")
    
    try:
        # Health check
        healthy = await processor.health_check()
        print(f"✓ Ollama health check: {healthy}")
        
        if healthy:
            # Simple test
            response = await processor.process_utterance("I want 2 pizzas")
            print(f"✓ Intent: {response.structured_data.intent}")
            print(f"✓ Items: {response.structured_data.items}")
            print(f"✓ Confidence: {response.structured_data.confidence}")
            print(f"✓ Processing time: {response.processing_time:.2f}s")
            return True
        else:
            print("✗ Ollama not healthy")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        await processor.close()


if __name__ == "__main__":
    success = asyncio.run(test_ollama())
    exit(0 if success else 1)