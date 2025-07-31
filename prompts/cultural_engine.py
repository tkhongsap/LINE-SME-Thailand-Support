"""
Thai Cultural Context Engine
Advanced cultural intelligence for authentic Thai business communication
"""

import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
import calendar

class ThaiCulturalEngine:
    """Advanced Thai cultural context detection and response adaptation engine"""
    
    # Thai Language Patterns and Cultural Markers
    LANGUAGE_PATTERNS = {
        'formal_markers': {
            'prefixes': ['เรียน', 'ท่าน', 'คุณ', 'พระ'],
            'formal_terms': ['การ', 'เพื่อ', 'ด้วย', 'จึง', 'ซึ่ง', 'อัน', 'แห่ง'],
            'royal_language': ['เสด็จ', 'ทรง', 'พระราชดำริ', 'โปรดเกล้า'],
            'bureaucratic': ['กระทรวง', 'กรม', 'สำนักงาน', 'หน่วยงาน', 'ราชการ']
        },
        'polite_particles': {
            'male': ['ครับ', 'นะครับ', 'เจ้าครับ'],
            'female': ['ค่ะ', 'นะคะ', 'เจ้าค่ะ'],
            'neutral': ['นะ', 'จ้ะ', 'หน่อย', 'หน่อยนะ'],
            'respectful_requests': ['ขอ', 'กรุณา', 'โปรด', 'ช่วย']
        },
        'informal_markers': {
            'casual_terms': ['เดี๋ยว', 'แป๊บ', 'เอาจริง', 'โอเค', 'ใส่ใจ'],
            'slang': ['เท่ห์', 'เจ๋ง', 'แจ่ม', 'แสบ', 'เฟี้ยว'],
            'generational': {
                'gen_z': ['ปัง', 'เทพ', 'สุดยอด', 'แซ่บ', 'ฟิน'],
                'millennial': ['คูล', 'ชิล', 'โหด', 'แกร่ง', 'เจ๋ง'],
                'gen_x': ['เยี่ยม', 'ดีมาก', 'เลิศ', 'ยอด']
            }
        },
        'business_terminology': {
            'traditional': ['ธุรกิจ', 'การค้า', 'พาณิชย์', 'การขาย', 'ลูกค้า'],
            'modern': ['บิซนิส', 'เทรด', 'มาร์เก็ตติ้ง', 'เซลส์', 'คัสตอมเมอร์'],
            'financial': ['กำไร', 'ต้นทุน', 'รายได้', 'ค่าใช้จ่าย', 'งบประมาณ'],
            'digital': ['ออนไลน์', 'เว็บไซต์', 'แอพ', 'โซเชียล', 'ดิจิทัล']
        }
    }
    
    # Cultural Values and Business Etiquette
    CULTURAL_VALUES = {
        'core_values': {
            'kreng_jai': {
                'thai_term': 'เกรงใจ',
                'meaning': 'Consideration for others, avoiding inconvenience',
                'business_application': 'Gentle approach, indirect communication, respect for time',
                'indicators': ['ไม่เป็นไร', 'ไม่รบกวน', 'ถ้าสะดวก', 'ขออนุญาต']
            },
            'sanook': {
                'thai_term': 'สนุก',
                'meaning': 'Fun, enjoyment, making work pleasant',
                'business_application': 'Team building, positive workplace culture, enjoyable processes',
                'indicators': ['สนุกสนาน', 'เพลิดเพลิน', 'มีความสุข', 'รื่นเริง']
            },
            'hai_kiad': {
                'thai_term': 'ให้เกียรติ',
                'meaning': 'Giving respect and honor',
                'business_application': 'Showing respect to seniors, formal recognition, proper protocol',
                'indicators': ['เกียรติ', 'ยกย่อง', 'เคารพ', 'ให้ความสำคัญ']
            },
            'nam_jai': {
                'thai_term': 'น้ำใจ',
                'meaning': 'Kindness, generosity of spirit',
                'business_application': 'Going beyond requirements, helping others, community support',
                'indicators': ['น้ำใจ', 'เมตตา', 'ใจดี', 'ช่วยเหลือ']
            }
        },
        'hierarchy_respect': {
            'age_hierarchy': ['พี่', 'น้อง', 'รุ่นพี่', 'รุ่นน้อง', 'อาวุโส'],
            'professional_hierarchy': ['เจ้านาย', 'ผู้บริหาร', 'หัวหน้า', 'ผู้จัดการ', 'ผู้อำนวยการ'],
            'social_hierarchy': ['ครู', 'อาจารย์', 'ผู้ใหญ่', 'คุณพ่อ', 'คุณแม่']
        },
        'face_saving': {
            'positive_terms': ['เก่ง', 'เชี่ยวชาญ', 'มีประสบการณ์', 'น่าเชื่อถือ'],
            'diplomatic_language': ['อาจจะ', 'บางที', 'น่าจะ', 'คิดว่า', 'เห็นด้วย'],
            'avoid_direct_criticism': True,
            'constructive_feedback': ['แนะนำ', 'เสนอแนะ', 'พิจารณา', 'ปรับปรุง']
        }
    }
    
    # Regional Cultural Variations
    REGIONAL_CULTURES = {
        'bangkok': {
            'communication_style': 'Direct but polite, business-focused, time-conscious',
            'business_pace': 'Fast-paced, efficiency-oriented',
            'relationship_building': 'Professional networks, formal meetings, structured approach',
            'cultural_markers': ['เมืองหลวง', 'กรุงเทพ', 'ในเมือง', 'ผู้บริหาร'],
            'preferred_formality': 'formal_polite'
        },
        'central': {
            'communication_style': 'Warm and relationship-focused, patient approach',
            'business_pace': 'Moderate pace, relationship before business',
            'relationship_building': 'Community connections, family references, gradual trust',
            'cultural_markers': ['ชุมชน', 'หมู่บ้าน', 'ใกล้ใจ', 'พื้นที่'],
            'preferred_formality': 'polite_friendly'
        },
        'northern': {
            'communication_style': 'Traditional, respectful, community-oriented',
            'business_pace': 'Deliberate, consensus-building, thoughtful decisions',
            'relationship_building': 'Extended family networks, traditional values, elder respect',
            'cultural_markers': ['ภาคเหนือ', 'ล้านนา', 'ประเพณี', 'วัฒนธรรม'],
            'preferred_formality': 'respectful_traditional'
        },
        'northeastern': {
            'communication_style': 'Direct but warm, community solidarity, mutual support',
            'business_pace': 'Steady, community-focused, collective decisions',
            'relationship_building': 'Strong community bonds, mutual assistance, shared experiences',
            'cultural_markers': ['อีสาน', 'หมู่บ้าน', 'ร่วมมือ', 'ช่วยเหลือ'],
            'preferred_formality': 'warm_community'
        },
        'southern': {
            'communication_style': 'Expressive, maritime culture influence, trade-oriented',
            'business_pace': 'Dynamic, trade-focused, adaptive',
            'relationship_building': 'Trading networks, multi-cultural awareness, port connections',
            'cultural_markers': ['ภาคใต้', 'ทะเล', 'การค้า', 'ท่าเรือ'],
            'preferred_formality': 'friendly_trade'
        }
    }
    
    # Buddhist Business Values
    BUDDHIST_VALUES = {
        'right_livelihood': {
            'principles': ['honest trade', 'fair pricing', 'ethical products', 'no harm to others'],
            'business_applications': ['transparent pricing', 'quality products', 'fair labor', 'environmental care'],
            'keywords': ['ซื่อสัตย์', 'ยุติธรรม', 'เมตตา', 'ไม่เบียดเบียน']
        },
        'merit_making': {
            'business_context': ['CSR activities', 'community support', 'temple donations', 'helping others'],
            'opportunities': ['social impact', 'community projects', 'education support', 'healthcare'],
            'keywords': ['ทำบุญ', 'ช่วยสังคม', 'ให้ทาน', 'สร้างบุญ']
        },
        'karma_in_business': {
            'long_term_thinking': ['sustainable practices', 'relationship investment', 'reputation building'],
            'ethical_considerations': ['fair treatment', 'honest communication', 'promise keeping'],
            'keywords': ['กรรม', 'ผลบุญ', 'ระยะยาว', 'ความดี']
        }
    }
    
    # Thai Calendar and Business Cycles
    THAI_CALENDAR = {
        'important_periods': {
            'new_year': {
                'dates': ['January 1', 'Songkran (April 13-15)'],
                'business_impact': 'Major holidays, family time, travel peak',
                'marketing_opportunities': ['new year promotions', 'family products', 'travel services']
            },
            'buddhist_holidays': {
                'dates': ['Visakha Bucha', 'Makha Bucha', 'Khao Phansa', 'Ok Phansa'],
                'business_impact': 'Religious observance, merit-making activities',
                'marketing_opportunities': ['spiritual products', 'merit-making services', 'temple supplies']
            },
            'royal_occasions': {
                'dates': ['King\'s Birthday', 'Queen\'s Birthday', 'Royal ceremonies'],
                'business_impact': 'National pride, formal atmosphere, government activities',
                'marketing_opportunities': ['patriotic themes', 'royal project products', 'formal services']
            },
            'agricultural_seasons': {
                'planting_season': 'May-July',
                'harvest_season': 'November-February',
                'business_impact': 'Rural income cycles, seasonal demand patterns'
            }
        },
        'business_patterns': {
            'peak_seasons': ['November-February (cool season)', 'March-May (summer)'],
            'slow_seasons': ['June-October (rainy season)'],
            'planning_cycles': ['Annual budgets in October', 'Quarterly reviews', 'Songkran break planning']
        }
    }
    
    @classmethod
    def analyze_cultural_context(cls, message: str, user_context: Dict = None) -> Dict[str, Any]:
        """Comprehensive cultural context analysis"""
        if user_context is None:
            user_context = {}
            
        analysis = {
            'formality_level': cls._detect_formality_level(message),
            'cultural_values': cls._detect_cultural_values(message),
            'regional_context': cls._detect_regional_markers(message),
            'generational_indicators': cls._detect_generational_markers(message),
            'business_context': cls._detect_business_context_markers(message),
            'religious_sensitivity': cls._detect_religious_markers(message),
            'hierarchy_awareness': cls._detect_hierarchy_markers(message),
            'communication_style': cls._recommend_communication_style(message, user_context)
        }
        
        return analysis
    
    @classmethod
    def _detect_formality_level(cls, message: str) -> Dict[str, Any]:
        """Detect appropriate formality level from message content"""
        formal_score = 0
        polite_score = 0
        casual_score = 0
        
        # Count formal markers
        for category in cls.LANGUAGE_PATTERNS['formal_markers'].values():
            formal_score += sum(1 for marker in category if marker in message)
        
        # Count polite particles
        for particles in cls.LANGUAGE_PATTERNS['polite_particles'].values():
            polite_score += sum(1 for particle in particles if particle in message)
        
        # Count informal markers
        for category in cls.LANGUAGE_PATTERNS['informal_markers'].values():
            if isinstance(category, list):
                casual_score += sum(1 for marker in category if marker in message)
            elif isinstance(category, dict):
                for markers in category.values():
                    casual_score += sum(1 for marker in markers if marker in message)
        
        # Determine formality level
        if formal_score > 0 or polite_score > 2:
            level = 'formal'
        elif polite_score > 0:
            level = 'polite'
        elif casual_score > 0:
            level = 'casual'
        else:
            level = 'neutral'
        
        return {
            'level': level,
            'formal_score': formal_score,
            'polite_score': polite_score,
            'casual_score': casual_score,
            'recommended_particles': cls._get_appropriate_particles(level)
        }
    
    @classmethod
    def _detect_cultural_values(cls, message: str) -> List[str]:
        """Detect cultural values references in message"""
        detected_values = []
        
        for value_name, value_data in cls.CULTURAL_VALUES['core_values'].items():
            if any(indicator in message for indicator in value_data['indicators']):
                detected_values.append(value_name)
        
        return detected_values
    
    @classmethod
    def _detect_regional_markers(cls, message: str) -> str:
        """Detect regional cultural markers"""
        for region, data in cls.REGIONAL_CULTURES.items():
            if any(marker in message for marker in data['cultural_markers']):
                return region
        
        return 'central'  # Default
    
    @classmethod
    def _detect_generational_markers(cls, message: str) -> str:
        """Detect generational language patterns"""
        for generation, markers in cls.LANGUAGE_PATTERNS['informal_markers']['generational'].items():
            if any(marker in message for marker in markers):
                return generation
        
        return 'millennial'  # Default
    
    @classmethod
    def _detect_business_context_markers(cls, message: str) -> Dict[str, bool]:
        """Detect business context indicators"""
        return {
            'traditional_business': any(term in message for term in cls.LANGUAGE_PATTERNS['business_terminology']['traditional']),
            'modern_business': any(term in message for term in cls.LANGUAGE_PATTERNS['business_terminology']['modern']),
            'financial_focus': any(term in message for term in cls.LANGUAGE_PATTERNS['business_terminology']['financial']),
            'digital_focus': any(term in message for term in cls.LANGUAGE_PATTERNS['business_terminology']['digital'])
        }
    
    @classmethod
    def _detect_religious_markers(cls, message: str) -> Dict[str, bool]:
        """Detect religious/spiritual context markers"""
        return {
            'merit_making': any(keyword in message for keyword in cls.BUDDHIST_VALUES['merit_making']['keywords']),
            'ethical_concern': any(keyword in message for keyword in cls.BUDDHIST_VALUES['right_livelihood']['keywords']),
            'long_term_thinking': any(keyword in message for keyword in cls.BUDDHIST_VALUES['karma_in_business']['keywords'])
        }
    
    @classmethod
    def _detect_hierarchy_markers(cls, message: str) -> Dict[str, bool]:
        """Detect hierarchy awareness indicators"""
        return {
            'age_hierarchy': any(term in message for term in cls.CULTURAL_VALUES['hierarchy_respect']['age_hierarchy']),
            'professional_hierarchy': any(term in message for term in cls.CULTURAL_VALUES['hierarchy_respect']['professional_hierarchy']),
            'needs_respect': any(term in message for term in cls.CULTURAL_VALUES['hierarchy_respect']['social_hierarchy'])
        }
    
    @classmethod
    def _recommend_communication_style(cls, message: str, user_context: Dict) -> Dict[str, Any]:
        """Recommend appropriate communication style"""
        formality = cls._detect_formality_level(message)
        region = cls._detect_regional_markers(message)
        
        regional_data = cls.REGIONAL_CULTURES.get(region, cls.REGIONAL_CULTURES['central'])
        
        return {
            'formality_level': formality['level'],
            'preferred_style': regional_data['preferred_formality'],
            'communication_approach': regional_data['communication_style'],
            'business_pace': regional_data['business_pace'],
            'relationship_focus': regional_data['relationship_building'],
            'recommended_particles': formality['recommended_particles']
        }
    
    @classmethod
    def _get_appropriate_particles(cls, formality_level: str) -> List[str]:
        """Get appropriate politeness particles for formality level"""
        particle_map = {
            'formal': ['ครับ', 'ค่ะ', 'กรุณา', 'ขอ'],
            'polite': ['ครับ', 'ค่ะ', 'นะ', 'หน่อย'],
            'casual': ['นะ', 'จ้ะ', 'เดี๋ยว'],
            'neutral': ['ครับ', 'ค่ะ']
        }
        
        return particle_map.get(formality_level, particle_map['neutral'])
    
    @classmethod
    def generate_culturally_appropriate_response_guidelines(cls, cultural_analysis: Dict) -> str:
        """Generate response guidelines based on cultural analysis"""
        formality = cultural_analysis['formality_level']['level']
        region = cultural_analysis['regional_context']
        values = cultural_analysis['cultural_values']
        
        regional_data = cls.REGIONAL_CULTURES.get(region, cls.REGIONAL_CULTURES['central'])
        
        guidelines = f"""
CULTURAL RESPONSE GUIDELINES:

COMMUNICATION STYLE:
- Formality Level: {formality.upper()}
- Regional Approach: {regional_data['communication_style']}
- Business Pace: {regional_data['business_pace']}
- Recommended Particles: {', '.join(cultural_analysis['communication_style']['recommended_particles'])}

CULTURAL VALUES TO EMPHASIZE:
{chr(10).join(f'- {value}: {cls.CULTURAL_VALUES["core_values"][value]["business_application"]}' for value in values if value in cls.CULTURAL_VALUES["core_values"])}

RELATIONSHIP BUILDING:
- Focus: {regional_data['relationship_building']}
- Hierarchy Respect: {'Required' if cultural_analysis['hierarchy_awareness']['needs_respect'] else 'Standard'}
- Face-Saving: Always use diplomatic language and positive framing

BUDDHIST BUSINESS VALUES:
{chr(10).join(f'- {area}: Emphasize ethical practices and long-term thinking' for area, detected in cultural_analysis['religious_sensitivity'].items() if detected)}

RESPONSE TONE:
- Be warm and respectful (เป็นกันเอง but professional)
- Use appropriate Thai politeness levels
- Show genuine interest in helping (น้ำใจ)
- Maintain face-saving approach in all suggestions
"""
        
        return guidelines

# Global instance for easy import
thai_cultural_engine = ThaiCulturalEngine()