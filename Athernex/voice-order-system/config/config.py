"""Configuration management for the voice order system."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Service Endpoints
    whisper_endpoint: str = "http://localhost:8000"
    vosk_endpoint: str = "http://localhost:8001"
    ollama_endpoint: str = "http://localhost:11434"
    piper_endpoint: str = "http://localhost:8002"
    
    # Model Configuration
    whisper_model: str = "medium"
    ollama_model: str = "llama3.1:8b-instruct-q4_K_M"
    
    # Confidence Thresholds
    threshold_place_order: float = 0.85
    threshold_modify_order: float = 0.80
    threshold_cancel_order: float = 0.90
    threshold_confirm_order: float = 0.85
    threshold_check_status: float = 0.70
    threshold_request_info: float = 0.70
    
    # Rate Limits (requests per minute)
    rate_limit_whisper: int = 10
    rate_limit_ollama: int = 5
    rate_limit_piper: int = 50
    
    # Resource Limits
    max_concurrent_requests: int = 10
    gpu_memory_limit_mb: int = 7500
    cpu_percent_limit: int = 80
    
    # Cache Configuration
    llm_cache_size: int = 1000
    tts_cache_size: int = 500
    cache_ttl_seconds: int = 3600
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Hugging Face (Fallback)
    hf_api_key: str = ""
    
    # Telephony (Twilio)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_base_url: str = "https://your-server.com"  # Your public URL for webhooks
    
    @property
    def intent_thresholds(self) -> Dict[str, float]:
        """Get intent-specific confidence thresholds."""
        return {
            "place_order": self.threshold_place_order,
            "modify_order": self.threshold_modify_order,
            "cancel_order": self.threshold_cancel_order,
            "confirm_order": self.threshold_confirm_order,
            "check_status": self.threshold_check_status,
            "request_information": self.threshold_request_info,
        }


# Global settings instance
settings = Settings()
