import os
import json
import hmac
import hashlib
import base64
import logging
import requests
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)

class LineService:
    """Simplified LINE API wrapper for Replit deployment"""
    
    def __init__(self):
        """Initialize LINE Bot API with Replit environment variables"""
        self.channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
        self.channel_secret = os.environ.get('LINE_CHANNEL_SECRET')
        
        if not self.channel_access_token or not self.channel_secret:
            raise ValueError("Missing LINE configuration. Check LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET")
        
        self.reply_url = "https://api.line.me/v2/bot/message/reply"
        self.push_url = "https://api.line.me/v2/bot/message/push"
        
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.channel_access_token}'
        }
        
        logging.info("LINE Bot API client initialized")
    
    def verify_signature(self, body: str, signature: str) -> bool:
        """
        Verify LINE webhook signature
        
        Args:
            body: Request body as string
            signature: X-Line-Signature header value
        
        Returns:
            True if signature is valid
        """
        try:
            if not self.channel_secret:
                logging.error("Channel secret not configured")
                return False
                
            hash_digest = hmac.new(
                self.channel_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            expected_signature = base64.b64encode(hash_digest).decode('utf-8')
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logging.error(f"Signature verification error: {e}")
            return False
    
    def send_message(self, reply_token: str, text: str) -> bool:
        """
        Send reply message to LINE user
        
        Args:
            reply_token: Reply token from webhook event
            text: Message text to send
        
        Returns:
            True if message sent successfully
        """
        try:
            payload = {
                "replyToken": reply_token,
                "messages": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
            
            response = requests.post(
                self.reply_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info(f"Message sent successfully to reply_token: {reply_token[:10]}...")
                return True
            else:
                logging.error(f"LINE API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Send message error: {e}")
            return False
    
    def send_push_message(self, user_id: str, text: str) -> bool:
        """
        Send push message to LINE user (fallback when reply token expires)
        
        Args:
            user_id: LINE user ID
            text: Message text to send
        
        Returns:
            True if message sent successfully
        """
        try:
            payload = {
                "to": user_id,
                "messages": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
            
            response = requests.post(
                self.push_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info(f"Push message sent successfully to user: {user_id[:10]}...")
                return True
            else:
                logging.error(f"LINE Push API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Send push message error: {e}")
            return False

# Global instance for simplified usage
_line_service = None

def get_line_service() -> LineService:
    """Get or create LINE service instance"""
    global _line_service
    if _line_service is None:
        _line_service = LineService()
    return _line_service

def verify_signature(body: str, signature: str) -> bool:
    """Simplified function for signature verification"""
    service = get_line_service()
    return service.verify_signature(body, signature)

def send_message(reply_token: str, text: str) -> bool:
    """Simplified function for sending messages"""
    service = get_line_service()
    return service.send_message(reply_token, text)