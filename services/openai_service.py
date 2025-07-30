import logging
import base64
from openai import AzureOpenAI
from config import Config
from utils.logger import setup_logger

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
    
    def generate_text_response(self, user_message, conversation_history=None, language='en'):
        """Generate text response using Azure OpenAI"""
        if not self.config_valid or not self.client:
            return self._get_dev_response(user_message, language)
        
        try:
            messages = self._build_messages(user_message, conversation_history, language)
            
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
    
    def analyze_image(self, image_content, user_message=None, language='en'):
        """Analyze image using GPT-4 Vision"""
        if not self.config_valid or not self.client:
            return self._get_dev_response("Image uploaded", language, "image")
        
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt(language, "image_analysis")
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
    
    def process_file_content(self, file_content, filename, user_message=None, language='en'):
        """Process file content and generate response"""
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
                    "content": self._get_system_prompt(language, "file_analysis")
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
    
    def _build_messages(self, user_message, conversation_history=None, language='en'):
        """Build message history for conversation context"""
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(language, "conversation")
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
    
    def _get_system_prompt(self, language, context_type):
        """Get system prompt based on language and context"""
        prompts = {
            'en': {
                'conversation': "You are a helpful AI assistant integrated with LINE messaging. Respond naturally and helpfully to user questions. Keep responses concise but informative. If you need clarification, ask follow-up questions.",
                'image_analysis': "You are an AI assistant that analyzes images. Describe what you see in detail, including objects, people, text, colors, and any relevant context. Be thorough but concise.",
                'file_analysis': "You are an AI assistant that analyzes files. Provide a comprehensive summary of the file content, key points, and answer any specific questions about the file. Format your response clearly."
            },
            'ja': {
                'conversation': "あなたはLINEメッセージングと統合された有用なAIアシスタントです。ユーザーの質問に自然で役立つ回答をしてください。回答は簡潔でありながら情報豊富にしてください。明確化が必要な場合は、フォローアップの質問をしてください。",
                'image_analysis': "あなたは画像を分析するAIアシスタントです。オブジェクト、人物、テキスト、色、関連するコンテキストを含めて、見えるものを詳細に説明してください。徹底的でありながら簡潔にしてください。",
                'file_analysis': "あなたはファイルを分析するAIアシスタントです。ファイル内容の包括的な要約、キーポイント、ファイルに関する具体的な質問への回答を提供してください。回答を明確にフォーマットしてください。"
            },
            'ko': {
                'conversation': "당신은 LINE 메시징과 통합된 유용한 AI 어시스턴트입니다. 사용자 질문에 자연스럽고 도움이 되는 답변을 제공하세요. 답변은 간결하면서도 정보가 풍부해야 합니다. 명확화가 필요한 경우 후속 질문을 하세요.",
                'image_analysis': "당신은 이미지를 분석하는 AI 어시스턴트입니다. 객체, 사람, 텍스트, 색상 및 관련 맥락을 포함하여 보이는 것을 자세히 설명하세요. 철저하면서도 간결하게 설명하세요.",
                'file_analysis': "당신은 파일을 분석하는 AI 어시스턴트입니다. 파일 내용의 포괄적인 요약, 핵심 포인트, 파일에 대한 구체적인 질문에 대한 답변을 제공하세요. 답변을 명확하게 포맷하세요."
            }
        }
        
        return prompts.get(language, prompts['en']).get(context_type, prompts['en']['conversation'])
    
    def _get_error_message(self, language, error_type):
        """Get error message in specified language"""
        return Config.ERROR_MESSAGES.get(language, Config.ERROR_MESSAGES['en']).get(error_type, 'An error occurred.')
    
    def _get_dev_response(self, user_message, language='en', message_type='text'):
        """Generate development mode response when OpenAI is not configured"""
        responses = {
            'en': {
                'text': f"This is a development mode response to: '{user_message}'. To enable AI responses, please configure your Azure OpenAI credentials.",
                'image': "I received your image, but I'm running in development mode. Configure Azure OpenAI credentials to enable image analysis.",
                'file': f"I received your file, but I'm running in development mode. Configure Azure OpenAI credentials to enable file processing."
            },
            'ja': {
                'text': f"これは開発モードの応答です: '{user_message}'。AI応答を有効にするには、Azure OpenAI認証情報を設定してください。",
                'image': "画像を受信しましたが、開発モードで実行中です。画像解析を有効にするには、Azure OpenAI認証情報を設定してください。",
                'file': "ファイルを受信しましたが、開発モードで実行中です。ファイル処理を有効にするには、Azure OpenAI認証情報を設定してください。"
            }
        }
        
        lang_responses = responses.get(language, responses['en'])
        return lang_responses.get(message_type, lang_responses['text'])
