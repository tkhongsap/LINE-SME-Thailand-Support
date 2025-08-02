import os
import logging
from openai import AzureOpenAI
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)

class OpenAIService:
    """Simplified direct Azure OpenAI integration for Replit deployment"""
    
    def __init__(self):
        """Initialize Azure OpenAI client with Replit environment variables"""
        self.api_key = os.environ.get('AZURE_OPENAI_API_KEY')
        self.endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
        self.deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1-nano')
        self.api_version = "2024-02-01"
        
        if not self.api_key or not self.endpoint:
            raise ValueError("Missing Azure OpenAI configuration. Check AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")
        
        # Initialize client
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
        
        logging.info(f"Azure OpenAI client initialized - Endpoint: {self.endpoint}")
    
    def generate_response(self, user_message: str, language: str = 'th') -> str:
        """
        Generate response using direct Azure OpenAI call
        
        Args:
            user_message: User's input message
            language: Response language ('th' for Thai, 'en' for English)
        
        Returns:
            Generated response text
        """
        # Define fallback messages before try block
        if language == 'th':
            fallback_message = "ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"
        else:
            fallback_message = "Sorry, an error occurred. Please try again."
            
        try:
            # Simple but effective prompt template for Thai SME
            if language == 'th':
                system_prompt = """คุณเป็นผู้ช่วย AI สำหรับ SME ไทย ที่เป็นมิตรและให้ความช่วยเหลือ
ตอบคำถามเกี่ยวกับธุรกิจ การเงิน การตลาด และเทคโนโลยี
ใช้ภาษาไทยที่เข้าใจง่าย เป็นมิตร และให้คำแนะนำที่เป็นประโยชน์"""
            else:
                system_prompt = """You are a helpful AI assistant for Thai SMEs (Small and Medium Enterprises).
Provide practical advice on business, finance, marketing, and technology.
Be friendly, clear, and give actionable recommendations."""
            
            # Make direct API call with timeout
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7,
                timeout=5.0  # 5 second timeout for Replit optimization
            )
            
            result = response.choices[0].message.content
            if result:
                logging.info(f"OpenAI response generated successfully (length: {len(result)})")
                return result
            else:
                logging.warning("Empty response from OpenAI API")
                return fallback_message
            
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return fallback_message
    
    def test_connection(self) -> bool:
        """Test Azure OpenAI connectivity for health checks"""
        try:
            test_response = self.generate_response("Hello", "en")
            return len(test_response) > 0
        except:
            return False

# Global instance for simplified usage
_openai_service = None

def get_openai_service() -> OpenAIService:
    """Get or create OpenAI service instance"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service

def generate_response(user_message: str, language: str = 'th') -> str:
    """Simplified function for direct usage"""
    service = get_openai_service()
    return service.generate_response(user_message, language)