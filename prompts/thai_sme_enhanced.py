"""
Enhanced Thai SME Business Advisory Prompt System
World-class cultural intelligence and business accuracy for Thai entrepreneurs
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

class ThaiSMEIntelligence:
    """Advanced Thai SME business intelligence and cultural context engine"""
    
    # Enhanced Industry Contexts with Thai Market Specifics
    INDUSTRY_CONTEXTS = {
        'retail': {
            'thai_name': 'ธุรกิจค้าปลีก',
            'context': 'retail operations, e-commerce, marketplace integration, Thai consumer behavior',
            'key_challenges': ['inventory management', 'online-offline integration', 'customer loyalty', 'pricing competition'],
            'opportunities': ['social commerce', 'live streaming sales', 'community marketing', 'local delivery'],
            'resources': ['Shopee Seller Center', 'Lazada Seller', 'Facebook Commerce', 'LINE Shopping'],
            'regulations': ['consumer protection', 'e-commerce licensing', 'VAT obligations'],
            'cultural_notes': 'Emphasize relationship-building (สร้างความสัมพันธ์), social proof, and community trust'
        },
        'food': {
            'thai_name': 'ธุรกิจอาหารและเครื่องดื่ม',
            'context': 'restaurant operations, street food business, food delivery, catering services',
            'key_challenges': ['food safety compliance', 'delivery logistics', 'cost management', 'seasonal demand'],
            'opportunities': ['food delivery apps', 'ghost kitchens', 'healthy food trends', 'authentic Thai cuisine export'],
            'resources': ['Food Panda Partner', 'Grab Food', 'Line Man', 'Foodtech Thailand'],
            'regulations': ['food safety standards', 'restaurant licensing', 'halal certification'],
            'cultural_notes': 'Respect for traditional recipes, family heritage, and communal dining culture'
        },
        'manufacturing': {
            'thai_name': 'ธุรกิจการผลิต',
            'context': 'production processes, quality control, supply chain, export markets',
            'key_challenges': ['production efficiency', 'quality standards', 'skilled labor', 'raw material costs'],
            'opportunities': ['Industry 4.0', 'automation', 'sustainable manufacturing', 'regional supply chains'],
            'resources': ['Board of Investment', 'Industrial Estate Authority', 'FTI Federation'],
            'regulations': ['industrial standards', 'environmental compliance', 'export licensing'],
            'cultural_notes': 'Emphasis on craftsmanship quality, long-term relationships with suppliers'
        },
        'agriculture': {
            'thai_name': 'ธุรกิจเกษตรกรรม',
            'context': 'farming operations, agricultural products, agri-tech, sustainable practices',
            'key_challenges': ['climate variability', 'market prices', 'modern farming techniques', 'access to finance'],
            'opportunities': ['organic farming', 'agri-tech solutions', 'direct-to-consumer sales', 'export markets'],
            'resources': ['Ministry of Agriculture', 'Bank for Agriculture', 'CP Group initiatives'],
            'regulations': ['organic certification', 'GAP standards', 'export quality standards'],
            'cultural_notes': 'Deep respect for land, traditional knowledge, and sustainable practices'
        },
        'services': {
            'thai_name': 'ธุรกิจบริการ',
            'context': 'professional services, consulting, digital transformation, B2B relationships',
            'key_challenges': ['service differentiation', 'client acquisition', 'digital adoption', 'skill development'],
            'opportunities': ['digital services', 'automation', 'regional expansion', 'government contracts'],
            'resources': ['Professional associations', 'Skills development programs', 'Government procurement'],
            'regulations': ['professional licensing', 'service standards', 'data protection'],
            'cultural_notes': 'Importance of personal relationships, trust-building, and service excellence'
        },
        'technology': {
            'thai_name': 'ธุรกิจเทคโนโลยี',
            'context': 'software development, tech startups, digital solutions, fintech services',
            'key_challenges': ['talent acquisition', 'funding access', 'market validation', 'regulatory compliance'],
            'opportunities': ['digital Thailand initiatives', 'fintech sandbox', 'ASEAN market', 'government digitization'],
            'resources': ['DEPA', 'Software Industry Promotion Agency', 'Tech startup accelerators'],
            'regulations': ['cybersecurity law', 'fintech regulations', 'data protection'],
            'cultural_notes': 'Balance between innovation and traditional business values'
        },
        'tourism': {
            'thai_name': 'ธุรกิจท่องเที่ยว',
            'context': 'hospitality services, tour operations, cultural tourism, eco-tourism',
            'key_challenges': ['seasonal fluctuations', 'competition', 'service quality', 'marketing reach'],
            'opportunities': ['sustainable tourism', 'cultural experiences', 'wellness tourism', 'digital marketing'],
            'resources': ['Tourism Authority of Thailand', 'Thai Hotels Association', 'Tour operator associations'],
            'regulations': ['tourism business licensing', 'safety standards', 'environmental compliance'],
            'cultural_notes': 'Thai hospitality (การต้อนรับ), cultural authenticity, and service with a smile (ยิ้ม)'
        },
        'logistics': {
            'thai_name': 'ธุรกิจโลจิสติกส์',
            'context': 'supply chain management, delivery services, warehousing, cross-border trade',
            'key_challenges': ['traffic congestion', 'fuel costs', 'technology adoption', 'last-mile delivery'],
            'opportunities': ['e-commerce growth', 'regional trade', 'automation', 'green logistics'],
            'resources': ['Department of Land Transport', 'Port Authority', 'Logistics associations'],
            'regulations': ['transport licensing', 'customs procedures', 'safety standards'],
            'cultural_notes': 'Relationship-based partnerships, reliability, and service commitment'
        }
    }
    
    # Business Stage Intelligence with Thai Context
    BUSINESS_STAGES = {
        'startup': {
            'thai_name': 'ธุรกิจเริ่มต้น',
            'characteristics': ['idea validation', 'initial funding', 'team formation', 'product development'],
            'focus_areas': ['business model validation', 'legal registration', 'initial market testing', 'bootstrap funding'],
            'common_challenges': ['limited capital', 'market uncertainty', 'regulatory navigation', 'team building'],
            'success_factors': ['market research', 'lean operations', 'networking', 'perseverance'],
            'thai_context': 'Emphasis on careful planning (วางแผน), seeking elder advice, and building community support',
            'resources': ['OSMEP startup programs', 'SME One registration', 'Startup Thailand', 'Young entrepreneur grants']
        },
        'growth': {
            'thai_name': 'ธุรกิจขยายตัว',
            'characteristics': ['scaling operations', 'market expansion', 'team growth', 'system development'],
            'focus_areas': ['operational efficiency', 'market penetration', 'funding rounds', 'technology adoption'],
            'common_challenges': ['cash flow management', 'quality control', 'talent acquisition', 'competition'],
            'success_factors': ['strategic planning', 'operational excellence', 'customer retention', 'innovation'],
            'thai_context': 'Maintaining relationships while scaling, preserving company culture, regional expansion',
            'resources': ['SME growth funding', 'Business development programs', 'Export assistance', 'Skills training']
        },
        'established': {
            'thai_name': 'ธุรกิจที่มั่นคง',
            'characteristics': ['stable operations', 'market position', 'mature processes', 'diversification'],
            'focus_areas': ['optimization', 'innovation', 'market leadership', 'sustainability'],
            'common_challenges': ['market saturation', 'digital transformation', 'next-gen leadership', 'competition'],
            'success_factors': ['continuous improvement', 'innovation', 'brand building', 'talent development'],
            'thai_context': 'Succession planning, giving back to community, maintaining competitive edge',
            'resources': ['Advanced training programs', 'Export promotion', 'Innovation support', 'CSR initiatives']
        },
        'pivot': {
            'thai_name': 'ธุรกิจปรับเปลี่ยน',
            'characteristics': ['business model change', 'market repositioning', 'restructuring', 'adaptation'],
            'focus_areas': ['strategic realignment', 'cost optimization', 'new market entry', 'change management'],
            'common_challenges': ['resistance to change', 'resource constraints', 'market acceptance', 'timing'],
            'success_factors': ['agility', 'stakeholder buy-in', 'clear communication', 'execution speed'],
            'thai_context': 'Saving face while changing direction, maintaining relationships, seeking consensus',
            'resources': ['Business turnaround support', 'Restructuring assistance', 'Market research', 'Change management']
        }
    }
    
    # Regional Business Context Intelligence
    REGIONAL_CONTEXTS = {
        'bangkok': {
            'thai_name': 'กรุงเทพมหานคร',
            'characteristics': ['high competition', 'diverse markets', 'advanced infrastructure', 'international exposure'],
            'opportunities': ['large customer base', 'supplier networks', 'talent pool', 'investment access'],
            'challenges': ['high costs', 'traffic congestion', 'intense competition', 'regulatory complexity'],
            'business_culture': 'Fast-paced, formal, hierarchy-conscious, international outlook'
        },
        'central': {
            'thai_name': 'ภาคกลาง',
            'characteristics': ['agricultural base', 'manufacturing hubs', 'tourism areas', 'proximity to Bangkok'],
            'opportunities': ['lower costs', 'agricultural supply chains', 'tourism markets', 'industrial estates'],
            'challenges': ['limited talent', 'infrastructure gaps', 'seasonal fluctuations', 'market access'],
            'business_culture': 'Relationship-focused, traditional, community-oriented, agricultural heritage'
        },
        'northern': {
            'thai_name': 'ภาคเหนือ',
            'characteristics': ['cultural heritage', 'tourism', 'agriculture', 'handicrafts'],
            'opportunities': ['cultural tourism', 'authentic products', 'mountain agriculture', 'cross-border trade'],
            'challenges': ['transportation costs', 'limited infrastructure', 'seasonal tourism', 'market reach'],
            'business_culture': 'Traditional values, community cooperation, pride in heritage, deliberate decision-making'
        },
        'northeastern': {
            'thai_name': 'ภาคตะวันออกเฉียงเหนือ',
            'characteristics': ['agricultural economy', 'cultural distinctiveness', 'growing urbanization', 'border trade'],
            'opportunities': ['agricultural innovation', 'cultural products', 'Vietnam-Laos trade', 'energy projects'],
            'challenges': ['economic disparities', 'infrastructure development', 'market access', 'climate challenges'],
            'business_culture': 'Strong community bonds, mutual assistance, traditional values, resilience'
        },
        'southern': {
            'thai_name': 'ภาคใต้',
            'characteristics': ['tourism economy', 'maritime industries', 'rubber and palm oil', 'fishing'],
            'opportunities': ['tourism services', 'marine products', 'agricultural processing', 'Malaysia trade'],
            'challenges': ['political sensitivities', 'transportation', 'seasonal tourism', 'natural disasters'],
            'business_culture': 'Maritime traditions, multi-cultural awareness, tourism hospitality, trade networks'
        }
    }
    
    # Cultural Intelligence Patterns
    CULTURAL_PATTERNS = {
        'communication_style': {
            'formal_indicators': ['เรียน', 'ท่าน', 'คุณ', 'การ', 'เพื่อ'],
            'polite_particles': ['ครับ', 'ค่ะ', 'นะครับ', 'นะคะ', 'ขอ', 'กรุณา'],
            'informal_indicators': ['เดี๋ยว', 'อีก', 'แป๊บ', 'เอาจริง', 'โอเค'],
            'business_terms': ['ธุรกิจ', 'บริษัท', 'การค้า', 'การตลาด', 'กำไร', 'ต้นทุน']
        },
        'relationship_building': {
            'importance': 'critical',
            'key_concepts': ['kreng-jai (เกร็งใจ)', 'sanook (สนุก)', 'long-term thinking', 'mutual benefit'],
            'approaches': ['personal meetings', 'social activities', 'family involvement', 'gradual trust building']
        },
        'decision_making': {
            'style': 'consensus-building',
            'factors': ['hierarchy respect', 'face-saving', 'group harmony', 'long-term impact'],
            'process': ['consultation', 'deliberation', 'consensus seeking', 'implementation']
        }
    }
    
    @classmethod
    def detect_business_context(cls, user_message: str, user_context: Dict) -> Dict[str, Any]:
        """Detect business context from user message and profile"""
        context = {
            'industry': cls._detect_industry(user_message, user_context),
            'stage': cls._detect_business_stage(user_message, user_context),
            'region': cls._detect_region(user_context),
            'formality': cls._detect_formality_level(user_message),
            'urgency': cls._detect_urgency(user_message),
            'cultural_sensitivity': cls._assess_cultural_sensitivity(user_message)
        }
        
        return context
    
    @classmethod
    def _detect_industry(cls, message: str, context: Dict) -> str:
        """Detect industry from message content and context"""
        message_lower = message.lower()
        
        # Direct industry mentions
        for industry, details in cls.INDUSTRY_CONTEXTS.items():
            if industry in message_lower or details['thai_name'] in message:
                return industry
            
            # Check for industry-specific keywords
            for keyword in details.get('key_challenges', []) + details.get('opportunities', []):
                if keyword.lower() in message_lower:
                    return industry
        
        # Context-based detection
        industry_keywords = {
            'retail': ['ขาย', 'ร้าน', 'สินค้า', 'ลูกค้า', 'ออนไลน์', 'shopee', 'lazada'],
            'food': ['อาหาร', 'ร้านอาหาร', 'เมนู', 'delivery', 'กิน', 'ครัว', 'foodpanda'],
            'manufacturing': ['ผลิต', 'โรงงาน', 'เครื่องจักร', 'คุณภาพ', 'ส่งออก', 'มาตรฐาน'],
            'agriculture': ['เกษตร', 'ปลูก', 'เก็บเกี่ยว', 'พืช', 'ไร่', 'สวน', 'ปุ๋ย'],
            'services': ['บริการ', 'ที่ปรึกษา', 'คำแนะนำ', 'ช่วยเหลือ', 'งานบริการ'],
            'technology': ['เทคโนโลยี', 'software', 'app', 'digital', 'AI', 'website'],
            'tourism': ['ท่องเที่ยว', 'โรงแรม', 'รีสอร์ท', 'ไกด์', 'นักท่องเที่ยว'],
            'logistics': ['ขนส่ง', 'delivery', 'โลจิสติกส์', 'คลังสินค้า', 'shipping']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return industry
        
        return context.get('business_type', 'services')
    
    @classmethod
    def _detect_business_stage(cls, message: str, context: Dict) -> str:
        """Detect business stage from message content"""
        message_lower = message.lower()
        
        stage_keywords = {
            'startup': ['เริ่มต้น', 'ใหม่', 'แรกเริ่ม', 'start', 'begin', 'new business', 'เปิดธุรกิจ'],
            'growth': ['ขยาย', 'เติบโต', 'พัฒนา', 'expand', 'grow', 'scale', 'เพิ่ม'],
            'established': ['มั่นคง', 'ประสบความสำเร็จ', 'established', 'stable', 'mature', 'นานแล้ว'],
            'pivot': ['เปลี่ยน', 'ปรับ', 'แก้ไข', 'change', 'pivot', 'restructure', 'ปรับปรุง']
        }
        
        for stage, keywords in stage_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return stage
        
        return context.get('stage', 'growth')
    
    @classmethod
    def _detect_region(cls, context: Dict) -> str:
        """Detect region from user context"""
        location = context.get('location', '').lower()
        
        if 'bangkok' in location or 'กรุงเทพ' in location:
            return 'bangkok'
        elif any(region in location for region in ['chiang mai', 'เชียงใหม่', 'north', 'เหนือ']):
            return 'northern'
        elif any(region in location for region in ['isaan', 'อีสาน', 'northeast', 'ตะวันออกเฉียงเหนือ']):
            return 'northeastern'
        elif any(region in location for region in ['south', 'ใต้', 'phuket', 'ภูเก็ต']):
            return 'southern'
        else:
            return 'central'
    
    @classmethod
    def _detect_formality_level(cls, message: str) -> str:
        """Detect appropriate formality level"""
        formal_count = sum(1 for indicator in cls.CULTURAL_PATTERNS['communication_style']['formal_indicators'] 
                          if indicator in message)
        polite_count = sum(1 for particle in cls.CULTURAL_PATTERNS['communication_style']['polite_particles'] 
                          if particle in message)
        
        if formal_count > 0 or polite_count > 1:
            return 'formal'
        elif polite_count > 0:
            return 'polite'
        else:
            return 'casual'
    
    @classmethod
    def _detect_urgency(cls, message: str) -> str:
        """Detect urgency level from message"""
        urgent_keywords = ['ด่วน', 'เร่งด่วน', 'urgent', 'asap', 'รีบ', 'เซ็ง', 'วิกฤต']
        normal_keywords = ['ช่วย', 'แนะนำ', 'ปรึกษา', 'suggest', 'advice']
        
        if any(keyword in message.lower() for keyword in urgent_keywords):
            return 'high'
        elif any(keyword in message.lower() for keyword in normal_keywords):
            return 'normal'
        else:
            return 'low'
    
    @classmethod
    def _assess_cultural_sensitivity(cls, message: str) -> Dict[str, Any]:
        """Assess cultural sensitivity requirements"""
        return {
            'requires_hierarchy_respect': 'เจ้านาย' in message or 'ผู้บริหาร' in message,
            'family_business_context': 'ครอบครัว' in message or 'family' in message.lower(),
            'religious_consideration': 'บุญ' in message or 'merit' in message.lower(),
            'face_saving_important': 'เสียหน้า' in message or 'reputation' in message.lower()
        }
    
    @classmethod
    def generate_enhanced_prompt(cls, user_message: str, user_context: Dict, context_type: str = 'conversation') -> str:
        """Generate culturally intelligent and industry-specific prompt"""
        
        # Detect business context
        business_context = cls.detect_business_context(user_message, user_context)
        
        # Get industry and stage details
        industry = business_context['industry']
        stage = business_context['stage']
        region = business_context['region']
        
        industry_details = cls.INDUSTRY_CONTEXTS.get(industry, cls.INDUSTRY_CONTEXTS['services'])
        stage_details = cls.BUSINESS_STAGES.get(stage, cls.BUSINESS_STAGES['growth'])
        region_details = cls.REGIONAL_CONTEXTS.get(region, cls.REGIONAL_CONTEXTS['central'])
        
        # Base system prompt with dynamic intelligence
        enhanced_prompt = f"""Thai SME Business Advisor with Advanced Cultural Intelligence

BUSINESS CONTEXT ANALYSIS:
Industry: {industry_details['thai_name']} ({industry})
Business Stage: {stage_details['thai_name']} ({stage})
Regional Context: {region_details['thai_name']} ({region})
Communication Style: {business_context['formality']} 
Urgency Level: {business_context['urgency']}

INDUSTRY EXPERTISE ({industry_details['thai_name']}):
Context: {industry_details['context']}
Key Challenges: {', '.join(industry_details['key_challenges'])}
Opportunities: {', '.join(industry_details['opportunities'])}
Relevant Resources: {', '.join(industry_details['resources'])}
Regulations: {', '.join(industry_details['regulations'])}

BUSINESS STAGE FOCUS ({stage_details['thai_name']}):
Current Focus: {', '.join(stage_details['focus_areas'])}
Common Challenges: {', '.join(stage_details['common_challenges'])}
Success Factors: {', '.join(stage_details['success_factors'])}
Thai Context: {stage_details['thai_context']}
Relevant Resources: {', '.join(stage_details['resources'])}

REGIONAL BUSINESS INTELLIGENCE ({region_details['thai_name']}):
Market Characteristics: {', '.join(region_details['characteristics'])}
Business Opportunities: {', '.join(region_details['opportunities'])}
Local Challenges: {', '.join(region_details['challenges'])}
Business Culture: {region_details['business_culture']}

CULTURAL COMMUNICATION GUIDELINES:
- Use {business_context['formality']} communication style
- Apply appropriate Thai politeness levels (ครับ/ค่ะ based on context)
- Respect Thai business hierarchy and relationship dynamics
- Consider Buddhist values: merit-making, karma, long-term thinking
- Emphasize relationship-building (สร้างความสัมพันธ์) and mutual benefit
- Show understanding of Thai SME challenges and opportunities

RESPONSE REQUIREMENTS:
1. Provide industry-specific advice using relevant Thai business terminology
2. Address stage-appropriate challenges and opportunities
3. Include relevant government resources and support programs
4. Respect regional business culture and practices
5. Use culturally appropriate examples and case studies
6. Maintain warm, supportive tone (เป็นกันเอง) while being professional
7. Include actionable next steps suitable for Thai SME context

THAI SME RESOURCE INTEGRATION:
- OSMEP (สำนักงานส่งเสริมวิสาหกิจขนาดกลางและขนาดย่อม)
- SME One Portal for government services
- Industry-specific associations and support programs
- Banking and financial support (SME Bank, KTB, etc.)
- Digital transformation programs (DEPA, Digital Thailand)

Respond naturally in the user's language with deep Thai business cultural understanding."""

        return enhanced_prompt

# Global instance for easy import
thai_sme_intelligence = ThaiSMEIntelligence()