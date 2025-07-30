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
    
    def generate_text_response(self, user_message, conversation_history=None, language=None, user_context=None):
        """Generate text response using Azure OpenAI"""
        # Auto-detect language if not provided
        if language is None:
            language = SMEPrompts.detect_language_from_message(user_message)
        
        if not self.config_valid or not self.client:
            return self._get_dev_response(user_message, language)
        
        try:
            messages = self._build_messages(user_message, conversation_history, language, user_context)
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                top_p=0.9
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"Generated text response for language: {language}")
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating text response: {e}")
            return self._get_error_message(language, 'openai_error')
    
    def analyze_image(self, image_content, user_message=None, language=None, user_context=None):
        """Analyze image using GPT-4 Vision"""
        # Auto-detect language if not provided and user_message exists
        if language is None and user_message:
            language = SMEPrompts.detect_language_from_message(user_message)
        elif language is None:
            language = 'th'  # Default to Thai for SME support
        
        if not self.config_valid or not self.client:
            return self._get_dev_response("Image uploaded", language, "image")
        
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            messages = [
                {
                    "role": "system",
                    "content": SMEPrompts.get_system_prompt(language, "image_analysis", user_context)
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
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            logger.info("Generated image analysis response")
            return response_text
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return self._get_error_message(language, 'invalid_image')
    
    def process_file_content(self, file_content, filename, user_message=None, language=None, user_context=None):
        """Process file content and generate response"""
        # Auto-detect language if not provided and user_message exists
        if language is None and user_message:
            language = SMEPrompts.detect_language_from_message(user_message)
        elif language is None:
            language = 'th'  # Default to Thai for SME support
        
        if not self.config_valid or not self.client:
            return self._get_dev_response(f"File uploaded: {filename}", language, "file")
        
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
                    "content": SMEPrompts.get_system_prompt(language, "file_analysis", user_context)
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
            return self._get_error_message(language, 'processing_error')
    
    def _build_messages(self, user_message, conversation_history=None, language='th', user_context=None):
        """Build message history for conversation context"""
        messages = [
            {
                "role": "system",
                "content": SMEPrompts.get_system_prompt(language, "conversation", user_context)
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
    

    
    def _get_error_message(self, language, error_type):
        """Get error message in specified language"""
        error_messages = SMEPrompts.get_error_messages()
        return error_messages.get(language, error_messages['en']).get(error_type, 'An error occurred.')
    
    def _get_dev_response(self, user_message, language='th', message_type='text'):
        """Generate development mode response when OpenAI is not configured"""
        dev_responses = SMEPrompts.get_dev_responses()
        lang_responses = dev_responses.get(language, dev_responses['th'])
        
        if message_type == 'text':
            return lang_responses['text'].format(user_message=user_message)
        else:
            return lang_responses.get(message_type, lang_responses['text'].format(user_message=user_message))
