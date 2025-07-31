import logging
import time
import hashlib
from typing import List, Dict, Optional, Union, Tuple
from collections import deque
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, FileMessage,
    TextSendMessage, ImageSendMessage, FlexSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    CarouselContainer, BubbleContainer, BoxComponent,
    TextComponent, ButtonComponent, MessageAction as MA,
    PostbackAction, URIAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds
)

from config import Config
from utils.logger import setup_logger, log_user_interaction

logger = setup_logger(__name__)


class OptimizedLineService:
    """Optimized LINE Bot service with connection pooling, batching, and caching"""
    
    def __init__(self):
        self.config_valid = Config.validate_config()
        self._signature_cache = {}  # Simple in-memory cache
        self._flex_template_cache = {}
        self._reply_token_tracker = {}
        
        if self.config_valid:
            # Initialize LINE SDK with custom session for connection pooling
            self.session = self._create_pooled_session()
            self.line_bot_api = LineBotApi(
                Config.LINE_CHANNEL_ACCESS_TOKEN,
                http_client=self.session
            )
            self.handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)
        else:
            logger.warning("LINE API credentials not configured. Running in development mode.")
            self.line_bot_api = None
            self.handler = None
            self.session = None
    
    def _create_pooled_session(self) -> requests.Session:
        """Create a session with connection pooling and retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=Config.CONNECTION_MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        # Configure connection pooling
        adapter = HTTPAdapter(
            pool_connections=Config.CONNECTION_POOL_SIZE,
            pool_maxsize=Config.CONNECTION_POOL_SIZE,
            max_retries=retry_strategy
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set timeout
        session.timeout = Config.CONNECTION_TIMEOUT
        
        return session
    
    def verify_signature(self, body: str, signature: str) -> bool:
        """Optimized signature verification with caching"""
        if not self.config_valid or not self.handler:
            logger.warning("LINE handler not configured, skipping signature verification")
            return True
        
        # Create cache key
        cache_key = hashlib.sha256(f"{body[:100]}{signature}".encode()).hexdigest()
        
        # Check cache
        cached_result = self._signature_cache.get(cache_key)
        if cached_result is not None:
            cache_time, result = cached_result
            if time.time() - cache_time < Config.SIGNATURE_CACHE_TTL:
                logger.debug("Using cached signature verification result")
                return result
        
        # Verify signature
        try:
            self.handler.handle(body, signature)
            result = True
        except InvalidSignatureError:
            logger.error("Invalid signature for LINE webhook")
            result = False
        
        # Cache result
        self._signature_cache[cache_key] = (time.time(), result)
        
        # Clean old cache entries
        self._clean_signature_cache()
        
        return result
    
    def _clean_signature_cache(self):
        """Remove expired entries from signature cache"""
        current_time = time.time()
        expired_keys = [
            key for key, (cache_time, _) in self._signature_cache.items()
            if current_time - cache_time > Config.SIGNATURE_CACHE_TTL
        ]
        for key in expired_keys:
            del self._signature_cache[key]
    
    def track_reply_token(self, reply_token: str):
        """Track reply token with expiration time"""
        self._reply_token_tracker[reply_token] = time.time() + Config.REPLY_TOKEN_EXPIRY
    
    def is_reply_token_valid(self, reply_token: str) -> bool:
        """Check if reply token is still valid"""
        expiry_time = self._reply_token_tracker.get(reply_token)
        if expiry_time is None:
            return True  # Assume valid if not tracked
        return time.time() < expiry_time
    
    def send_messages(self, reply_token: str, messages: List[Union[TextSendMessage, ImageSendMessage, FlexSendMessage]]):
        """Send multiple messages with batching support"""
        if not self.config_valid or not self.line_bot_api:
            logger.info(f"Development mode - would send {len(messages)} messages")
            return
        
        # Check reply token validity
        if not self.is_reply_token_valid(reply_token):
            logger.warning("Reply token may have expired, consider using push message")
            # Could implement fallback to push message here
        
        try:
            # LINE API supports up to 5 messages per reply
            for i in range(0, len(messages), Config.MAX_MESSAGES_PER_REPLY):
                batch = messages[i:i + Config.MAX_MESSAGES_PER_REPLY]
                self.line_bot_api.reply_message(reply_token, batch)
                logger.info(f"Sent batch of {len(batch)} messages")
                
        except LineBotApiError as e:
            logger.error(f"Failed to send messages: {e}")
            raise
    
    def send_text_message(self, reply_token: str, message: str, quick_replies: Optional[List[Tuple[str, str]]] = None):
        """Send text message with optional quick replies"""
        quick_reply = None
        if quick_replies:
            quick_reply_buttons = [
                QuickReplyButton(action=MessageAction(label=label, text=text))
                for label, text in quick_replies
            ]
            quick_reply = QuickReply(items=quick_reply_buttons)
        
        text_message = TextSendMessage(text=message, quick_reply=quick_reply)
        self.send_messages(reply_token, [text_message])
    
    def send_text_messages_batch(self, reply_token: str, messages: List[str]):
        """Send multiple text messages in a batch"""
        text_messages = [TextSendMessage(text=msg) for msg in messages]
        self.send_messages(reply_token, text_messages)
    
    def push_message(self, user_id: str, messages: List[Union[TextSendMessage, ImageSendMessage, FlexSendMessage]]):
        """Send push messages (doesn't require reply token)"""
        if not self.config_valid or not self.line_bot_api:
            logger.info(f"Development mode - would push {len(messages)} messages to {user_id}")
            return
        
        try:
            # Push API also supports up to 5 messages
            for i in range(0, len(messages), Config.MAX_MESSAGES_PER_REPLY):
                batch = messages[i:i + Config.MAX_MESSAGES_PER_REPLY]
                self.line_bot_api.push_message(user_id, batch)
                logger.info(f"Pushed batch of {len(batch)} messages to {user_id}")
                
        except LineBotApiError as e:
            logger.error(f"Failed to push messages: {e}")
            raise
    
    def multicast_messages(self, user_ids: List[str], messages: List[Union[TextSendMessage, ImageSendMessage, FlexSendMessage]]):
        """Send messages to multiple users (up to 500)"""
        if not self.config_valid or not self.line_bot_api:
            logger.info(f"Development mode - would multicast to {len(user_ids)} users")
            return
        
        try:
            # Multicast API supports up to 500 users
            for i in range(0, len(user_ids), 500):
                batch_users = user_ids[i:i + 500]
                self.line_bot_api.multicast(batch_users, messages)
                logger.info(f"Multicast to {len(batch_users)} users")
                
        except LineBotApiError as e:
            logger.error(f"Failed to multicast messages: {e}")
            raise
    
    def create_carousel_flex(self, items: List[Dict], title: str = "เลือกรายการ") -> FlexSendMessage:
        """Create optimized carousel flex message for Thai SME scenarios"""
        bubbles = []
        
        for item in items[:10]:  # LINE limits carousels to 10 bubbles
            bubble = BubbleContainer(
                body=BoxComponent(
                    layout="vertical",
                    contents=[
                        TextComponent(
                            text=item.get('title', 'ไม่มีชื่อ'),
                            weight="bold",
                            size="lg",
                            wrap=True
                        ),
                        TextComponent(
                            text=item.get('description', ''),
                            size="sm",
                            wrap=True,
                            color="#999999",
                            margin="sm"
                        )
                    ]
                ),
                footer=BoxComponent(
                    layout="vertical",
                    contents=[
                        ButtonComponent(
                            action=MessageAction(
                                label=item.get('action_label', 'เลือก'),
                                text=item.get('action_text', item.get('title', ''))
                            ),
                            style="primary"
                        )
                    ]
                )
            )
            bubbles.append(bubble)
        
        carousel = CarouselContainer(contents=bubbles)
        return FlexSendMessage(alt_text=title, contents=carousel)
    
    def create_quick_reply_from_context(self, context: str, language: str = 'th') -> QuickReply:
        """Create context-aware quick replies for Thai SME scenarios"""
        quick_replies_map = {
            'th': {
                'greeting': [
                    ('ขอคำปรึกษาธุรกิจ', 'ขอคำปรึกษาธุรกิจ'),
                    ('ดูตัวอย่างเอกสาร', 'ดูตัวอย่างเอกสาร'),
                    ('วิเคราะห์ไฟล์', 'อัพโหลดไฟล์เพื่อวิเคราะห์'),
                    ('เปลี่ยนภาษา', '/lang')
                ],
                'business': [
                    ('แผนธุรกิจ', 'ช่วยเขียนแผนธุรกิจ'),
                    ('การตลาด', 'แนะนำกลยุทธ์การตลาด'),
                    ('การเงิน', 'คำนวณต้นทุนและกำไร'),
                    ('กฎหมาย', 'กฎหมายที่เกี่ยวข้อง')
                ],
                'document': [
                    ('สร้างใบเสนอราคา', 'สร้างใบเสนอราคา'),
                    ('สร้างใบกำกับภาษี', 'สร้างใบกำกับภาษี'),
                    ('สัญญาธุรกิจ', 'ตัวอย่างสัญญาธุรกิจ'),
                    ('รายงานการเงิน', 'วิเคราะห์รายงานการเงิน')
                ]
            },
            'en': {
                'greeting': [
                    ('Business Advice', 'I need business advice'),
                    ('Document Templates', 'Show document templates'),
                    ('File Analysis', 'Upload file for analysis'),
                    ('Change Language', '/lang')
                ],
                'business': [
                    ('Business Plan', 'Help with business plan'),
                    ('Marketing', 'Marketing strategies'),
                    ('Finance', 'Calculate costs and profit'),
                    ('Legal', 'Legal requirements')
                ]
            }
        }
        
        # Get appropriate quick replies based on context and language
        lang_replies = quick_replies_map.get(language, quick_replies_map['en'])
        context_replies = lang_replies.get(context, lang_replies['greeting'])
        
        quick_reply_buttons = [
            QuickReplyButton(action=MessageAction(label=label, text=text))
            for label, text in context_replies
        ]
        
        return QuickReply(items=quick_reply_buttons)
    
    def create_rich_menu(self, language: str = 'th') -> Optional[str]:
        """Create and upload rich menu for Thai SME users"""
        if not self.config_valid or not self.line_bot_api:
            logger.info("Development mode - would create rich menu")
            return None
        
        try:
            # Define rich menu structure
            rich_menu = RichMenu(
                size=RichMenuSize(width=2500, height=1686),
                selected=True,
                name=f"Thai SME Menu ({language})",
                chat_bar_text="เมนู" if language == 'th' else "Menu",
                areas=[
                    # Row 1
                    RichMenuArea(
                        bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
                        action=MessageAction(
                            label="คำปรึกษา" if language == 'th' else "Consult",
                            text="ขอคำปรึกษาธุรกิจ" if language == 'th' else "Business consultation"
                        )
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=833, y=0, width=834, height=843),
                        action=MessageAction(
                            label="เอกสาร" if language == 'th' else "Documents",
                            text="ดูตัวอย่างเอกสารธุรกิจ" if language == 'th' else "View document templates"
                        )
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=1667, y=0, width=833, height=843),
                        action=CameraAction(label="ถ่ายรูป" if language == 'th' else "Camera")
                    ),
                    # Row 2
                    RichMenuArea(
                        bounds=RichMenuBounds(x=0, y=843, width=833, height=843),
                        action=CameraRollAction(label="อัพโหลด" if language == 'th' else "Upload")
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=833, y=843, width=834, height=843),
                        action=MessageAction(
                            label="ภาษา" if language == 'th' else "Language",
                            text="/lang"
                        )
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=1667, y=843, width=833, height=843),
                        action=MessageAction(
                            label="ช่วยเหลือ" if language == 'th' else "Help",
                            text="/help"
                        )
                    )
                ]
            )
            
            # Create rich menu
            rich_menu_id = self.line_bot_api.create_rich_menu(rich_menu)
            
            # Upload rich menu image (would need actual image)
            # self.line_bot_api.set_rich_menu_image(rich_menu_id, content_type, image_data)
            
            # Set as default
            self.line_bot_api.set_default_rich_menu(rich_menu_id)
            
            logger.info(f"Created rich menu: {rich_menu_id}")
            return rich_menu_id
            
        except LineBotApiError as e:
            logger.error(f"Failed to create rich menu: {e}")
            return None
    
    def get_cached_flex_template(self, template_name: str) -> Optional[Dict]:
        """Get cached flex message template"""
        cached = self._flex_template_cache.get(template_name)
        if cached and time.time() - cached['timestamp'] < Config.FLEX_MESSAGE_CACHE_TTL:
            return cached['template']
        return None
    
    def cache_flex_template(self, template_name: str, template: Dict):
        """Cache flex message template"""
        self._flex_template_cache[template_name] = {
            'template': template,
            'timestamp': time.time()
        }
    
    # Maintain backward compatibility
    def send_image_message(self, reply_token: str, original_content_url: str, preview_image_url: str):
        """Send image message"""
        image_message = ImageSendMessage(
            original_content_url=original_content_url,
            preview_image_url=preview_image_url
        )
        self.send_messages(reply_token, [image_message])
    
    def send_flex_message(self, reply_token: str, alt_text: str, flex_content: Dict):
        """Send flex message with caching support"""
        # Check if this is a known template
        template_key = hashlib.md5(str(flex_content).encode()).hexdigest()[:8]
        
        flex_message = FlexSendMessage(alt_text=alt_text, contents=flex_content)
        self.send_messages(reply_token, [flex_message])
    
    def get_message_content(self, message_id: str) -> bytes:
        """Get message content with connection pooling"""
        if not self.config_valid or not self.line_bot_api:
            logger.info(f"Development mode - cannot get message content for: {message_id}")
            return b"Mock file content for development mode"
        
        try:
            message_content = self.line_bot_api.get_message_content(message_id)
            return message_content.content
        except LineBotApiError as e:
            logger.error(f"Failed to get message content: {e}")
            raise
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile with error handling"""
        if not self.config_valid or not self.line_bot_api:
            return {'user_id': user_id, 'display_name': 'Dev User', 'picture_url': None, 'status_message': None}
        
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
    
    def create_language_selection_flex(self) -> Dict:
        """Create optimized language selection flex message"""
        # Check cache first
        cached = self.get_cached_flex_template('language_selection')
        if cached:
            return cached
        
        template = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "เลือกภาษา / Choose Language",
                        "weight": "bold",
                        "size": "xl",
                        "align": "center",
                        "color": "#1DB446"
                    }
                ],
                "backgroundColor": "#F0F0F0"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "🇹🇭 ภาษาไทย",
                            "text": "/lang th"
                        },
                        "style": "primary",
                        "color": "#1DB446"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "🇬🇧 English",
                            "text": "/lang en"
                        },
                        "style": "secondary"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "🇯🇵 日本語",
                            "text": "/lang ja"
                        },
                        "style": "secondary"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "🇰🇷 한국어",
                            "text": "/lang ko"
                        },
                        "style": "secondary"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "🇨🇳 中文",
                            "text": "/lang zh"
                        },
                        "style": "secondary"
                    }
                ]
            }
        }
        
        # Cache the template
        self.cache_flex_template('language_selection', template)
        
        return template
    
    def create_help_message(self, language: str = 'th') -> str:
        """Create help message based on language"""
        help_messages = {
            'th': """🤖 ผู้ช่วย SME ไทย

ฉันช่วยคุณได้ในเรื่อง:
📊 คำปรึกษาธุรกิจ - วางแผน การตลาด การเงิน
📄 วิเคราะห์เอกสาร - PDF, Word, Excel, PowerPoint
🖼️ วิเคราะห์รูปภาพ - สินค้า ป้าย เอกสาร
💼 เอกสารธุรกิจ - ใบเสนอราคา ใบกำกับภาษี สัญญา

คำสั่งพิเศษ:
/help - แสดงข้อความช่วยเหลือ
/lang - เปลี่ยนภาษา
/clear - ล้างประวัติการสนทนา

💡 เคล็ดลับ: ส่งไฟล์หรือรูปภาพมาได้เลย ฉันจะวิเคราะห์ให้ทันที!

ไฟล์ที่รองรับ:
• เอกสาร: PDF, DOCX, TXT, MD
• ตาราง: XLSX, XLS, CSV  
• นำเสนอ: PPTX, PPT
• โค้ด: PY, JS, HTML, CSS ฯลฯ
• รูปภาพ: JPG, PNG, GIF ฯลฯ

🏢 พัฒนาโดยทีม Thai SME Support
📞 ติดต่อ: support@thaismebot.com""",
            
            'en': """🤖 Thai SME Assistant

I can help you with:
📊 Business consulting - Planning, Marketing, Finance
📄 Document analysis - PDF, Word, Excel, PowerPoint
🖼️ Image analysis - Products, Signs, Documents
💼 Business documents - Quotations, Invoices, Contracts

Commands:
/help - Show this help message
/lang - Change language
/clear - Clear conversation history

💡 Tip: Just send me files or images, I'll analyze them immediately!

Supported files:
• Documents: PDF, DOCX, TXT, MD
• Spreadsheets: XLSX, XLS, CSV  
• Presentations: PPTX, PPT
• Code files: PY, JS, HTML, CSS, etc.
• Images: JPG, PNG, GIF, etc.

🏢 Developed by Thai SME Support Team
📞 Contact: support@thaismebot.com""",
            
            'ja': """🤖 タイSMEアシスタント

お手伝いできること:
📊 ビジネスコンサルティング - 計画、マーケティング、財務
📄 文書分析 - PDF、Word、Excel、PowerPoint
🖼️ 画像分析 - 製品、看板、文書
💼 ビジネス文書 - 見積書、請求書、契約書

コマンド:
/help - このヘルプメッセージを表示
/lang - 言語を変更
/clear - 会話履歴をクリア

💡 ヒント: ファイルや画像を送信するだけで、すぐに分析します！

対応ファイル:
• 文書: PDF, DOCX, TXT, MD
• スプレッドシート: XLSX, XLS, CSV
• プレゼンテーション: PPTX, PPT
• コードファイル: PY, JS, HTML, CSS など
• 画像: JPG, PNG, GIF など

🏢 Thai SME Supportチーム開発
📞 お問い合わせ: support@thaismebot.com"""
        }
        
        return help_messages.get(language, help_messages['en'])
    
    def close(self):
        """Close the session and clean up resources"""
        if self.session:
            self.session.close()