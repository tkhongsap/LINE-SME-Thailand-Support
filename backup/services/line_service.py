import logging
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, FileMessage,
    TextSendMessage, ImageSendMessage, FlexSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
from config import Config
from utils.logger import setup_logger, log_user_interaction

logger = setup_logger(__name__)

class LineService:
    def __init__(self):
        self.config_valid = Config.validate_config()
        if self.config_valid:
            self.line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)
            self.handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)
        else:
            logger.warning("LINE API credentials not configured. Running in development mode.")
            self.line_bot_api = None
            self.handler = None
        
    def verify_signature(self, body, signature):
        """Verify LINE webhook signature"""
        if not self.config_valid or not self.handler:
            logger.warning("LINE handler not configured, skipping signature verification")
            return True  # Allow in development mode
        try:
            self.handler.handle(body, signature)
            return True
        except InvalidSignatureError:
            logger.error("Invalid signature for LINE webhook")
            return False
    
    def send_text_message(self, reply_token, message, quick_replies=None):
        """Send text message with optional quick replies"""
        if not self.config_valid or not self.line_bot_api:
            logger.info(f"Development mode - would send message: {message[:100]}...")
            return
        
        try:
            quick_reply = None
            if quick_replies:
                quick_reply_buttons = [
                    QuickReplyButton(action=MessageAction(label=label, text=text))
                    for label, text in quick_replies
                ]
                quick_reply = QuickReply(items=quick_reply_buttons)
            
            text_message = TextSendMessage(text=message, quick_reply=quick_reply)
            self.line_bot_api.reply_message(reply_token, text_message)
            logger.info(f"Sent text message: {message[:100]}...")
            
        except LineBotApiError as e:
            logger.error(f"Failed to send text message: {e}")
            raise
    
    def send_image_message(self, reply_token, original_content_url, preview_image_url):
        """Send image message"""
        try:
            image_message = ImageSendMessage(
                original_content_url=original_content_url,
                preview_image_url=preview_image_url
            )
            self.line_bot_api.reply_message(reply_token, image_message)
            logger.info("Sent image message")
            
        except LineBotApiError as e:
            logger.error(f"Failed to send image message: {e}")
            raise
    
    def send_flex_message(self, reply_token, alt_text, flex_content):
        """Send flex message"""
        try:
            flex_message = FlexSendMessage(alt_text=alt_text, contents=flex_content)
            self.line_bot_api.reply_message(reply_token, flex_message)
            logger.info("Sent flex message")
            
        except LineBotApiError as e:
            logger.error(f"Failed to send flex message: {e}")
            raise
    
    def get_message_content(self, message_id):
        """Get message content for files and images"""
        if not self.config_valid or not self.line_bot_api:
            logger.info(f"Development mode - cannot get message content for: {message_id}")
            return b"Mock file content for development mode"
        
        try:
            message_content = self.line_bot_api.get_message_content(message_id)
            return message_content.content
        except LineBotApiError as e:
            logger.error(f"Failed to get message content: {e}")
            raise
    
    def get_user_profile(self, user_id):
        """Get user profile information"""
        try:
            profile = self.line_bot_api.get_profile(user_id)
            return {
                'user_id': profile.user_id,
                'display_name': profile.display_name,
                'picture_url': profile.picture_url,
                'status_message': profile.status_message
            }
        except LineBotApiError as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    def create_language_selection_flex(self):
        """Create a flex message for language selection"""
        return {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "Choose Your Language / 言語を選択",
                        "weight": "bold",
                        "size": "lg",
                        "align": "center"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "English",
                            "text": "/lang en"
                        },
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "日本語",
                            "text": "/lang ja"
                        },
                        "style": "secondary",
                        "margin": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "한국어",
                            "text": "/lang ko"
                        },
                        "style": "secondary",
                        "margin": "sm"
                    }
                ]
            }
        }
    
    def create_help_message(self, language='en'):
        """Create help message based on language"""
        help_messages = {
            'en': """🤖 LINE AI Assistant Help

I can help you with:
📝 Text conversations - Ask me anything!
🖼️ Image analysis - Send me images to analyze
📄 File processing - Upload documents, spreadsheets, presentations, or code files

Commands:
/help - Show this help message
/lang - Change language
/clear - Clear conversation history

Supported file types:
• Documents: PDF, DOCX, TXT, MD
• Spreadsheets: XLSX, XLS, CSV  
• Presentations: PPTX, PPT
• Code files: PY, JS, HTML, CSS, etc.
• Images: JPG, PNG, GIF, etc.

Just send me a message, image, or file and I'll help you!""",
            
            'ja': """🤖 LINE AIアシスタント ヘルプ

お手伝いできること:
📝 テキスト会話 - 何でも聞いてください！
🖼️ 画像解析 - 画像を送信して分析
📄 ファイル処理 - 文書、スプレッドシート、プレゼンテーション、コードファイルをアップロード

コマンド:
/help - このヘルプメッセージを表示
/lang - 言語を変更
/clear - 会話履歴をクリア

対応ファイル形式:
• 文書: PDF, DOCX, TXT, MD
• スプレッドシート: XLSX, XLS, CSV
• プレゼンテーション: PPTX, PPT
• コードファイル: PY, JS, HTML, CSS など
• 画像: JPG, PNG, GIF など

メッセージ、画像、ファイルを送信するだけでお手伝いします！""",
            
            'ko': """🤖 LINE AI 어시스턴트 도움말

도움을 드릴 수 있는 것들:
📝 텍스트 대화 - 무엇이든 물어보세요!
🖼️ 이미지 분석 - 이미지를 보내서 분석
📄 파일 처리 - 문서, 스프레드시트, 프레젠테이션, 코드 파일 업로드

명령어:
/help - 이 도움말 메시지 표시
/lang - 언어 변경
/clear - 대화 기록 지우기

지원 파일 형식:
• 문서: PDF, DOCX, TXT, MD
• 스프레드시트: XLSX, XLS, CSV
• 프레젠테이션: PPTX, PPT
• 코드 파일: PY, JS, HTML, CSS 등
• 이미지: JPG, PNG, GIF 등

메시지, 이미지, 파일을 보내주시면 도와드리겠습니다!"""
        }
        
        return help_messages.get(language, help_messages['en'])
