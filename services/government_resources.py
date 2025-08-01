"""
Thai Government Resource Integration Service
Real-time integration with Thai government resources and SME support programs
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)

class GovernmentResourceService:
    """Service for integrating Thai government resources and SME support programs"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = Config.GOVERNMENT_RESOURCE_CACHE_TTL
        self.resources_file = Path(__file__).parent.parent / 'data' / 'thai_sme_resources.json'
        
        # Load static resources
        self.static_resources = self._load_static_resources()
        
        logger.info("Government Resource Service initialized")
    
    def _load_static_resources(self) -> Dict[str, Any]:
        """Load static Thai SME resources from JSON file"""
        try:
            with open(self.resources_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading static resources: {e}")
            return {}
    
    def get_relevant_resources(self, industry: str, business_stage: str, region: str = 'central') -> Dict[str, Any]:
        """Get relevant government resources based on business context"""
        resources = {
            'government_support': self._get_government_support(industry, business_stage),
            'funding_options': self._get_funding_options(industry, business_stage),
            'regulatory_info': self._get_regulatory_info(industry),
            'regional_support': self._get_regional_support(region),
            'training_programs': self._get_training_programs(industry, business_stage),
            'industry_associations': self._get_industry_associations(industry)
        }
        
        return resources
    
    def _get_government_support(self, industry: str, business_stage: str) -> List[Dict[str, Any]]:
        """Get relevant government support programs"""
        support_programs = []
        
        # OSMEP programs
        osmep = self.static_resources.get('government_agencies', {}).get('osmep', {})
        if osmep:
            support_programs.append({
                'agency': 'OSMEP',
                'name': osmep.get('name'),
                'website': osmep.get('website'),
                'services': osmep.get('services', []),
                'contact': osmep.get('contact', {}),
                'relevance': 'General SME support and development'
            })
        
        # Industry-specific agencies
        if industry in ['manufacturing', 'technology']:
            boi = self.static_resources.get('government_agencies', {}).get('boi', {})
            if boi:
                support_programs.append({
                    'agency': 'BOI',
                    'name': boi.get('name'),
                    'website': boi.get('website'),
                    'services': boi.get('services', []),
                    'relevance': 'Investment promotion and tax incentives'
                })
        
        # Business stage specific
        if business_stage == 'startup':
            support_programs.append({
                'agency': 'SME One Portal',
                'name': 'ศูนย์รวมบริการ SME',
                'website': 'https://www.smeone.go.th',
                'services': ['Business registration', 'License applications', 'One-stop services'],
                'relevance': 'Essential for business setup and registration'
            })
        
        return support_programs
    
    def _get_funding_options(self, industry: str, business_stage: str) -> List[Dict[str, Any]]:
        """Get relevant funding options"""
        funding_options = []
        
        # SME Bank
        sme_bank = self.static_resources.get('financial_institutions', {}).get('sme_bank', {})
        if sme_bank:
            funding_options.append({
                'institution': 'SME Bank',
                'name': sme_bank.get('name'),
                'website': sme_bank.get('website'),
                'products': sme_bank.get('loan_products', []),
                'relevance': 'Specialized SME financing solutions'
            })
        
        # Industry-specific funding
        if industry == 'agriculture':
            baac = self.static_resources.get('financial_institutions', {}).get('baac', {})
            if baac:
                funding_options.append({
                    'institution': 'BAAC',
                    'name': baac.get('name'),
                    'website': baac.get('website'),
                    'services': baac.get('services', []),
                    'relevance': 'Agricultural and rural business financing'
                })
        
        # OSMEP funding programs
        osmep_funding = self.static_resources.get('funding_programs', {}).get('osmep_funding', {})
        if osmep_funding:
            for program in osmep_funding.get('programs', []):
                funding_options.append({
                    'type': 'Government Program',
                    'name': program.get('name'),
                    'description': program.get('description'),
                    'max_amount': program.get('max_amount'),
                    'interest_rate': program.get('interest_rate'),
                    'requirements': program.get('requirements', []),
                    'relevance': f'Government support for {business_stage} businesses'
                })
        
        return funding_options
    
    def _get_regulatory_info(self, industry: str) -> Dict[str, Any]:
        """Get regulatory information for specific industry"""
        regulatory_info = {
            'business_registration': self.static_resources.get('legal_compliance', {}).get('business_registration', {}),
            'licensing_requirements': [],
            'tax_obligations': self.static_resources.get('important_dates', {}).get('tax_deadlines', {}),
            'compliance_checklist': []
        }
        
        # Industry-specific licensing
        licensing = self.static_resources.get('legal_compliance', {}).get('licensing_requirements', {})
        if industry in licensing:
            regulatory_info['licensing_requirements'] = licensing[industry]
        
        # General compliance checklist
        if industry == 'retail':
            regulatory_info['compliance_checklist'] = [
                'Business registration with DBD',
                'VAT registration (if revenue > 1.8M THB)',
                'Consumer protection compliance',
                'Product safety standards',
                'PDPA compliance for customer data'
            ]
        elif industry == 'food':
            regulatory_info['compliance_checklist'] = [
                'Restaurant license',
                'Food handler certificates',
                'Health department approvals',
                'Food safety standards',
                'Halal certification (if applicable)'
            ]
        elif industry == 'manufacturing':
            regulatory_info['compliance_checklist'] = [
                'Factory license',
                'Environmental permits',
                'Industrial safety compliance',
                'Quality certifications (ISO)',
                'Export licenses (if applicable)'
            ]
        
        return regulatory_info
    
    def _get_regional_support(self, region: str) -> Dict[str, Any]:
        """Get regional-specific support and resources"""
        regional_resources = self.static_resources.get('regional_resources', {})
        
        if region in regional_resources:
            return regional_resources[region]
        
        return regional_resources.get('central', {})
    
    def _get_training_programs(self, industry: str, business_stage: str) -> List[Dict[str, Any]]:
        """Get relevant training programs"""
        training_programs = []
        
        # OSMEP training
        osmep_training = self.static_resources.get('training_programs', {}).get('osmep_training', [])
        for program in osmep_training:
            training_programs.append({
                'provider': 'OSMEP',
                'program': program,
                'relevance': 'General SME skills development'
            })
        
        # Digital-focused training
        if industry in ['retail', 'services', 'technology']:
            depa_training = self.static_resources.get('training_programs', {}).get('depa_training', [])
            for program in depa_training:
                training_programs.append({
                    'provider': 'DEPA',
                    'program': program,
                    'relevance': 'Digital transformation and technology skills'
                })
        
        return training_programs
    
    def _get_industry_associations(self, industry: str) -> List[Dict[str, Any]]:
        """Get relevant industry associations"""
        associations = []
        industry_assocs = self.static_resources.get('industry_associations', {})
        
        # General business associations
        if 'cci' in industry_assocs:
            associations.append({
                'name': industry_assocs['cci'].get('name'),
                'website': industry_assocs['cci'].get('website'),
                'services': industry_assocs['cci'].get('services', []),
                'relevance': 'General business networking and certification'
            })
        
        # Industry-specific associations
        if industry == 'manufacturing' and 'fti' in industry_assocs:
            associations.append({
                'name': industry_assocs['fti'].get('name'),
                'website': industry_assocs['fti'].get('website'),
                'services': industry_assocs['fti'].get('services', []),
                'relevance': 'Manufacturing industry support and advocacy'
            })
        elif industry == 'retail' and 'tra' in industry_assocs:
            associations.append({
                'name': industry_assocs['tra'].get('name'),
                'website': industry_assocs['tra'].get('website'),
                'services': industry_assocs['tra'].get('services', []),
                'relevance': 'Retail industry development and standards'
            })
        
        return associations
    
    def get_seasonal_business_info(self) -> Dict[str, Any]:
        """Get seasonal business information"""
        business_calendar = self.static_resources.get('important_dates', {}).get('business_calendar', {})
        current_month = datetime.now().strftime('%B').lower()
        
        # Determine current season
        current_season = 'moderate'
        if current_month in ['november', 'december', 'january', 'february']:
            current_season = 'peak'
        elif current_month in ['june', 'july', 'august', 'september', 'october']:
            current_season = 'low'
        
        return {
            'current_season': current_season,
            'season_description': business_calendar.get(f'{current_season}_season', ''),
            'business_implications': self._get_seasonal_implications(current_season),
            'upcoming_holidays': self._get_upcoming_holidays(),
            'tax_deadlines': self._get_upcoming_tax_deadlines()
        }
    
    def _get_seasonal_implications(self, season: str) -> List[str]:
        """Get business implications for current season"""
        implications = {
            'peak': [
                'High consumer spending period',
                'Optimal time for marketing campaigns',
                'Increased tourism and hospitality demand',
                'Higher inventory requirements'
            ],
            'moderate': [
                'Steady business activity',
                'Good time for planning and development',
                'Moderate marketing activities',
                'Regular inventory levels'
            ],
            'low': [
                'Reduced consumer spending',
                'Focus on cost management',
                'Good time for maintenance and upgrades',
                'Lower inventory requirements'
            ]
        }
        
        return implications.get(season, [])
    
    def _get_upcoming_holidays(self) -> List[str]:
        """Get upcoming major holidays affecting business"""
        # This would be enhanced with dynamic calendar integration
        major_holidays = self.static_resources.get('important_dates', {}).get('business_calendar', {}).get('major_holidays', [])
        return major_holidays
    
    def _get_upcoming_tax_deadlines(self) -> List[Dict[str, str]]:
        """Get upcoming tax deadlines"""
        tax_deadlines = self.static_resources.get('important_dates', {}).get('tax_deadlines', {})
        
        deadlines = []
        for tax_type, deadline in tax_deadlines.items():
            deadlines.append({
                'tax_type': tax_type.replace('_', ' ').title(),
                'deadline': deadline,
                'description': f'{tax_type.replace("_", " ").title()} filing deadline'
            })
        
        return deadlines
    
    def search_resources(self, query: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for resources based on query"""
        if context is None:
            context = {}
        
        results = []
        
        # Extract industry and stage from context
        industry = context.get('industry', 'services')
        business_stage = context.get('business_stage', 'growth')
        region = context.get('region', 'central')
        
        # Get comprehensive resources
        resources = self.get_relevant_resources(industry, business_stage, region)
        
        # Filter based on query relevance (simple keyword matching)
        query_lower = query.lower()
        
        # Search in government support
        for support in resources.get('government_support', []):
            if any(keyword in query_lower for keyword in ['government', 'support', 'osmep', 'agency']):
                results.append({
                    'type': 'Government Support',
                    'title': support.get('name', ''),
                    'description': support.get('relevance', ''),
                    'website': support.get('website', ''),
                    'services': support.get('services', [])
                })
        
        # Search in funding options
        for funding in resources.get('funding_options', []):
            if any(keyword in query_lower for keyword in ['loan', 'funding', 'money', 'capital', 'finance']):
                results.append({
                    'type': 'Funding',
                    'title': funding.get('name', ''),
                    'description': funding.get('relevance', ''),
                    'details': {
                        'max_amount': funding.get('max_amount'),
                        'requirements': funding.get('requirements', [])
                    }
                })
        
        # Search in training programs
        for training in resources.get('training_programs', []):
            if any(keyword in query_lower for keyword in ['training', 'skill', 'course', 'education', 'learn']):
                results.append({
                    'type': 'Training',
                    'title': training.get('program', ''),
                    'provider': training.get('provider', ''),
                    'description': training.get('relevance', '')
                })
        
        return results[:10]  # Limit results
    
    def get_quick_reference(self, industry: str) -> Dict[str, Any]:
        """Get quick reference guide for specific industry"""
        return {
            'key_agencies': self._get_key_agencies_for_industry(industry),
            'essential_licenses': self._get_essential_licenses(industry),
            'funding_sources': self._get_top_funding_sources(industry),
            'important_deadlines': self._get_important_deadlines(),
            'emergency_contacts': self._get_emergency_business_contacts()
        }
    
    def _get_key_agencies_for_industry(self, industry: str) -> List[Dict[str, str]]:
        """Get key government agencies for specific industry"""
        key_agencies = [
            {'name': 'OSMEP', 'website': 'https://www.sme.go.th', 'purpose': 'SME development'}
        ]
        
        if industry == 'manufacturing':
            key_agencies.append({'name': 'BOI', 'website': 'https://www.boi.go.th', 'purpose': 'Investment promotion'})
        elif industry == 'agriculture':
            key_agencies.append({'name': 'BAAC', 'website': 'https://www.baac.or.th', 'purpose': 'Agricultural financing'})
        elif industry == 'technology':
            key_agencies.append({'name': 'DEPA', 'website': 'https://www.depa.or.th', 'purpose': 'Digital economy'})
        
        return key_agencies
    
    def _get_essential_licenses(self, industry: str) -> List[str]:
        """Get essential licenses for industry"""
        licensing = self.static_resources.get('legal_compliance', {}).get('licensing_requirements', {})
        return licensing.get(industry, ['Business license', 'Tax registration'])
    
    def _get_top_funding_sources(self, industry: str) -> List[str]:
        """Get top funding sources for industry"""
        if industry == 'agriculture':
            return ['BAAC loans', 'Agricultural cooperatives', 'OSMEP funding']
        elif industry == 'technology':
            return ['Startup grants', 'VC funding', 'DEPA support programs']
        else:
            return ['SME Bank loans', 'OSMEP soft loans', 'Commercial bank SME loans']
    
    def _get_important_deadlines(self) -> List[str]:
        """Get important business deadlines"""
        return [
            'Corporate tax: May 31',
            'VAT filing: 15th of each month',
            'Social security: 15th of each month',
            'Annual report: May 31'
        ]
    
    def _get_emergency_business_contacts(self) -> List[Dict[str, str]]:
        """Get emergency business contacts"""
        return [
            {'service': 'OSMEP Hotline', 'phone': '0-2142-2800'},
            {'service': 'SME One Center', 'phone': '1357'},
            {'service': 'Business Registration', 'phone': '1570'},
            {'service': 'Tax Assistance', 'phone': '1161'}
        ]

# Global instance for easy import
government_resource_service = GovernmentResourceService()