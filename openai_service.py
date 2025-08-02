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
        self.deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT',
                                         'gpt-4.1-nano')
        self.api_version = "2024-02-01"

        if not self.api_key or not self.endpoint:
            raise ValueError(
                "Missing Azure OpenAI configuration. Check AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT"
            )

        # Initialize client
        self.client = AzureOpenAI(api_key=self.api_key,
                                  api_version=self.api_version,
                                  azure_endpoint=self.endpoint)

        logging.info(
            f"Azure OpenAI client initialized - Endpoint: {self.endpoint}")

    def generate_response(self, user_message: str) -> str:
        """
        Generate response using direct Azure OpenAI call with universal language support
        
        Args:
            user_message: User's input message
        
        Returns:
            Generated response text
        """
        # Universal fallback message for any errors
        fallback_message = "ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง / Sorry, an error occurred. Please try again."

        try:
            # Optimized universal system prompt for faster processing
            system_prompt = """AI assistant for Thai SMEs. Respond in user's language. Give practical business, finance, marketing, and tech advice. Be friendly and clear."""

            # Make direct API call with extended timeout for natural completion
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{
                    "role": "system",
                    "content": system_prompt
                }, {
                    "role": "user",
                    "content": user_message
                }],
                max_tokens=500,
                temperature=0.7,
                timeout=30.0  # Extended timeout for complex queries
            )

            result = response.choices[0].message.content
            if result:
                logging.info(
                    f"OpenAI response generated successfully (length: {len(result)})"
                )
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
            test_response = self.generate_response("Hello")
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


def generate_response(user_message: str) -> str:
    """Simplified function for direct usage with universal language support"""
    service = get_openai_service()
    return service.generate_response(user_message)
