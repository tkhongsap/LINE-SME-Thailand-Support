import logging
import base64
from openai import AzureOpenAI
from config import Config
from utils.logger import setup_logger
from prompts.sme_prompts import SMEPrompts

logger = setup_logger(__name__)

class OpenAIService:
    def __init__(self):
        self.config_valid = Config.validate_config()
        if self.config_valid:
            self.client = AzureOpenAI(
                api_key=Config.AZURE_OPENAI_API_KEY,
                api_version=Config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
            )
            self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT_NAME
        else:
            logger.warning("Azure OpenAI credentials not configured. Running in development mode.")
            self.client = None
            self.deployment_name = None
    
    def generate_text_response(self, user_message, conversation_history=None, user_context=None):
        """Generate text response using Azure OpenAI"""
        if not self.config_valid or not self.client:
            return self._get_dev_response(user_message, 'text')
        
        try:
            messages = self._build_messages(user_message, conversation_history, user_context)
            
            # Optimized parameters for GPT-4.1-nano (speed and performance)
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=800,  # Reduced for faster response
                temperature=0.5,  # Lower for more consistent, faster responses
                top_p=0.8,  # Slightly lower for better performance
                frequency_penalty=0.1,  # Prevent repetition
                presence_penalty=0.1   # Encourage variety
            )
            
            response_text = response.choices[0].message.content
            logger.info("Generated text response")
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating text response: {e}")
            return self._get_error_message('openai_error')
    
    def analyze_image(self, image_content, user_message=None, user_context=None):
        """Analyze image using GPT-4 Vision"""
        if not self.config_valid or not self.client:
            return self._get_dev_response("Image uploaded", "image")
        
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            messages = [
                {
                    "role": "system",
                    "content": SMEPrompts.get_system_prompt(context_type="image_analysis", user_context=user_context)
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message or "Please analyze this image and describe what you see."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # Optimized parameters for GPT-4.1-nano image analysis (speed and performance)
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=600,  # Reduced for faster image analysis
                temperature=0.4,  # Lower for more accurate image descriptions
                top_p=0.8,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            response_text = response.choices[0].message.content
            logger.info("Generated image analysis response")
            return response_text
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return self._get_error_message('invalid_image')
    
    def process_file_content(self, file_content, filename, user_message=None, user_context=None):
        """Process file content and generate response"""
        if not self.config_valid or not self.client:
            return self._get_dev_response(f"File uploaded: {filename}", "file")
        
        try:
            file_prompt = f"""
File name: {filename}
File content:
{file_content}

User request: {user_message or 'Please analyze this file and provide a summary.'}
"""
            
            messages = [
                {
                    "role": "system",
                    "content": SMEPrompts.get_system_prompt(context_type="file_analysis", user_context=user_context)
                },
                {
                    "role": "user",
                    "content": file_prompt
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"Generated file analysis response for: {filename}")
            return response_text
            
        except Exception as e:
            logger.error(f"Error processing file content: {e}")
            return self._get_error_message('processing_error')
    
    def _build_messages(self, user_message, conversation_history=None, user_context=None):
        """Build message history for conversation context"""
        messages = [
            {
                "role": "system",
                "content": SMEPrompts.get_system_prompt(context_type="conversation", user_context=user_context)
            }
        ]
        
        # Add conversation history
        if conversation_history:
            for conv in conversation_history[-Config.MAX_CONVERSATION_HISTORY:]:
                if conv.user_message:
                    messages.append({"role": "user", "content": conv.user_message})
                if conv.bot_response:
                    messages.append({"role": "assistant", "content": conv.bot_response})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    

    
    def _get_error_message(self, error_type):
        """Get error message"""
        error_messages = SMEPrompts.get_error_messages()
        return error_messages.get(error_type, 'An error occurred.')
    
    def _get_dev_response(self, user_message, message_type='text'):
        """Generate development mode response when OpenAI is not configured"""
        dev_responses = SMEPrompts.get_dev_responses()
        
        if message_type == 'text':
            return dev_responses['text'].format(user_message=user_message)
        else:
            return dev_responses.get(message_type, dev_responses['text'].format(user_message=user_message))
