"""
SME-focused prompts for Thai SME Support LINE OA chatbot
Uses unified multilingual approach - AI responds in user's language naturally
"""

class SMEPrompts:
    """Advanced prompts specifically designed for Thai SME support chatbot"""
    
    # Industry-specific prompt variations
    INDUSTRY_CONTEXTS = {
        'retail': "retail/e-commerce operations, inventory management, customer service",
        'manufacturing': "production processes, supply chain, quality control, export",
        'food': "food service, hygiene standards, food safety regulations, restaurant operations",
        'agriculture': "farming, agricultural products, export markets, sustainable practices",
        'services': "service delivery, client management, professional services",
        'technology': "digital solutions, software development, tech startups"
    }
    
    # Business stage contexts
    STAGE_CONTEXTS = {
        'startup': "business planning, initial setup, legal registration, funding",
        'growth': "scaling operations, market expansion, team building, investment",
        'established': "optimization, new markets, digital transformation, sustainability",
        'pivot': "business model changes, market repositioning, restructuring"
    }
    
    @staticmethod
    def get_system_prompt(language=None, context_type='conversation', user_context=None):
        """
        Get system prompt based on context type
        The AI will naturally respond in the user's language
        
        Args:
            language (str): Deprecated - kept for backward compatibility
            context_type (str): Type of interaction (conversation, image_analysis, file_analysis)
            user_context (dict): Additional context about the user/SME
        """
        # Enhanced conversation prompt with dynamic context injection
        conversation_base = """Thai SME business advisor specializing in Thai market context. Respond naturally in user's language.

Thai Cultural Guidelines:
• Use appropriate Thai politeness levels (กรุณา, ครับ/ค่ะ, นะครับ/นะคะ)
• Respect business hierarchy and relationship-building (การสร้างความสัมพันธ์)
• Consider Buddhist values in business ethics
• Acknowledge family business dynamics common in Thai SME

Expertise: {expertise_areas}
Business Context: {business_context}
Current Focus: {current_focus}

Core SME Areas:
• Financial: SME Bank loans, OSMEP funding, cash flow, Thai accounting standards
• Digital: LINE OA setup, Thai social commerce, Lazada/Shopee integration
• Operations: Thai labor law, inventory for Thai market, regulatory compliance
• Legal: PDPA compliance, VAT registration, BOI benefits, export licensing
• Government: OSMEP programs, SME One portal, DBD registration

Thai Market Expertise:
• Bangkok vs provincial market differences
• Thai consumer behavior and preferences
• Regulatory environment (SEC, BOT, Ministry of Commerce)
• Cultural considerations for marketing and operations

Communication Style: 
• Warm, respectful, and supportive (เป็นกันเอง but professional)
• Provide step-by-step guidance with Thai examples
• Reference Thai success stories and local case studies
• Ask culturally appropriate clarifying questions
• Use colloquial Thai when appropriate, formal when discussing regulations"""

        prompts = {
            'conversation': conversation_base,

            'image_analysis': """Thai SME image analyst. Language: {language}

Analyze for: {analysis_focus}
Business type: {business_type}

Focus areas:
• Products: Visual appeal, marketability, photography tips
• Documents: Key info, action items, compliance issues  
• Marketing: Design effectiveness, Thai market fit
• Operations: Layout, customer appeal, improvements

Provide: Specific, actionable feedback within SME resources.""",

            'file_analysis': """Thai SME document analyst. Language: {language}

File type: {file_type}
Analysis focus: {analysis_focus}

Key areas:
• Financial: Metrics, trends, opportunities, SME resources
• Business plans: Completeness, Thai market fit, feasibility
• Marketing: Thai consumer appeal, optimization strategies
• Legal: Compliance, obligations, regulatory requirements
• Data: Key insights, actionable findings, leverage opportunities

Output: Clear summary, specific recommendations, next steps."""
        }
        
        base_prompt = prompts.get(context_type, prompts['conversation'])
        
        # Inject dynamic context variables
        if user_context:
            prompt_variables = SMEPrompts._prepare_prompt_variables(user_context, context_type)
            try:
                base_prompt = base_prompt.format(**prompt_variables)
            except KeyError as e:
                # Fallback if variable missing
                base_prompt = prompts['conversation'].format(**prompt_variables)
        
        return base_prompt
    
    @staticmethod
    def _prepare_prompt_variables(user_context, context_type):
        """Prepare variables for dynamic prompt injection"""
        variables = {
            'language': user_context.get('language', 'th'),
            'business_type': user_context.get('business_type', 'SME'),
            'expertise_areas': 'Thai SME advisory',
            'business_context': 'Thai market',
            'current_focus': 'practical business guidance',
            'analysis_focus': 'business optimization',
            'file_type': user_context.get('file_type', 'document')
        }
        
        # Industry-specific enhancements
        business_type = user_context.get('business_type', '').lower()
        for industry, context in SMEPrompts.INDUSTRY_CONTEXTS.items():
            if industry in business_type:
                variables['expertise_areas'] = f"Thai SME advisory specializing in {context}"
                variables['current_focus'] = context
                break
        
        # Stage-specific enhancements  
        stage = user_context.get('stage', '').lower()
        for stage_key, context in SMEPrompts.STAGE_CONTEXTS.items():
            if stage_key in stage:
                variables['current_focus'] = f"{variables['current_focus']}, focusing on {context}"
                break
        
        # Context-specific adjustments
        if context_type == 'image_analysis':
            variables['analysis_focus'] = user_context.get('analysis_focus', 'business relevance and actionable insights')
        elif context_type == 'file_analysis':
            variables['analysis_focus'] = user_context.get('analysis_focus', 'key insights and recommendations')
        
        # Location context
        location = user_context.get('location', '')
        if location and location.lower() != 'thailand':
            variables['business_context'] = f"Thai market with {location} considerations"
        
        return variables
    
    @staticmethod
    def _get_context_addition(user_context):
        """Legacy method for backward compatibility"""
        if not user_context:
            return ""
        return f"Context: {user_context.get('business_type', 'SME')}, {user_context.get('location', 'Thailand')}"
    
    @staticmethod
    def get_error_messages():
        """Get error messages - simplified approach using AI's natural language ability"""
        return {
            'openai_error': 'เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง / An error occurred while processing. Please try again.',
            'invalid_image': 'ไม่สามารถวิเคราะห์รูปภาพได้ กรุณาส่งรูปภาพที่ชัดเจน / Unable to analyze the image. Please send a clear image.',
            'processing_error': 'เกิดข้อผิดพลาดในการประมวลผลไฟล์ กรุณาลองใหม่ / An error occurred while processing the file. Please try again.',
            'unsupported_file': 'ประเภทไฟล์นี้ไม่รองรับ กรุณาส่งไฟล์ประเภทอื่น / This file type is not supported. Please send a different file type.',
            'file_too_large': 'ไฟล์มีขนาดเกิน 20MB กรุณาส่งไฟล์ที่เล็กกว่า / File size exceeds 20MB limit. Please upload a smaller file.'
        }
    
    @staticmethod
    def get_dev_responses():
        """Get development mode responses - bilingual for broad accessibility"""
        return {
            'text': "นี่คือการตอบกลับในโหมดพัฒนาสำหรับ: '{user_message}' หากต้องการเปิดใช้งาน AI กรุณาตั้งค่า Azure OpenAI credentials / This is a development mode response to: '{user_message}'. To enable AI responses, please configure your Azure OpenAI credentials.",
            'image': "ได้รับรูปภาพแล้ว แต่ระบบทำงานในโหมดพัฒนา กรุณาตั้งค่า Azure OpenAI เพื่อใช้งานการวิเคราะห์รูปภาพ / I received your image, but I'm running in development mode. Configure Azure OpenAI credentials to enable image analysis.",
            'file': "ได้รับไฟล์แล้ว แต่ระบบทำงานในโหมดพัฒนา กรุณาตั้งค่า Azure OpenAI เพื่อใช้งานการประมวลผลไฟล์ / I received your file, but I'm running in development mode. Configure Azure OpenAI credentials to enable file processing."
        }