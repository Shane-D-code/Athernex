"""
Twilio Integration Handler for Phone Calls.

Handles incoming/outgoing calls, STT/TTS via Twilio,
and integrates with the voice order pipeline.
"""

import logging
from typing import Optional, Dict, Any
from twilio.twiml.voice_response import VoiceResponse, Gather, Say
from twilio.rest import Client

logger = logging.getLogger(__name__)


class TwilioHandler:
    """
    Twilio telephony handler.
    
    Manages phone calls using Twilio's API and TwiML.
    Integrates with the voice order pipeline for processing.
    """
    
    # Language mapping: system language → Twilio language code
    LANGUAGE_MAP = {
        "hi": "hi-IN",      # Hindi (India)
        "en": "en-IN",      # English (India)
        "kn": "kn-IN",      # Kannada (India)
        "mr": "mr-IN",      # Marathi (India)
        "hinglish": "hi-IN" # Hinglish → Hindi voice
    }
    
    # Voice mapping for better quality
    VOICE_MAP = {
        "hi-IN": "Polly.Aditi",      # Hindi female voice
        "en-IN": "Polly.Raveena",    # English Indian female
        "kn-IN": "Polly.Aditi",      # Use Hindi voice for Kannada
        "mr-IN": "Polly.Aditi",      # Use Hindi voice for Marathi
    }
    
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        phone_number: str,
        base_url: str = "https://your-server.com"
    ):
        """
        Initialize Twilio handler.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            phone_number: Your Twilio phone number
            base_url: Your server's public URL (for webhooks)
        """
        self.client = Client(account_sid, auth_token)
        self.phone_number = phone_number
        self.base_url = base_url.rstrip("/")
        
        logger.info("TwilioHandler initialized with number: %s", phone_number)
    
    def get_twilio_language(self, system_language: str) -> str:
        """Convert system language code to Twilio language code."""
        return self.LANGUAGE_MAP.get(system_language, "hi-IN")
    
    def get_voice(self, twilio_language: str) -> str:
        """Get appropriate voice for language."""
        return self.VOICE_MAP.get(twilio_language, "Polly.Aditi")
    
    def create_greeting_response(
        self,
        greeting_text: str,
        language: str = "hi"
    ) -> str:
        """
        Create TwiML response for initial greeting.
        
        Args:
            greeting_text: Greeting message to speak
            language: System language code
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        twilio_lang = self.get_twilio_language(language)
        voice = self.get_voice(twilio_lang)
        
        # Speak greeting
        response.say(
            greeting_text,
            language=twilio_lang,
            voice=voice
        )
        
        # Gather speech input
        gather = Gather(
            input="speech",
            action=f"{self.base_url}/twilio/process-speech",
            method="POST",
            language=twilio_lang,
            speech_timeout="auto",
            timeout=5,
            hints="pizza, burger, order, cancel"  # Help STT accuracy
        )
        response.append(gather)
        
        # Fallback if no speech detected
        response.say(
            "मुझे सुनाई नहीं दिया। कृपया दोबारा कॉल करें।",
            language=twilio_lang,
            voice=voice
        )
        response.hangup()
        
        return str(response)
    
    def create_speech_response(
        self,
        bot_text: str,
        continue_conversation: bool = True,
        language: str = "hi",
        is_final: bool = False
    ) -> str:
        """
        Create TwiML response for bot's speech.
        
        Args:
            bot_text: Text for bot to speak
            continue_conversation: Whether to continue listening
            language: System language code
            is_final: Whether this is the final message (end call)
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        twilio_lang = self.get_twilio_language(language)
        voice = self.get_voice(twilio_lang)
        
        # Speak bot's response
        response.say(
            bot_text,
            language=twilio_lang,
            voice=voice
        )
        
        if is_final:
            # End call
            response.hangup()
        elif continue_conversation:
            # Continue listening
            gather = Gather(
                input="speech",
                action=f"{self.base_url}/twilio/process-speech",
                method="POST",
                language=twilio_lang,
                speech_timeout="auto",
                timeout=5
            )
            response.append(gather)
            
            # Fallback
            response.say(
                "धन्यवाद! अलविदा।",
                language=twilio_lang,
                voice=voice
            )
            response.hangup()
        else:
            # Just hang up
            response.hangup()
        
        return str(response)
    
    def create_error_response(
        self,
        error_message: str,
        language: str = "hi"
    ) -> str:
        """
        Create TwiML response for errors.
        
        Args:
            error_message: Error message to speak
            language: System language code
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        twilio_lang = self.get_twilio_language(language)
        voice = self.get_voice(twilio_lang)
        
        response.say(
            error_message,
            language=twilio_lang,
            voice=voice
        )
        response.hangup()
        
        return str(response)
    
    def create_no_speech_response(
        self,
        language: str = "hi"
    ) -> str:
        """
        Create TwiML response when no speech detected.
        
        Args:
            language: System language code
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        twilio_lang = self.get_twilio_language(language)
        voice = self.get_voice(twilio_lang)
        
        messages = {
            "hi": "मुझे सुनाई नहीं दिया। कृपया दोबारा बोलें।",
            "en": "I didn't hear you. Please speak again.",
            "kn": "ನನಗೆ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಮಾತನಾಡಿ.",
            "mr": "मला ऐकू आले नाही. कृपया पुन्हा बोला.",
        }
        
        message = messages.get(language, messages["hi"])
        
        response.say(message, language=twilio_lang, voice=voice)
        
        # Try again
        gather = Gather(
            input="speech",
            action=f"{self.base_url}/twilio/process-speech",
            method="POST",
            language=twilio_lang,
            speech_timeout="auto"
        )
        response.append(gather)
        
        # Final fallback
        response.say(
            "धन्यवाद। अलविदा।",
            language=twilio_lang,
            voice=voice
        )
        response.hangup()
        
        return str(response)
    
    def make_outbound_call(
        self,
        to_number: str,
        greeting_text: str,
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Make an outbound call to a customer.
        
        Args:
            to_number: Customer's phone number (E.164 format)
            greeting_text: Initial greeting message
            language: System language code
            
        Returns:
            Dict with call_sid and status
        """
        try:
            # Create TwiML for outbound call
            twiml = self.create_greeting_response(greeting_text, language)
            
            # Make the call
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                twiml=twiml
            )
            
            logger.info("Outbound call initiated: %s to %s", call.sid, to_number)
            
            return {
                "call_sid": call.sid,
                "status": call.status,
                "to": to_number,
                "from": self.phone_number
            }
            
        except Exception as e:
            logger.error("Failed to make outbound call: %s", e)
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """
        Get status of a call.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Dict with call details
        """
        try:
            call = self.client.calls(call_sid).fetch()
            
            return {
                "call_sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "from": call.from_,
                "to": call.to,
                "direction": call.direction
            }
        except Exception as e:
            logger.error("Failed to get call status: %s", e)
            return {"error": str(e)}
    
    def hangup_call(self, call_sid: str) -> bool:
        """
        Hang up an active call.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            True if successful
        """
        try:
            self.client.calls(call_sid).update(status="completed")
            logger.info("Call hung up: %s", call_sid)
            return True
        except Exception as e:
            logger.error("Failed to hang up call: %s", e)
            return False


# Singleton instance
_twilio_handler: Optional[TwilioHandler] = None


def get_twilio_handler(
    account_sid: Optional[str] = None,
    auth_token: Optional[str] = None,
    phone_number: Optional[str] = None,
    base_url: Optional[str] = None
) -> TwilioHandler:
    """
    Get or create singleton Twilio handler.
    
    Args:
        account_sid: Twilio account SID (required on first call)
        auth_token: Twilio auth token (required on first call)
        phone_number: Your Twilio phone number (required on first call)
        base_url: Your server's public URL (required on first call)
        
    Returns:
        TwilioHandler instance
    """
    global _twilio_handler
    
    if _twilio_handler is None:
        if not all([account_sid, auth_token, phone_number, base_url]):
            raise ValueError(
                "First call to get_twilio_handler requires all parameters"
            )
        
        _twilio_handler = TwilioHandler(
            account_sid=account_sid,
            auth_token=auth_token,
            phone_number=phone_number,
            base_url=base_url
        )
    
    return _twilio_handler
