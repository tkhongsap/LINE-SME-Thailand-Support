"""
Smart SME Advisory Intelligence Service
Integrates enhanced Thai cultural context, industry intelligence, and business stage detection
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import re

# Import our enhanced prompt systems
from prompts.thai_sme_enhanced import thai_sme_intelligence
from prompts.industry_contexts import thai_industry_contexts
from prompts.cultural_engine import thai_cultural_engine

logger = logging.getLogger(__name__)

class SMEIntelligenceService:
    """Advanced SME intelligence service with cultural awareness and business context"""
    
    def __init__(self):
        self.thai_sme = thai_sme_intelligence
        self.industry_contexts = thai_industry_contexts
        self.cultural_engine = thai_cultural_engine
        
        # Cache for user context profiles
        self.user_profiles = {}
        self.session_timeout = 3600  # 1 hour
        
        logger.info("SME Intelligence Service initialized with enhanced Thai context")
    
    def analyze_user_message(self, user_message: str, user_id: str, user_context: Dict = None) -> Dict[str, Any]:
        """Comprehensive analysis of user message with cultural and business intelligence"""
        if user_context is None:
            user_context = {}
        
        # Get or create user profile
        user_profile = self.get_user_profile(user_id, user_context)
        
        # Comprehensive message analysis
        analysis = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'message_analysis': {
                'original_message': user_message,
                'message_length': len(user_message),
                'language': self._detect_language(user_message),
                'sentiment': self._analyze_sentiment(user_message),
                'intent': self._detect_intent(user_message),
                'urgency': self._detect_urgency(user_message)
            },
            'business_context': self.thai_sme.detect_business_context(user_message, user_context),
            'cultural_analysis': self.cultural_engine.analyze_cultural_context(user_message, user_context),
            'industry_intelligence': self._get_industry_intelligence(user_message, user_context),
            'personalization': {
                'user_profile': user_profile,
                'conversation_history': self._get_conversation_patterns(user_id),
                'preferences': self._get_user_preferences(user_id)
            },
            'response_strategy': self._determine_response_strategy(user_message, user_context)
        }
        
        # Update user profile with new insights
        self._update_user_profile(user_id, analysis)
        
        return analysis
    
    def generate_enhanced_system_prompt(self, analysis: Dict[str, Any], context_type: str = 'conversation') -> str:
        """Generate enhanced system prompt based on comprehensive analysis"""
        
        business_context = analysis['business_context']
        cultural_analysis = analysis['cultural_analysis']
        industry_intel = analysis['industry_intelligence']
        user_profile = analysis['personalization']['user_profile']
        
        # Generate base enhanced prompt
        base_prompt = self.thai_sme.generate_enhanced_prompt(
            analysis['message_analysis']['original_message'],
            {**business_context, **user_profile},
            context_type
        )
        
        # Add cultural guidelines
        cultural_guidelines = self.cultural_engine.generate_culturally_appropriate_response_guidelines(
            cultural_analysis
        )
        
        # Add industry-specific intelligence
        industry_context = ""
        if industry_intel['industry'] != 'unknown':
            industry_context = self.industry_contexts.get_industry_advice_template(
                industry_intel['industry'],
                business_context.get('stage', 'growth')
            )
        
        # Combine all intelligence
        enhanced_prompt = f"""
{base_prompt}

{cultural_guidelines}

INDUSTRY INTELLIGENCE:
{industry_context}

PERSONALIZATION CONTEXT:
- User Interaction Pattern: {user_profile.get('interaction_pattern', 'New user')}
- Preferred Communication Style: {user_profile.get('preferred_style', 'Polite and helpful')}
- Business Maturity: {user_profile.get('business_maturity', 'Growing')}
- Previous Topics: {', '.join(user_profile.get('topic_history', [])[-3:])}

RESPONSE OPTIMIZATION:
- Sentiment Consideration: {analysis['message_analysis']['sentiment']}
- Intent Focus: {analysis['message_analysis']['intent']}
- Urgency Level: {analysis['message_analysis']['urgency']}
- Cultural Sensitivity: {cultural_analysis['communication_style']['formality_level']}

THAI SME SUCCESS FACTORS:
- Emphasize practical, actionable advice suitable for Thai market
- Reference relevant government resources and support programs
- Consider seasonal business patterns and Thai calendar impacts
- Balance traditional values with modern business practices
- Provide culturally appropriate examples and case studies
- Maintain warm, supportive tone while being professional
"""
        
        return enhanced_prompt
    
    def get_user_profile(self, user_id: str, user_context: Dict = None) -> Dict[str, Any]:
        """Get or create comprehensive user profile"""
        if user_context is None:
            user_context = {}
        
        current_time = datetime.now()
        
        # Check if we have existing profile
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            # Check if profile is still valid
            if (current_time - datetime.fromisoformat(profile['last_updated'])).seconds < self.session_timeout:
                return profile
        
        # Create new profile
        profile = {
            'user_id': user_id,
            'created_at': current_time.isoformat(),
            'last_updated': current_time.isoformat(),
            'interaction_count': 0,
            'preferred_language': user_context.get('language', 'th'),
            'business_type': user_context.get('business_type', 'unknown'),
            'business_stage': user_context.get('stage', 'unknown'),
            'location': user_context.get('location', 'thailand'),
            'industry_focus': user_context.get('industry', 'unknown'),
            'interaction_pattern': 'new_user',
            'preferred_style': 'polite_helpful',
            'business_maturity': 'exploring',
            'topic_history': [],
            'cultural_preferences': {
                'formality_level': 'polite',
                'communication_style': 'warm_professional',
                'hierarchy_awareness': True
            },
            'session_data': {
                'message_count': 0,
                'topics_discussed': [],
                'assistance_areas': []
            }
        }
        
        self.user_profiles[user_id] = profile
        return profile
    
    def _update_user_profile(self, user_id: str, analysis: Dict[str, Any]):
        """Update user profile with new interaction insights"""
        if user_id not in self.user_profiles:
            return
        
        profile = self.user_profiles[user_id]
        
        # Update basic info
        profile['last_updated'] = datetime.now().isoformat()
        profile['interaction_count'] += 1
        profile['session_data']['message_count'] += 1
        
        # Update business context
        business_context = analysis['business_context']
        if business_context['industry'] != 'unknown':
            profile['industry_focus'] = business_context['industry']
        if business_context['stage'] != 'unknown':
            profile['business_stage'] = business_context['stage']
        
        # Update cultural preferences
        cultural_analysis = analysis['cultural_analysis']
        profile['cultural_preferences'] = {
            'formality_level': cultural_analysis['formality_level']['level'],
            'communication_style': cultural_analysis['communication_style']['preferred_style'],
            'hierarchy_awareness': cultural_analysis['hierarchy_awareness']['needs_respect']
        }
        
        # Update topic history
        intent = analysis['message_analysis']['intent']
        if intent not in profile['topic_history']:
            profile['topic_history'].append(intent)
        
        # Limit topic history size
        if len(profile['topic_history']) > 10:
            profile['topic_history'] = profile['topic_history'][-10:]
        
        # Update interaction pattern
        if profile['interaction_count'] > 10:
            profile['interaction_pattern'] = 'regular_user'
        elif profile['interaction_count'] > 5:
            profile['interaction_pattern'] = 'returning_user'
        
        # Update business maturity
        if business_context['stage'] in ['established', 'growth']:
            profile['business_maturity'] = 'experienced'
        elif business_context['stage'] == 'startup':
            profile['business_maturity'] = 'beginner'
        else:
            profile['business_maturity'] = 'developing'
    
    def _detect_language(self, message: str) -> str:
        """Enhanced language detection with Thai business context"""
        # Thai script detection
        if any('\u0e00' <= c <= '\u0e7f' for c in message):
            return 'th'
        
        # English business terms
        english_business_terms = ['business', 'marketing', 'sales', 'customer', 'profit', 'revenue']
        if any(term in message.lower() for term in english_business_terms):
            return 'en'
        
        # Default to Thai for SME context
        return 'th'
    
    def _analyze_sentiment(self, message: str) -> str:
        """Analyze message sentiment for appropriate response tone"""
        positive_indicators = ['ดี', 'เยี่ยม', 'สุดยอด', 'ขอบคุณ', 'great', 'excellent', 'thank']
        negative_indicators = ['ปัญหา', 'ยาก', 'เครียด', 'problem', 'difficult', 'stress', 'help']
        neutral_indicators = ['ปรึกษา', 'แนะนำ', 'advice', 'suggest', 'recommend']
        
        message_lower = message.lower()
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in message_lower)
        negative_count = sum(1 for indicator in negative_indicators if indicator in message_lower)
        
        if positive_count > negative_count and positive_count > 0:
            return 'positive'
        elif negative_count > positive_count and negative_count > 0:
            return 'concerned'
        else:
            return 'neutral'
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent for appropriate response strategy"""
        intent_patterns = {
            'business_advice': ['ปรึกษา', 'แนะนำ', 'advice', 'suggest', 'recommend', 'ช่วย'],
            'financial_help': ['เงิน', 'กำไร', 'ต้นทุน', 'งบ', 'money', 'profit', 'cost', 'budget'],
            'marketing_help': ['การตลาด', 'ขาย', 'ลูกค้า', 'marketing', 'sales', 'customer'],
            'operational_help': ['ดำเนินงาน', 'บริหาร', 'จัดการ', 'operation', 'manage', 'process'],
            'legal_compliance': ['กฎหมาย', 'ระเบียบ', 'ใบอนุญาต', 'legal', 'regulation', 'license'],
            'technology_help': ['เทคโนโลยี', 'ออนไลน์', 'แอพ', 'technology', 'online', 'app', 'digital'],
            'general_inquiry': ['อะไร', 'ยังไง', 'what', 'how', 'where', 'when']
        }
        
        message_lower = message.lower()
        
        for intent, keywords in intent_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return 'general_inquiry'
    
    def _detect_urgency(self, message: str) -> str:
        """Detect urgency level for response prioritization"""
        urgent_keywords = ['ด่วน', 'เร่งด่วน', 'urgent', 'asap', 'รีบ', 'วิกฤต', 'emergency']
        normal_keywords = ['ปรึกษา', 'แนะนำ', 'advice', 'suggest', 'ช่วย', 'help']
        
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in urgent_keywords):
            return 'high'
        elif any(keyword in message_lower for keyword in normal_keywords):
            return 'normal'
        else:
            return 'low'
    
    def _get_industry_intelligence(self, message: str, user_context: Dict) -> Dict[str, Any]:
        """Get comprehensive industry intelligence"""
        industry = self.thai_sme._detect_industry(message, user_context)
        
        if industry != 'unknown':
            return {
                'industry': industry,
                'context': self.industry_contexts.get_industry_context(industry),
                'resources': self.industry_contexts.get_industry_specific_resources(industry),
                'regulations': self.industry_contexts.get_regulatory_checklist(industry),
                'benchmarks': self.industry_contexts.get_financial_benchmarks(industry)
            }
        
        return {'industry': 'unknown', 'context': {}, 'resources': [], 'regulations': [], 'benchmarks': {}}
    
    def _get_conversation_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get user conversation patterns for personalization"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            return {
                'total_interactions': profile['interaction_count'],
                'session_messages': profile['session_data']['message_count'],
                'recent_topics': profile['topic_history'][-5:],
                'interaction_pattern': profile['interaction_pattern']
            }
        
        return {'total_interactions': 0, 'session_messages': 0, 'recent_topics': [], 'interaction_pattern': 'new_user'}
    
    def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences for response customization"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            return {
                'preferred_language': profile['preferred_language'],
                'communication_style': profile['cultural_preferences']['communication_style'],
                'formality_level': profile['cultural_preferences']['formality_level'],
                'business_maturity': profile['business_maturity']
            }
        
        return {
            'preferred_language': 'th',
            'communication_style': 'warm_professional',
            'formality_level': 'polite',
            'business_maturity': 'exploring'
        }
    
    def _determine_response_strategy(self, message: str, user_context: Dict) -> Dict[str, Any]:
        """Determine optimal response strategy"""
        return {
            'approach': 'comprehensive_advisory',
            'tone': 'warm_professional',
            'structure': 'problem_solution_resources',
            'personalization_level': 'high',
            'cultural_adaptation': 'full',
            'industry_focus': True,
            'resource_integration': True,
            'follow_up_suggestions': True
        }
    
    def get_intelligence_metrics(self) -> Dict[str, Any]:
        """Get intelligence service metrics"""
        return {
            'active_users': len(self.user_profiles),
            'total_interactions': sum(profile['interaction_count'] for profile in self.user_profiles.values()),
            'user_patterns': {
                'new_users': len([p for p in self.user_profiles.values() if p['interaction_pattern'] == 'new_user']),
                'returning_users': len([p for p in self.user_profiles.values() if p['interaction_pattern'] == 'returning_user']),
                'regular_users': len([p for p in self.user_profiles.values() if p['interaction_pattern'] == 'regular_user'])
            },
            'business_stages': {
                stage: len([p for p in self.user_profiles.values() if p['business_stage'] == stage])
                for stage in ['startup', 'growth', 'established', 'pivot', 'unknown']
            },
            'industries': {
                industry: len([p for p in self.user_profiles.values() if p['industry_focus'] == industry])
                for industry in ['retail', 'food', 'manufacturing', 'agriculture', 'services', 'technology', 'unknown']
            },
            'cultural_preferences': {
                'formality_levels': {
                    level: len([p for p in self.user_profiles.values() 
                              if p['cultural_preferences']['formality_level'] == level])
                    for level in ['formal', 'polite', 'casual']
                }
            },
            'system_health': {
                'active_sessions': len([p for p in self.user_profiles.values() 
                                      if (datetime.now() - datetime.fromisoformat(p['last_updated'])).seconds < 3600]),
                'cache_size': len(self.user_profiles),
                'memory_usage': 'healthy'
            }
        }
    
    def cleanup_expired_profiles(self):
        """Clean up expired user profiles to manage memory"""
        current_time = datetime.now()
        expired_users = []
        
        for user_id, profile in self.user_profiles.items():
            last_updated = datetime.fromisoformat(profile['last_updated'])
            if (current_time - last_updated).seconds > self.session_timeout * 2:  # 2x timeout for cleanup
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.user_profiles[user_id]
        
        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired user profiles")

# Global instance for easy import
sme_intelligence_service = SMEIntelligenceService()