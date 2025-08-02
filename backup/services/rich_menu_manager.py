import logging
from typing import Dict, Optional, List
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import requests

from linebot.models import (
    RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds,
    MessageAction, PostbackAction, URIAction,
    CameraAction, CameraRollAction, LocationAction
)
from linebot.exceptions import LineBotApiError

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RichMenuManager:
    """Manager for creating and managing LINE Rich Menus"""
    
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.active_menus = {}  # user_id -> rich_menu_id
        
        # Menu templates for different contexts
        self.menu_templates = {
            'default': lambda: self.create_thai_sme_menu(),
            'business': lambda: self.create_business_context_menu(),
            'document': lambda: self.create_thai_sme_menu(),
            'help': lambda: self.create_thai_sme_menu()
        }
    
    def create_thai_sme_menu(self, language: str = 'th') -> Optional[str]:
        """Create the main Thai SME rich menu"""
        try:
            # Menu text based on language
            texts = self._get_menu_texts(language)
            
            rich_menu = RichMenu(
                size=RichMenuSize(width=2500, height=1686),
                selected=True,
                name=f"Thai SME Menu ({language})",
                chat_bar_text=texts['chat_bar'],
                areas=[
                    # Top row - Business functions
                    RichMenuArea(
                        bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
                        action=MessageAction(
                            label=texts['consult']['label'],
                            text=texts['consult']['text']
                        )
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=833, y=0, width=834, height=843),
                        action=MessageAction(
                            label=texts['documents']['label'],
                            text=texts['documents']['text']
                        )
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=1667, y=0, width=833, height=843),
                        action=MessageAction(
                            label=texts['analysis']['label'],
                            text=texts['analysis']['text']
                        )
                    ),
                    
                    # Bottom row - Utility functions
                    RichMenuArea(
                        bounds=RichMenuBounds(x=0, y=843, width=833, height=843),
                        action=CameraRollAction(label=texts['upload']['label'])
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=833, y=843, width=834, height=843),
                        action=MessageAction(
                            label=texts['language']['label'],
                            text="/lang"
                        )
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=1667, y=843, width=833, height=843),
                        action=MessageAction(
                            label=texts['help']['label'],
                            text="/help"
                        )
                    )
                ]
            )
            
            # Create the menu
            rich_menu_id = self.line_bot_api.create_rich_menu(rich_menu)
            
            # Generate and upload menu image
            menu_image = self._generate_menu_image(texts, language)
            if menu_image:
                self.line_bot_api.set_rich_menu_image(
                    rich_menu_id, 
                    'image/png', 
                    menu_image
                )
            
            logger.info(f"Created Thai SME rich menu: {rich_menu_id}")
            return rich_menu_id
            
        except LineBotApiError as e:
            logger.error(f"Failed to create rich menu: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating rich menu: {e}")
            return None
    
    def create_business_context_menu(self, language: str = 'th') -> Optional[str]:
        """Create a business-focused rich menu"""
        try:
            texts = self._get_business_menu_texts(language)
            
            rich_menu = RichMenu(
                size=RichMenuSize(width=2500, height=1686),
                selected=False,
                name=f"Business Context Menu ({language})",
                chat_bar_text=texts['chat_bar'],
                areas=[
                    # Business planning
                    RichMenuArea(
                        bounds=RichMenuBounds(x=0, y=0, width=1250, height=843),
                        action=MessageAction(
                            label=texts['business_plan']['label'],
                            text=texts['business_plan']['text']
                        )
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=1250, y=0, width=1250, height=843),
                        action=MessageAction(
                            label=texts['marketing']['label'],
                            text=texts['marketing']['text']
                        )
                    ),
                    
                    # Financial and legal
                    RichMenuArea(
                        bounds=RichMenuBounds(x=0, y=843, width=833, height=843),
                        action=MessageAction(
                            label=texts['finance']['label'],
                            text=texts['finance']['text']
                        )
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=833, y=843, width=834, height=843),
                        action=MessageAction(
                            label=texts['legal']['label'],
                            text=texts['legal']['text']
                        )
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=1667, y=843, width=833, height=843),
                        action=MessageAction(
                            label=texts['back']['label'],
                            text="/menu default"
                        )
                    )
                ]
            )
            
            rich_menu_id = self.line_bot_api.create_rich_menu(rich_menu)
            
            # Generate business menu image
            menu_image = self._generate_business_menu_image(texts, language)
            if menu_image:
                self.line_bot_api.set_rich_menu_image(
                    rich_menu_id,
                    'image/png',
                    menu_image
                )
            
            logger.info(f"Created business context menu: {rich_menu_id}")
            return rich_menu_id
            
        except LineBotApiError as e:
            logger.error(f"Failed to create business menu: {e}")
            return None
    
    def set_user_menu(self, user_id: str, menu_type: str = 'default', language: str = 'th') -> bool:
        """Set rich menu for a specific user"""
        try:
            # Get or create the appropriate menu
            if menu_type == 'default':
                menu_id = self.create_thai_sme_menu(language)
            elif menu_type == 'business':
                menu_id = self.create_business_context_menu(language)
            else:
                logger.warning(f"Unknown menu type: {menu_type}")
                return False
            
            if not menu_id:
                return False
            
            # Link menu to user
            self.line_bot_api.link_rich_menu_to_user(user_id, menu_id)
            self.active_menus[user_id] = menu_id
            
            logger.info(f"Set {menu_type} menu for user {user_id}")
            return True
            
        except LineBotApiError as e:
            logger.error(f"Failed to set user menu: {e}")
            return False
    
    def set_default_menu(self, menu_type: str = 'default', language: str = 'th') -> bool:
        """Set default rich menu for all new users"""
        try:
            if menu_type == 'default':
                menu_id = self.create_thai_sme_menu(language)
            else:
                logger.warning(f"Cannot set {menu_type} as default menu")
                return False
            
            if not menu_id:
                return False
            
            self.line_bot_api.set_default_rich_menu(menu_id)
            logger.info(f"Set default menu: {menu_id}")
            return True
            
        except LineBotApiError as e:
            logger.error(f"Failed to set default menu: {e}")
            return False
    
    def get_user_menu(self, user_id: str) -> Optional[str]:
        """Get the current rich menu for a user"""
        try:
            menu_id = self.line_bot_api.get_rich_menu_id_of_user(user_id)
            return menu_id
        except LineBotApiError:
            return None
    
    def list_rich_menus(self) -> List[Dict]:
        """List all rich menus"""
        try:
            menus = self.line_bot_api.get_rich_menu_list()
            return [
                {
                    'id': menu.rich_menu_id,
                    'name': menu.name,
                    'selected': menu.selected,
                    'areas': len(menu.areas)
                }
                for menu in menus
            ]
        except LineBotApiError as e:
            logger.error(f"Failed to list rich menus: {e}")
            return []
    
    def delete_rich_menu(self, menu_id: str) -> bool:
        """Delete a rich menu"""
        try:
            self.line_bot_api.delete_rich_menu(menu_id)
            logger.info(f"Deleted rich menu: {menu_id}")
            return True
        except LineBotApiError as e:
            logger.error(f"Failed to delete rich menu: {e}")
            return False
    
    def _get_menu_texts(self, language: str) -> Dict:
        """Get menu texts for different languages"""
        texts = {
            'th': {
                'chat_bar': 'เมนู SME',
                'consult': {'label': 'คำปรึกษา', 'text': 'ขอคำปรึกษาธุรกิจ SME'},
                'documents': {'label': 'เอกสาร', 'text': 'เอกสารธุรกิจและแบบฟอร์ม'},
                'analysis': {'label': 'วิเคราะห์', 'text': 'วิเคราะห์ข้อมูลธุรกิจ'},
                'upload': {'label': 'อัพโหลด'},
                'language': {'label': 'ภาษา'},
                'help': {'label': 'ช่วยเหลือ'}
            },
            'en': {
                'chat_bar': 'SME Menu',
                'consult': {'label': 'Consult', 'text': 'SME Business Consultation'},
                'documents': {'label': 'Documents', 'text': 'Business documents and forms'},
                'analysis': {'label': 'Analysis', 'text': 'Analyze business data'},
                'upload': {'label': 'Upload'},
                'language': {'label': 'Language'},
                'help': {'label': 'Help'}
            }
        }
        return texts.get(language, texts['en'])
    
    def _get_business_menu_texts(self, language: str) -> Dict:
        """Get business menu specific texts"""
        texts = {
            'th': {
                'chat_bar': 'เมนูธุรกิจ',
                'business_plan': {'label': 'แผนธุรกิจ', 'text': 'ช่วยเขียนแผนธุรกิจ SME'},
                'marketing': {'label': 'การตลาด', 'text': 'กลยุทธ์การตลาดสำหรับ SME'},
                'finance': {'label': 'การเงิน', 'text': 'คำนวณต้นทุนและวางแผนการเงิน'},
                'legal': {'label': 'กฎหมาย', 'text': 'กฎหมายและระเบียบสำหรับ SME'},
                'back': {'label': 'กลับ'}
            },
            'en': {
                'chat_bar': 'Business',
                'business_plan': {'label': 'Business Plan', 'text': 'Help with SME business plan'},
                'marketing': {'label': 'Marketing', 'text': 'Marketing strategies for SME'},
                'finance': {'label': 'Finance', 'text': 'Calculate costs and financial planning'},
                'legal': {'label': 'Legal', 'text': 'Legal requirements for SME'},
                'back': {'label': 'Back'}
            }
        }
        return texts.get(language, texts['en'])
    
    def _generate_menu_image(self, texts: Dict, language: str) -> Optional[bytes]:
        """Generate menu image using PIL"""
        try:
            # Create image
            width, height = 2500, 1686
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Colors for Thai SME theme
            primary_color = '#1DB446'  # LINE green
            secondary_color = '#E8F5E8'
            text_color = '#333333'
            
            # Try to load a font (fallback to default if not available)
            try:
                font_large = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf', 60)
                font_medium = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf', 40)
            except:
                try:
                    font_large = ImageFont.truetype('arial.ttf', 60)
                    font_medium = ImageFont.truetype('arial.ttf', 40)
                except:
                    font_large = ImageFont.load_default()
                    font_medium = ImageFont.load_default()
            
            # Draw grid
            col_width = width // 3
            row_height = height // 2
            
            # Top row
            areas = [
                (texts['consult']['label'], 0, 0),
                (texts['documents']['label'], col_width, 0),
                (texts['analysis']['label'], col_width * 2, 0),
                (texts['upload']['label'], 0, row_height),
                (texts['language']['label'], col_width, row_height),
                (texts['help']['label'], col_width * 2, row_height)
            ]
            
            for i, (text, x, y) in enumerate(areas):
                # Alternate colors
                bg_color = primary_color if i < 3 else secondary_color
                txt_color = 'white' if i < 3 else text_color
                
                # Draw background
                draw.rectangle([x, y, x + col_width, y + row_height], fill=bg_color, outline='white', width=3)
                
                # Draw text (centered)
                bbox = draw.textbbox((0, 0), text, font=font_medium)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = x + (col_width - text_width) // 2
                text_y = y + (row_height - text_height) // 2
                
                draw.text((text_x, text_y), text, fill=txt_color, font=font_medium)
                
                # Add icons (simple shapes for demonstration)
                icon_size = 80
                icon_x = text_x - icon_size - 20
                icon_y = text_y - icon_size // 2
                
                if i == 0:  # Consult - circle
                    draw.ellipse([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], 
                               fill=txt_color, outline=txt_color)
                elif i == 1:  # Documents - rectangle
                    draw.rectangle([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], 
                                 fill=txt_color, outline=txt_color)
                elif i == 2:  # Analysis - triangle
                    draw.polygon([(icon_x + icon_size//2, icon_y), 
                                (icon_x, icon_y + icon_size), 
                                (icon_x + icon_size, icon_y + icon_size)], 
                               fill=txt_color, outline=txt_color)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG', optimize=True)
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate menu image: {e}")
            return None
    
    def _generate_business_menu_image(self, texts: Dict, language: str) -> Optional[bytes]:
        """Generate business-specific menu image"""
        try:
            # Similar to main menu but with business theme
            width, height = 2500, 1686
            img = Image.new('RGB', (width, height), color='#F8F9FA')
            draw = ImageDraw.Draw(img)
            
            # Business color scheme
            primary_color = '#0066CC'
            secondary_color = '#E6F2FF'
            text_color = '#333333'
            
            # Simple layout for business menu
            areas = [
                (texts['business_plan']['label'], 0, 0, width//2, height//2),
                (texts['marketing']['label'], width//2, 0, width//2, height//2),
                (texts['finance']['label'], 0, height//2, width//3, height//2),
                (texts['legal']['label'], width//3, height//2, width//3, height//2),
                (texts['back']['label'], width*2//3, height//2, width//3, height//2)
            ]
            
            for i, (text, x, y, w, h) in enumerate(areas):
                bg_color = primary_color if i < 2 else secondary_color
                txt_color = 'white' if i < 2 else text_color
                
                draw.rectangle([x, y, x + w, y + h], fill=bg_color, outline='white', width=3)
                
                # Centered text
                try:
                    font = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf', 50)
                except:
                    font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = x + (w - text_width) // 2
                text_y = y + (h - text_height) // 2
                
                draw.text((text_x, text_y), text, fill=txt_color, font=font)
            
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG', optimize=True)
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate business menu image: {e}")
            return None