"""
Message Complexity Detection Utility
Determines whether a message should use fast path or full pipeline processing
"""

import re
import logging
from typing import Dict, List, Tuple
from config import Config

logger = logging.getLogger(__name__)

class ComplexityDetector:
    """
    Analyzes message complexity to route between fast path and full pipeline
    """
    
    def __init__(self):
        self.fast_path_keywords = [word.lower() for word in Config.FAST_PATH_KEYWORDS]
        self.complex_indicators = [
            # Thai complex indicators
            'วิเคราะห์', 'ประเมิน', 'แผนธุรกิจ', 'กลยุทธ์', 'การตลาด', 
            'การเงิน', 'บัญชี', 'ภาษี', 'กฎหมาย', 'สัญญา', 'ใบเสนอราคา',
            'รายงาน', 'สรุป', 'เปรียบเทียบ', 'คำนวณ', 'วางแผน',
            
            # English complex indicators  
            'analyze', 'analysis', 'evaluate', 'assessment', 'business plan',
            'strategy', 'marketing', 'financial', 'accounting', 'tax', 'legal',
            'contract', 'proposal', 'report', 'summary', 'compare', 'calculate',
            'planning', 'consultation', 'recommendation'
        ]
        
        self.command_patterns = [
            r'^/\w+',  # Commands starting with /
        ]
        
    def is_simple_query(self, message: str, message_type: str = 'text') -> Tuple[bool, Dict]:
        """
        Determine if a message is simple enough for fast path processing
        
        Returns:
            (is_simple: bool, analysis: Dict)
        """
        
        # Non-text messages always go to full pipeline
        if message_type != 'text':
            return False, {
                'reason': 'non_text_message',
                'message_type': message_type,
                'decision': 'full_pipeline'
            }
        
        message_lower = message.strip().lower()
        analysis = {
            'original_length': len(message),
            'word_count': len(message.split()),
            'line_count': len(message.strip().split('\n')),
            'has_fast_keywords': False,
            'has_complex_indicators': False,
            'is_command': False,
            'decision': 'unknown'
        }
        
        # Check basic length constraints
        if len(message) > Config.FAST_PATH_MAX_LENGTH:
            analysis['decision'] = 'full_pipeline'
            analysis['reason'] = f'message_too_long ({len(message)} > {Config.FAST_PATH_MAX_LENGTH})'
            return False, analysis
        
        # Check word count threshold
        if analysis['word_count'] > Config.COMPLEXITY_THRESHOLD_WORDS:
            analysis['decision'] = 'full_pipeline'
            analysis['reason'] = f'too_many_words ({analysis["word_count"]} > {Config.COMPLEXITY_THRESHOLD_WORDS})'
            return False, analysis
        
        # Check line count (multi-line messages are often complex)
        if analysis['line_count'] > Config.COMPLEXITY_THRESHOLD_LINES:
            analysis['decision'] = 'full_pipeline'
            analysis['reason'] = f'multi_line_message ({analysis["line_count"]} lines)'
            return False, analysis
        
        # Check for commands
        for pattern in self.command_patterns:
            if re.match(pattern, message_lower):
                analysis['is_command'] = True
                analysis['decision'] = 'fast_path'
                analysis['reason'] = 'command'
                return True, analysis
        
        # Check for fast path keywords
        analysis['has_fast_keywords'] = any(
            keyword in message_lower for keyword in self.fast_path_keywords
        )
        
        # Check for complex indicators
        analysis['has_complex_indicators'] = any(
            indicator in message_lower for indicator in self.complex_indicators
        )
        
        # Decision logic
        if analysis['has_complex_indicators']:
            analysis['decision'] = 'full_pipeline'
            analysis['reason'] = 'complex_business_query'
            return False, analysis
        
        if analysis['has_fast_keywords']:
            analysis['decision'] = 'fast_path'
            analysis['reason'] = 'simple_greeting_or_query'
            return True, analysis
        
        # More aggressive fast path routing for better performance
        # Expand criteria for very short messages
        if (analysis['word_count'] <= 8 and  # Increased from 5
            analysis['line_count'] == 1 and 
            len(message) <= 80):  # Increased from 50
            analysis['decision'] = 'fast_path'
            analysis['reason'] = 'short_simple_message'
            return True, analysis
        
        # Route medium-length simple messages to fast path  
        if (analysis['word_count'] <= 15 and  # New criteria
            analysis['line_count'] <= 2 and 
            len(message) <= 120 and
            not any(complex_word in message_lower for complex_word in 
                   ['detailed', 'comprehensive', 'analysis', 'strategy', 'วิเคราะห์', 'ยุทธศาสตร์'])):
            analysis['decision'] = 'fast_path'
            analysis['reason'] = 'medium_simple_message'
            return True, analysis
        
        # Default to full pipeline only for clearly complex queries
        analysis['decision'] = 'full_pipeline'
        analysis['reason'] = 'potentially_complex'
        return False, analysis
    
    def analyze_user_context(self, user_id: str, message_history: List = None) -> Dict:
        """
        Analyze user context to influence complexity detection
        This is a lightweight version for fast path decisions
        """
        context = {
            'user_id': user_id,
            'has_recent_complex_queries': False,
            'message_count': len(message_history) if message_history else 0,
            'context_influence': 'none'
        }
        
        # If user has recent complex queries, lean towards full pipeline
        if message_history and len(message_history) > 0:
            recent_messages = message_history[-3:]  # Last 3 messages
            for msg in recent_messages:
                if any(indicator in msg.get('user_message', '').lower() 
                       for indicator in self.complex_indicators[:10]):  # Check top 10 complex indicators
                    context['has_recent_complex_queries'] = True
                    context['context_influence'] = 'lean_full_pipeline'
                    break
        
        return context
    
    def get_routing_decision(self, message: str, user_id: str, message_type: str = 'text', 
                           message_history: List = None) -> Dict:
        """
        Get comprehensive routing decision with context
        """
        # Basic complexity analysis
        is_simple, analysis = self.is_simple_query(message, message_type)
        
        # User context analysis (lightweight)
        user_context = self.analyze_user_context(user_id, message_history)
        
        # Final decision with context influence
        final_decision = analysis['decision']
        
        # Context-based adjustments
        if (is_simple and 
            analysis['reason'] not in ['command', 'very_short_simple_message'] and
            user_context['context_influence'] == 'lean_full_pipeline'):
            final_decision = 'full_pipeline'
            analysis['reason'] = f"{analysis['reason']}_but_complex_context"
        
        result = {
            'route_to_fast_path': final_decision == 'fast_path',
            'decision': final_decision,
            'confidence': self._calculate_confidence(analysis, user_context),
            'analysis': analysis,
            'user_context': user_context,
            'processing_recommendation': {
                'fast_path': final_decision == 'fast_path',
                'skip_sme_intelligence': Config.FAST_PATH_SKIP_SME_INTELLIGENCE if final_decision == 'fast_path' else False,
                'skip_ai_optimizer': Config.FAST_PATH_SKIP_AI_OPTIMIZER if final_decision == 'fast_path' else False,
                'skip_conversation_history': Config.FAST_PATH_SKIP_CONVERSATION_HISTORY if final_decision == 'fast_path' else False
            }
        }
        
        logger.debug(f"Complexity decision for '{message[:30]}...': {final_decision} (confidence: {result['confidence']:.2f})")
        
        return result
    
    def _calculate_confidence(self, analysis: Dict, user_context: Dict) -> float:
        """Calculate confidence score for the routing decision"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for clear indicators
        if analysis.get('is_command'):
            confidence += 0.4
        elif analysis.get('has_complex_indicators'):
            confidence += 0.3
        elif analysis.get('has_fast_keywords'):
            confidence += 0.2
        
        # Adjust for message characteristics
        if analysis.get('reason') == 'very_short_simple_message':
            confidence += 0.3
        elif analysis.get('reason') == 'message_too_long':
            confidence += 0.4
        
        # Context adjustments
        if user_context.get('context_influence') == 'lean_full_pipeline':
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))

# Global instance
complexity_detector = ComplexityDetector()