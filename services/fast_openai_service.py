"""
Fast OpenAI Service - Lightweight direct Azure OpenAI integration
Optimized for simple queries with minimal overhead and maximum speed
"""

import logging
import time
from typing import Dict, Optional
from openai import AzureOpenAI
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class FastOpenAIService:
    """
    Lightweight OpenAI service for fast path processing
    Bypasses heavy optimization layers for maximum speed
    """
    
    def __init__(self):
        self.config_valid = Config.validate_config()
        self.client = None
        self.deployment_name = None
        
        if self.config_valid:
            try:
                self.client = AzureOpenAI(
                    api_key=Config.AZURE_OPENAI_API_KEY,
                    api_version=Config.AZURE_OPENAI_API_VERSION,
                    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
                )
                self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT_NAME
                logger.info("Fast OpenAI service initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize Fast OpenAI client: {e}")
                self.config_valid = False
                self.client = None
        
        # Simple cache for common responses (in-memory only)
        self._response_cache = {}
        self._cache_max_size = 100
        
    def generate_fast_response(self, user_message: str, user_language: str = 'th') -> str:
        """
        Generate fast response for simple queries
        Direct Azure OpenAI call with minimal processing
        """
        start_time = time.time()
        
        if not self.config_valid or not self.client:
            logger.warning("Using development response - Azure OpenAI not configured")
            return self._get_dev_response(user_message, user_language)
        
        try:
            # Check cache first for common queries
            cache_key = f"{user_message.lower()}_{user_language}"
            if cache_key in self._response_cache:
                logger.info(f"Cache hit for fast response: {user_message[:30]}...")
                return self._response_cache[cache_key]
            
            # Build minimal messages for fast processing
            messages = self._build_fast_messages(user_message, user_language)
            
            # Direct Azure OpenAI call with optimized parameters
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=400,  # Shorter responses for speed
                temperature=0.3,  # Lower temperature for consistency
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            bot_response = response.choices[0].message.content.strip()
            
            # Cache common responses
            if len(self._response_cache) < self._cache_max_size:
                self._response_cache[cache_key] = bot_response
            
            elapsed_time = time.time() - start_time
            logger.info(f"Fast response generated in {elapsed_time:.2f}s for: {user_message[:30]}...")
            
            return bot_response
            
        except Exception as e:
            logger.error(f"Fast OpenAI generation failed: {e}")
            elapsed_time = time.time() - start_time
            logger.error(f"Failed after {elapsed_time:.2f}s")
            
            # Fallback to simple response
            return self._get_fallback_response(user_message, user_language)
    
    def _build_fast_messages(self, user_message: str, user_language: str) -> list:
        """Build minimal message structure for fast processing"""
        
        # Use lightweight system prompt based on language
        if user_language == 'th':
            system_prompt = """คุณเป็นผู้ช่วย AI สำหรับธุรกิจ SME ไทย
- ตอบสั้นและตรงประเด็น 
- ใช้ภาษาเป็นกันเองแต่สุภาพ
- ให้คำแนะนำที่เป็นประโยชน์"""
        else:
            system_prompt = """You are an AI assistant for Thai SME businesses.
- Respond concisely and directly
- Use friendly but professional language  
- Provide helpful actionable advice"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        return messages
    
    def _get_dev_response(self, user_message: str, user_language: str) -> str:
        """Development response when Azure OpenAI is not configured"""
        if user_language == 'th':
            return f"[พัฒนาระบบ] ได้รับข้อความ: {user_message[:50]}... ระบบ AI ยังไม่ได้ตั้งค่า"
        else:
            return f"[Development Mode] Received: {user_message[:50]}... AI system not configured"
    
    def _get_fallback_response(self, user_message: str, user_language: str) -> str:
        """Fallback response when Azure OpenAI fails"""
        fallback_responses = {
            'th': {
                'greeting': 'สวัสดีครับ! ยินดีที่ได้ช่วยเหลือธุรกิจของคุณ',
                'help': 'ฉันพร้อมช่วยเหลือเรื่องธุรกิจ SME ไทย ลองถามคำถามใหม่ดูครับ',
                'error': 'ขออภัย เกิดข้อผิดพลาดชั่วคราว กรุณาลองใหม่อีกครั้งครับ'
            },
            'en': {
                'greeting': 'Hello! I\'m here to help with your SME business.',
                'help': 'I\'m ready to assist with Thai SME business matters. Please try asking again.',
                'error': 'Sorry, there was a temporary error. Please try again.'
            }
        }
        
        lang_responses = fallback_responses.get(user_language, fallback_responses['en'])
        user_lower = user_message.lower()
        
        # Simple keyword matching for fallback
        if any(word in user_lower for word in ['สวัสดี', 'hello', 'hi', 'หวัดดี']):
            return lang_responses['greeting']
        elif any(word in user_lower for word in ['help', 'ช่วย', '/help']):
            return lang_responses['help']
        else:
            return lang_responses['error']
    
    def is_available(self) -> bool:
        """Check if the fast service is available"""
        return self.config_valid and self.client is not None
    
    def clear_cache(self):
        """Clear the response cache"""
        self._response_cache.clear()
        logger.info("Fast OpenAI response cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cache_size': len(self._response_cache),
            'max_size': self._cache_max_size,
            'hit_ratio': 'Not tracked in simple cache'
        }

# Global instance for fast access
fast_openai_service = FastOpenAIService()