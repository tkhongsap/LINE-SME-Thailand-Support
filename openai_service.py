import os
import logging
import time
import threading
from datetime import datetime, timedelta
from openai import AzureOpenAI
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global session storage for conversation memory
conversation_sessions = {}
session_lock = threading.Lock()


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

    def generate_response(
            self,
            user_message: str,
            conversation_history: Optional[List[Dict[str,
                                                     Any]]] = None) -> str:
        """
        Generate response using Azure OpenAI with language detection, Alex Hormozi persona, and conversation memory
        
        Args:
            user_message: User's input message
            conversation_history: Optional conversation context for memory
        
        Returns:
            Generated response text
        """
        # Universal fallback message for any errors
        fallback_message = "ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง / Sorry, an error occurred. Please try again."

        try:
            # Enhanced system prompt with language detection and Alex Hormozi persona
            system_prompt = self._build_enhanced_system_prompt(
                user_message, conversation_history)

            # Build message history for conversation context
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history if available (sliding window approach)
            if conversation_history:
                formatted_history = self._format_conversation_history(
                    conversation_history)
                messages.extend(formatted_history)

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            # Make direct API call with extended timeout
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                timeout=30.0)

            result = response.choices[0].message.content
            if result:
                logging.info(
                    f"OpenAI response generated successfully (length: {len(result)}, history_items: {len(conversation_history) if conversation_history else 0})"
                )
                return result
            else:
                logging.warning("Empty response from OpenAI API")
                return fallback_message

        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return fallback_message

    def _build_enhanced_system_prompt(
            self,
            user_message: str,
            conversation_history: Optional[List[Dict[str,
                                                     Any]]] = None) -> str:

        base_prompt = f"""
        LANGUAGE OVERRIDE: The user message "{user_message}" - YOU MUST respond in the exact same language as this message. 
        If ANY English words: respond ONLY in English. If ANY Thai characters: respond ONLY in Thai.
        This language rule overrides everything else.

        You are a practical advisor for small business owners in Thailand.

        **Persona**: Anthony Bourdain-inspired — direct but human, honest, empathetic. Not here to sell hype, just help.

        **Expertise**: Finance (cashflow, loans), Digital Marketing (LINE OA, social media), E-Commerce (marketplaces, payments), Operations (staff, compliance, pricing).

        **Approach**: 
        • Understand their problem first
        • Give practical steps with timelines when useful
        • Never make things sound easier than they are
        • Always end with a next step or question
        • Ask about their business when needed

        **Boundaries**: Not a lawyer or tax officer — suggest professionals for legal/tax matters.

        """

        # Add conversation context if available
        if conversation_history and len(conversation_history) > 0:
            base_prompt += f"\n\nCONVERSATION CONTEXT: You have been discussing business topics with this user. Keep the conversation coherent and build upon previous exchanges."

        return base_prompt

    def _format_conversation_history(
            self,
            conversation_history: List[Dict[str,
                                            Any]]) -> List[Dict[str, Any]]:
        """Format conversation history for OpenAI API (sliding window approach)"""
        if not conversation_history:
            return []

        # Implement sliding window - keep last 50 exchanges (100 messages) to stay within token limits
        max_history_items = 100
        recent_history = conversation_history[-max_history_items:] if len(
            conversation_history) > max_history_items else conversation_history

        formatted_messages = []
        for item in recent_history:
            if item.get('role') and item.get('content'):
                formatted_messages.append({
                    "role": str(item['role']),
                    "content": str(item['content'])
                })

        return formatted_messages

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


# Session Management Functions
def get_conversation_history(user_id: str) -> List[Dict[str, Any]]:
    """Get conversation history for a user"""
    with session_lock:
        if user_id in conversation_sessions:
            session = conversation_sessions[user_id]
            # Check if session is still valid (not expired)
            if datetime.now() - session['last_activity'] < timedelta(hours=1):
                return session['history']
            else:
                # Session expired, remove it
                del conversation_sessions[user_id]
                logging.info(f"Session expired for user {user_id[:10]}...")
    return []


def update_conversation_history(user_id: str, user_message: str,
                                assistant_response: str):
    """Update conversation history with new exchange"""
    with session_lock:
        if user_id not in conversation_sessions:
            conversation_sessions[user_id] = {
                'history': [],
                'created_at': datetime.now(),
                'last_activity': datetime.now()
            }

        session = conversation_sessions[user_id]

        # Add user message and assistant response
        session['history'].extend([{
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        }, {
            'role': 'assistant',
            'content': assistant_response,
            'timestamp': datetime.now().isoformat()
        }])

        # Update last activity
        session['last_activity'] = datetime.now()

        # Implement sliding window to prevent memory overflow
        max_history_length = 20  # Keep last 10 exchanges (20 messages)
        if len(session['history']) > max_history_length:
            session['history'] = session['history'][-max_history_length:]
            logging.info(
                f"Conversation history pruned for user {user_id[:10]}...")

        logging.info(
            f"Updated conversation history for user {user_id[:10]}... (history length: {len(session['history'])})"
        )


def cleanup_expired_sessions():
    """Clean up expired sessions to manage memory"""
    current_time = datetime.now()
    expired_sessions = []

    with session_lock:
        for user_id, session in conversation_sessions.items():
            if current_time - session['last_activity'] > timedelta(hours=1):
                expired_sessions.append(user_id)

        for user_id in expired_sessions:
            del conversation_sessions[user_id]

    if expired_sessions:
        logging.info(f"Cleaned up {len(expired_sessions)} expired sessions")


def get_session_stats() -> Dict[str, Any]:
    """Get statistics about current sessions for monitoring"""
    with session_lock:
        total_sessions = len(conversation_sessions)
        total_messages = sum(
            len(session['history'])
            for session in conversation_sessions.values())

        return {
            'active_sessions': total_sessions,
            'total_messages': total_messages,
            'memory_estimate_mb':
            (total_messages * 200) / (1024 * 1024)  # Rough estimate
        }


def clear_user_session(user_id: str) -> bool:
    """Clear conversation history for a specific user"""
    with session_lock:
        if user_id in conversation_sessions:
            del conversation_sessions[user_id]
            logging.info(f"Cleared session for user {user_id[:10]}...")
            return True
    return False


def generate_response(
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Simplified function for direct usage with universal language support and conversation memory"""
    service = get_openai_service()
    return service.generate_response(user_message, conversation_history)
