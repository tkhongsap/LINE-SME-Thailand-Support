"""
Industry-Specific Business Contexts for Thai SME Advisory System
Comprehensive business intelligence for different industry sectors in Thailand
"""

from typing import Dict, List, Any
from datetime import datetime

class ThaiIndustryContexts:
    """Comprehensive industry-specific business contexts for Thai SME advisory"""
    
    # Detailed Industry Profiles with Thai Market Intelligence
    INDUSTRY_PROFILES = {
        'retail': {
            'industry_info': {
                'thai_name': 'ธุรกิจค้าปลีก',
                'english_name': 'Retail & E-commerce',
                'market_size': 'THB 4.2 trillion (2023)',
                'growth_rate': '8.5% annually',
                'digital_penetration': '65%'
            },
            'business_models': [
                'traditional retail stores', 'online marketplaces', 'social commerce',
                'omnichannel retail', 'subscription services', 'direct-to-consumer'
            ],
            'thai_consumer_behavior': {
                'shopping_patterns': ['price-conscious', 'brand loyalty', 'social influence', 'convenience-focused'],
                'preferred_channels': ['Shopee', 'Lazada', 'Facebook', 'LINE Shopping', 'physical stores'],
                'payment_preferences': ['mobile banking', 'cash on delivery', 'QR codes', 'installments'],
                'decision_factors': ['price', 'reviews', 'brand reputation', 'convenience', 'promotions']
            },
            'market_opportunities': [
                'Social commerce growth (live streaming sales)',
                'Rural market penetration',
                'Sustainable products demand',
                'Health and wellness trends',
                'Premium local brands',
                'Cross-border e-commerce'
            ],
            'key_challenges': [
                'Intense price competition',
                'Inventory management complexity',
                'Last-mile delivery costs',
                'Customer acquisition costs',
                'Seasonal demand fluctuations',
                'Platform dependency risks'
            ],
            'success_strategies': [
                'Build strong brand community',
                'Leverage influencer partnerships',
                'Optimize inventory turnover',
                'Focus on customer experience',
                'Develop omnichannel presence',
                'Use data analytics for insights'
            ],
            'technology_needs': [
                'POS systems', 'inventory management', 'CRM systems', 
                'e-commerce platforms', 'analytics tools', 'payment gateways'
            ],
            'regulatory_requirements': [
                'Business registration (DBD)',
                'VAT registration (if revenue > 1.8M)',
                'Consumer protection compliance',
                'Product safety standards',
                'Online business licensing',
                'Data protection (PDPA)'
            ],
            'financial_considerations': {
                'startup_capital': 'THB 100K - 2M',
                'working_capital_needs': '30-45 days inventory',
                'profit_margins': '15-40% depending on category',
                'funding_sources': ['personal savings', 'SME loans', 'crowdfunding', 'angel investors']
            },
            'thai_resources': [
                'Thai Retailers Association',
                'E-commerce Association of Thailand', 
                'Department of Business Development',
                'Shopee Seller Education',
                'Lazada University',
                'Facebook Blueprint Thailand'
            ]
        },
        
        'food': {
            'industry_info': {
                'thai_name': 'ธุรกิจอาหารและเครื่องดื่ม',
                'english_name': 'Food & Beverage',
                'market_size': 'THB 800 billion (2023)',
                'growth_rate': '6.2% annually',
                'digital_penetration': '45%'
            },
            'business_models': [
                'restaurants', 'street food', 'catering services', 'food delivery',
                'ghost kitchens', 'food trucks', 'cloud restaurants', 'franchising'
            ],
            'thai_food_culture': {
                'dining_preferences': ['fresh ingredients', 'spicy flavors', 'communal dining', 'street food culture'],
                'meal_patterns': ['multiple small meals', 'late night eating', 'social dining', 'food sharing'],
                'popular_cuisines': ['Thai traditional', 'Thai-Chinese', 'Korean', 'Japanese', 'Western fusion'],
                'health_trends': ['organic food', 'plant-based options', 'low-sugar drinks', 'functional foods']
            },
            'market_opportunities': [
                'Food delivery market expansion',
                'Healthy food segment growth',
                'Premium Thai cuisine export',
                'Food tourism experiences',
                'Halal food market',
                'Organic and sustainable food'
            ],
            'key_challenges': [
                'Food safety compliance',
                'Rising ingredient costs',
                'Labor shortage and costs',
                'Delivery logistics complexity',
                'Seasonal ingredient availability',
                'Competition from chains'
            ],
            'success_strategies': [
                'Focus on signature dishes',
                'Maintain consistent quality',
                'Build customer loyalty programs',
                'Optimize delivery operations',
                'Leverage social media marketing',
                'Control food costs effectively'
            ],
            'technology_needs': [
                'POS systems', 'inventory management', 'delivery apps integration',
                'kitchen management systems', 'customer ordering systems', 'food safety monitoring'
            ],
            'regulatory_requirements': [
                'Restaurant license (ใบอนุญาตประกอบการร้านอาหาร)',
                'Food handler certificates',
                'Health department approvals',
                'Fire safety certificates',
                'Alcohol serving license (if applicable)',
                'Halal certification (if targeting Muslim market)'
            ],
            'financial_considerations': {
                'startup_capital': 'THB 300K - 5M',
                'food_cost_ratio': '25-35% of revenue',
                'labor_cost_ratio': '25-35% of revenue',
                'profit_margins': '10-25% depending on segment'
            },
            'thai_resources': [
                'Thai Restaurant Association',
                'Department of Health',
                'Food and Drug Administration',
                'Grab Food Partner Program',
                'Food Panda Partner Center',
                'Line Man Merchant Support'
            ]
        },
        
        'manufacturing': {
            'industry_info': {
                'thai_name': 'ธุรกิจการผลิต',
                'english_name': 'Manufacturing',
                'market_size': 'THB 5.8 trillion (2023)',
                'growth_rate': '4.8% annually',
                'export_value': 'THB 8.2 trillion'
            },
            'business_models': [
                'OEM manufacturing', 'ODM services', 'private label production',
                'contract manufacturing', 'component manufacturing', 'assembly services'
            ],
            'thai_manufacturing_strengths': {
                'competitive_advantages': ['skilled workforce', 'strategic location', 'government support', 'industrial infrastructure'],
                'key_sectors': ['automotive', 'electronics', 'textiles', 'food processing', 'petrochemicals'],
                'export_markets': ['ASEAN', 'China', 'Japan', 'USA', 'EU'],
                'industry_40_adoption': ['automation', 'IoT integration', 'data analytics', 'smart factories']
            },
            'market_opportunities': [
                'Industry 4.0 transformation',
                'Sustainable manufacturing',
                'Regional supply chain integration',
                'Electric vehicle components',
                'Medical device manufacturing',
                'High-tech electronics'
            ],
            'key_challenges': [
                'Rising labor costs',
                'Skills shortage in technical areas',
                'Environmental compliance',
                'Supply chain disruptions',
                'Technology upgrade costs',
                'Competition from other ASEAN countries'
            ],
            'success_strategies': [
                'Invest in automation technology',
                'Focus on quality certifications',
                'Develop long-term supplier relationships',
                'Build skilled workforce',
                'Pursue export market diversification',
                'Adopt lean manufacturing principles'
            ],
            'technology_needs': [
                'ERP systems', 'quality management systems', 'production planning software',
                'inventory management', 'supply chain management', 'IoT monitoring systems'
            ],
            'regulatory_requirements': [
                'Industrial license (โรงงาน)',
                'Environmental impact assessment',
                'ISO quality certifications',
                'Export licenses',
                'Safety and health compliance',
                'BOI investment promotion (if applicable)'
            ],
            'financial_considerations': {
                'startup_capital': 'THB 2M - 50M+',
                'working_capital_needs': '60-90 days',
                'profit_margins': '8-20% depending on complexity',
                'funding_sources': ['SME loans', 'BOI incentives', 'industrial estate financing']
            },
            'thai_resources': [
                'Federation of Thai Industries (FTI)',
                'Board of Investment (BOI)',
                'Industrial Estate Authority',
                'Department of Industrial Works',
                'Thailand Productivity Institute',
                'SME Bank manufacturing loans'
            ]
        },
        
        'agriculture': {
            'industry_info': {
                'thai_name': 'ธุรกิจเกษตรกรรม',
                'english_name': 'Agriculture & Agribusiness',
                'market_size': 'THB 1.8 trillion (2023)',
                'growth_rate': '3.2% annually',
                'employment': '32% of Thai workforce'
            },
            'business_models': [
                'crop farming', 'livestock farming', 'aquaculture', 'agro-processing',
                'organic farming', 'contract farming', 'agricultural services', 'farm-to-table'
            ],
            'thai_agricultural_assets': {
                'climate_advantages': ['tropical climate', 'year-round growing', 'diverse ecosystems', 'abundant water'],
                'key_crops': ['rice', 'cassava', 'sugarcane', 'rubber', 'palm oil', 'fruits', 'vegetables'],
                'export_strengths': ['processed foods', 'tropical fruits', 'organic products', 'seafood'],
                'traditional_knowledge': ['sustainable practices', 'crop rotation', 'integrated farming', 'water management']
            },
            'market_opportunities': [
                'Organic and sustainable farming',
                'Agri-tech and precision farming',
                'Value-added processing',
                'Direct-to-consumer sales',
                'Export market expansion',
                'Agro-tourism integration'
            ],
            'key_challenges': [
                'Climate change impacts',
                'Volatile commodity prices',
                'Limited access to modern technology',
                'Fragmented land ownership',
                'Post-harvest losses',
                'Market access for small farmers'
            ],
            'success_strategies': [
                'Adopt sustainable farming practices',
                'Invest in post-harvest technology',
                'Form farmer cooperatives',
                'Diversify crop portfolio',
                'Build direct market channels',
                'Pursue organic certification'
            ],
            'technology_needs': [
                'irrigation systems', 'greenhouse technology', 'processing equipment',
                'cold storage', 'farm management software', 'IoT monitoring systems'
            ],
            'regulatory_requirements': [
                'GAP (Good Agricultural Practices) certification',
                'Organic certification',
                'Export quality standards',
                'Pesticide usage regulations',
                'Water usage permits',
                'Land use compliance'
            ],
            'financial_considerations': {
                'startup_capital': 'THB 200K - 10M',
                'seasonal_cash_flow': 'Need working capital for 3-6 months',
                'profit_margins': '10-30% depending on crop and value-add',
                'funding_sources': ['Bank for Agriculture', 'BAAC loans', 'cooperative financing']
            },
            'thai_resources': [
                'Ministry of Agriculture and Cooperatives',
                'Bank for Agriculture and Agricultural Cooperatives (BAAC)',
                'Department of Agriculture',
                'Office of Agricultural Economics',
                'Kasetsart University extension services',
                'Royal Project Foundation'
            ]
        },
        
        'technology': {
            'industry_info': {
                'thai_name': 'ธุรกิจเทคโนโลยี',
                'english_name': 'Technology & Digital Services',
                'market_size': 'THB 400 billion (2023)',
                'growth_rate': '15.8% annually',
                'digital_economy_target': '30% of GDP by 2027'
            },
            'business_models': [
                'software development', 'mobile app development', 'web development',
                'fintech services', 'e-commerce platforms', 'digital marketing services', 'SaaS solutions'
            ],
            'thai_digital_landscape': {
                'internet_penetration': '85% of population',
                'mobile_penetration': '95% of adults',
                'popular_platforms': ['LINE', 'Facebook', 'TikTok', 'YouTube', 'Instagram'],
                'fintech_adoption': ['mobile banking', 'QR payments', 'digital wallets', 'P2P transfers'],
                'government_initiatives': ['Digital Thailand 2030', 'Smart City projects', 'Digital Government']
            },
            'market_opportunities': [
                'Fintech and digital payments',
                'EdTech and online learning',
                'HealthTech and telemedicine',
                'AgriTech solutions',
                'Government digital transformation',
                'Regional expansion to ASEAN'
            ],
            'key_challenges': [
                'Talent shortage in tech skills',
                'Competition from global players',
                'Regulatory compliance complexity',
                'Cybersecurity threats',
                'Funding access for startups',
                'Digital divide in rural areas'
            ],
            'success_strategies': [
                'Focus on local market needs',
                'Build strong technical team',
                'Ensure regulatory compliance',
                'Develop strategic partnerships',
                'Invest in cybersecurity',
                'Create scalable solutions'
            ],
            'technology_needs': [
                'cloud infrastructure', 'development tools', 'security solutions',
                'analytics platforms', 'payment gateways', 'API management'
            ],
            'regulatory_requirements': [
                'Digital business license',
                'PDPA compliance',
                'Cybersecurity law compliance',
                'Fintech regulatory sandbox (if applicable)',
                'Software copyright registration',
                'Data localization requirements'
            ],
            'financial_considerations': {
                'startup_capital': 'THB 500K - 20M',
                'development_costs': '60-80% of initial investment',
                'monthly_burn_rate': 'THB 100K - 2M depending on team size',
                'funding_sources': ['angel investors', 'VC funds', 'government grants', 'crowdfunding']
            },
            'thai_resources': [
                'Digital Economy Promotion Agency (DEPA)',
                'Software Industry Promotion Agency (SIPA)',
                'National Innovation Agency (NIA)',
                'Thai Fintech Association',
                'Startup Thailand',
                'Government Savings Bank Startup Fund'
            ]
        }
    }
    
    @classmethod
    def get_industry_context(cls, industry: str) -> Dict[str, Any]:
        """Get comprehensive industry context"""
        # Default to retail if industry not found
        return cls.INDUSTRY_PROFILES.get(industry, cls.INDUSTRY_PROFILES['retail'])
    
    @classmethod
    def get_industry_advice_template(cls, industry: str, business_stage: str) -> str:
        """Generate industry-specific advice template"""
        context = cls.get_industry_context(industry)
        
        template = f"""
INDUSTRY: {context['industry_info']['thai_name']} ({context['industry_info']['english_name']})

MARKET OVERVIEW:
• Market Size: {context['industry_info']['market_size']}
• Growth Rate: {context['industry_info']['growth_rate']} 
• Key Opportunities: {', '.join(context['market_opportunities'][:3])}

BUSINESS STAGE FOCUS ({business_stage.upper()}):
{cls._get_stage_specific_advice(industry, business_stage, context)}

SUCCESS STRATEGIES:
{chr(10).join(f'• {strategy}' for strategy in context['success_strategies'][:5])}

REGULATORY REQUIREMENTS:
{chr(10).join(f'• {req}' for req in context['regulatory_requirements'][:4])}

THAI RESOURCES:
{chr(10).join(f'• {resource}' for resource in context['thai_resources'][:4])}
"""
        return template
    
    @classmethod
    def _get_stage_specific_advice(cls, industry: str, stage: str, context: Dict) -> str:
        """Get stage-specific advice for industry"""
        stage_advice = {
            'startup': f"""
• Initial Capital Needed: {context['financial_considerations'].get('startup_capital', 'Varies')}
• Key Focus: Market validation, regulatory compliance, initial team building
• First Steps: Business registration, permits, initial funding, prototype development
• Challenges: {', '.join(context['key_challenges'][:2])}
""",
            'growth': f"""
• Growth Capital: Consider additional funding for expansion
• Key Focus: Scaling operations, market expansion, team development
• Technology Needs: {', '.join(context['technology_needs'][:3])}
• Challenges: {', '.join(context['key_challenges'][2:4])}
""",
            'established': f"""
• Optimization Focus: Efficiency improvements, technology upgrades
• Market Position: Leverage competitive advantages, explore new markets
• Innovation: Consider R&D investments, new product development
• Sustainability: Environmental and social responsibility initiatives
""",
            'pivot': f"""
• Strategic Review: Assess market position and competitive landscape
• Resource Reallocation: Optimize costs, realign investments
• Market Opportunities: {', '.join(context['market_opportunities'][:2])}
• Risk Management: Diversification, contingency planning
"""
        }
        
        return stage_advice.get(stage, stage_advice['growth'])
    
    @classmethod
    def get_industry_specific_resources(cls, industry: str) -> List[str]:
        """Get industry-specific resources and support"""
        context = cls.get_industry_context(industry)
        return context.get('thai_resources', [])
    
    @classmethod
    def get_regulatory_checklist(cls, industry: str) -> List[str]:
        """Get industry-specific regulatory checklist"""
        context = cls.get_industry_context(industry)
        return context.get('regulatory_requirements', [])
    
    @classmethod 
    def get_financial_benchmarks(cls, industry: str) -> Dict[str, Any]:
        """Get industry financial benchmarks"""
        context = cls.get_industry_context(industry)
        return context.get('financial_considerations', {})

# Global instance for easy import
thai_industry_contexts = ThaiIndustryContexts()