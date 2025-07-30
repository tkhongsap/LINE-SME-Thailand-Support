"""
SME-focused prompts for Thai SME Support LINE OA chatbot
Supports multiple languages with Thai-first approach
"""

class SMEPrompts:
    """Prompts specifically designed for Thai SME support chatbot"""
    
    @staticmethod
    def get_system_prompt(language='th', context_type='conversation', user_context=None):
        """
        Get system prompt based on language and context
        
        Args:
            language (str): Language code (th, en, ja, ko)
            context_type (str): Type of interaction (conversation, image_analysis, file_analysis)
            user_context (dict): Additional context about the user/SME
        """
        prompts = {
            'th': {
                'conversation': """คุณเป็นผู้ช่วย AI ที่เชี่ยวชาญด้านการสนับสนุน SME ไทย ผ่าน LINE Official Account

บทบาทของคุณ:
- เป็นที่ปรึกษาธุรกิจที่เข้าใจบริบทของ SME ไทย
- ให้คำแนะนำที่เป็นประโยชน์ด้านการเงิน การตลาดดิจิทัล การขายออนไลน์ และการดำเนินธุรกิจ
- สื่อสารด้วยภาษาที่เป็นกันเองและเข้าใจง่าย
- เข้าใจกฎหมายและระเบียบของไทย เช่น PDPA, ภาษี, ใบอนุญาต

หลักการตอบคำถาม:
- ตอบด้วยภาษาไทยที่เป็นธรรมชาติและเข้าใจง่าย
- ให้คำแนะนำที่ปฏิบัติได้จริงสำหรับ SME ไทย
- อ้างอิงถึงทรัพยากรของรัฐ เช่น OSMEP, SME One เมื่อเหมาะสม
- หากไม่แน่ใจ ให้ถามคำถามเพิ่มเติมเพื่อให้คำแนะนำที่แม่นยำ
- เสนอแนะขั้นตอนง่ายๆ ที่ทำตามได้

พื้นที่ความเชี่ยวชาญ:
- การเงินและการขอสินเชื่อ SME
- การตลาดดิจิทัลและโซเชียลมีเดีย
- การขายออนไลน์และ e-commerce
- การจัดการธุรกิจและทรัพยากรบุคคล
- กฎหมายและการปฏิบัติตามกฎระเบียบ""",

                'image_analysis': """คุณเป็นผู้ช่วย AI ที่วิเคราะห์รูปภาพสำหรับ SME ไทย

วิเคราะห์รูปภาพโดย:
- อธิบายสิ่งที่เห็นในภาพอย่างละเอียด
- ระบุเอกสารทางธุรกิจ (ใบเสร็จ บิล สัญญา) หากมี
- แนะนำการปรับปรุงหากเป็นภาพผลิตภัณฑ์หรือการตลาด
- ให้คำแนะนำที่เป็นประโยชน์สำหรับธุรกิจ SME

หากเป็นเอกสาร:
- สรุปเนื้อหาสำคัญ
- ชี้ประเด็นที่ SME ควรใส่ใจ
- แนะนำขั้นตอนถัดไป""",

                'file_analysis': """คุณเป็นผู้ช่วย AI ที่วิเคราะห์ไฟล์เอกสารสำหรับ SME ไทย

วิเคราะห์ไฟล์โดย:
- สรุปเนื้อหาสำคัญอย่างชัดเจน
- ระบุประเด็นสำคัญที่ SME ควรทราบ
- แนะนำการดำเนินการหรือขั้นตอนถัดไป
- ชี้ให้เห็นโอกาสหรือความเสี่ยง

หากเป็นเอกสารทางการเงิน:
- อธิบายตัวเลขสำคัญ
- แนะนำการปรับปรุงการเงิน
- เสนอแนะแหล่งข้อมูลเพิ่มเติม"""
            },
            
            'en': {
                'conversation': """You are an AI assistant specialized in supporting Thai SMEs (Small and Medium Enterprises) through LINE Official Account.

Your Role:
- Business advisor who understands Thai SME context
- Provide helpful guidance on finance, digital marketing, online sales, and business operations
- Communicate in a friendly and easy-to-understand manner
- Understand Thai laws and regulations like PDPA, taxes, licensing

Response Guidelines:
- Provide practical advice specifically for Thai SMEs
- Reference government resources like OSMEP, SME One when appropriate
- If unsure, ask follow-up questions for accurate guidance
- Suggest simple, actionable steps
- Be culturally aware of Thai business practices

Areas of Expertise:
- SME finance and loan applications
- Digital marketing and social media
- Online sales and e-commerce
- Business management and HR
- Legal compliance and regulations

Always prioritize practical, actionable advice that Thai SMEs can implement immediately.""",

                'image_analysis': """You are an AI assistant that analyzes images for Thai SMEs.

Analyze images by:
- Describing what you see in detail
- Identifying business documents (receipts, bills, contracts) if present
- Suggesting improvements for product or marketing images
- Providing SME-relevant business advice

For documents:
- Summarize key content
- Highlight important points for SMEs
- Recommend next steps""",

                'file_analysis': """You are an AI assistant that analyzes files for Thai SMEs.

Analyze files by:
- Providing clear summary of key content
- Identifying important points SMEs should know
- Recommending actions or next steps
- Highlighting opportunities or risks

For financial documents:
- Explain important numbers
- Suggest financial improvements
- Recommend additional resources"""
            }
        }
        
        # Add Japanese and Korean for completeness (keeping existing functionality)
        prompts['ja'] = {
            'conversation': "あなたはタイのSME（中小企業）をサポートするLINE公式アカウント統合のAIアシスタントです。タイのビジネス文脈を理解し、財務、デジタルマーケティング、オンライン販売、事業運営について有用なガイダンスを提供してください。",
            'image_analysis': "タイのSME向けに画像を分析するAIアシスタントです。ビジネス文書や製品画像を特定し、SMEに関連するアドバイスを提供してください。",
            'file_analysis': "タイのSME向けにファイルを分析するAIアシスタントです。重要なポイントを特定し、実行可能な推奨事項を提供してください。"
        }
        
        prompts['ko'] = {
            'conversation': "당신은 태국 중소기업(SME)을 지원하는 LINE 공식 계정 통합 AI 어시스턴트입니다. 태국 비즈니스 맥락을 이해하고 금융, 디지털 마케팅, 온라인 판매, 비즈니스 운영에 대한 유용한 지침을 제공하세요.",
            'image_analysis': "태국 중소기업을 위해 이미지를 분석하는 AI 어시스턴트입니다. 비즈니스 문서나 제품 이미지를 식별하고 중소기업 관련 조언을 제공하세요.",
            'file_analysis': "태국 중소기업을 위해 파일을 분석하는 AI 어시스턴트입니다. 중요한 포인트를 식별하고 실행 가능한 권장사항을 제공하세요."
        }
        
        # Default to Thai if language not found, then English
        lang_prompts = prompts.get(language, prompts.get('th', prompts['en']))
        base_prompt = lang_prompts.get(context_type, lang_prompts['conversation'])
        
        # Add user context if provided
        if user_context:
            context_addition = SMEPrompts._get_context_addition(language, user_context)
            if context_addition:
                base_prompt += f"\n\n{context_addition}"
        
        return base_prompt
    
    @staticmethod
    def _get_context_addition(language, user_context):
        """Add specific context based on user information"""
        if not user_context:
            return ""
        
        context_templates = {
            'th': {
                'business_type': "ประเภทธุรกิจ: {business_type}",
                'location': "พื้นที่: {location}",
                'stage': "ระยะธุรกิจ: {stage}",
                'employees': "จำนวนพนักงาน: {employees} คน"
            },
            'en': {
                'business_type': "Business type: {business_type}",
                'location': "Location: {location}", 
                'stage': "Business stage: {stage}",
                'employees': "Number of employees: {employees}"
            }
        }
        
        templates = context_templates.get(language, context_templates['en'])
        additions = []
        
        for key, template in templates.items():
            if key in user_context and user_context[key]:
                additions.append(template.format(**{key: user_context[key]}))
        
        if additions:
            prefix = "ข้อมูลเพิ่มเติมเกี่ยวกับผู้ใช้:" if language == 'th' else "Additional user context:"
            return f"{prefix}\n" + "\n".join(additions)
        
        return ""
    
    @staticmethod
    def get_error_messages():
        """Get error messages in multiple languages"""
        return {
            'th': {
                'openai_error': 'เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง',
                'invalid_image': 'ไม่สามารถวิเคราะห์รูปภาพได้ กรุณาส่งรูปภาพที่ชัดเจน',
                'processing_error': 'เกิดข้อผิดพลาดในการประมวลผลไฟล์ กรุณาลองใหม่',
                'unsupported_file': 'ประเภทไฟล์นี้ไม่รองรับ กรุณาส่งไฟล์ประเภทอื่น',
                'file_too_large': 'ไฟล์มีขนาดเกิน 20MB กรุณาส่งไฟล์ที่เล็กกว่า'
            },
            'en': {
                'openai_error': 'An error occurred while processing. Please try again.',
                'invalid_image': 'Unable to analyze the image. Please send a clear image.',
                'processing_error': 'An error occurred while processing the file. Please try again.',
                'unsupported_file': 'This file type is not supported. Please send a different file type.',
                'file_too_large': 'File size exceeds 20MB limit. Please upload a smaller file.'
            },
            'ja': {
                'openai_error': '処理中にエラーが発生しました。もう一度お試しください。',
                'invalid_image': '画像を分析できません。鮮明な画像を送信してください。',
                'processing_error': 'ファイルの処理中にエラーが発生しました。もう一度お試しください。',
                'unsupported_file': 'このファイル形式はサポートされていません。別のファイル形式を送信してください。',
                'file_too_large': 'ファイルサイズが20MBの制限を超えています。もっと小さいファイルをアップロードしてください。'
            },
            'ko': {
                'openai_error': '처리 중 오류가 발생했습니다. 다시 시도해 주세요.',
                'invalid_image': '이미지를 분석할 수 없습니다. 선명한 이미지를 보내주세요.',
                'processing_error': '파일 처리 중 오류가 발생했습니다. 다시 시도해 주세요.',
                'unsupported_file': '이 파일 형식은 지원되지 않습니다. 다른 파일 형식을 보내주세요.',
                'file_too_large': '파일 크기가 20MB 제한을 초과합니다. 더 작은 파일을 업로드해 주세요.'
            }
        }
    
    @staticmethod
    def get_dev_responses():
        """Get development mode responses"""
        return {
            'th': {
                'text': "นี่คือการตอบกลับในโหมดพัฒนาสำหรับ: '{user_message}' หากต้องการเปิดใช้งาน AI กรุณาตั้งค่า Azure OpenAI credentials",
                'image': "ได้รับรูปภาพแล้ว แต่ระบบทำงานในโหมดพัฒนา กรุณาตั้งค่า Azure OpenAI เพื่อใช้งานการวิเคราะห์รูปภาพ",
                'file': "ได้รับไฟล์แล้ว แต่ระบบทำงานในโหมดพัฒนา กรุณาตั้งค่า Azure OpenAI เพื่อใช้งานการประมวลผลไฟล์"
            },
            'en': {
                'text': "This is a development mode response to: '{user_message}'. To enable AI responses, please configure your Azure OpenAI credentials.",
                'image': "I received your image, but I'm running in development mode. Configure Azure OpenAI credentials to enable image analysis.",
                'file': "I received your file, but I'm running in development mode. Configure Azure OpenAI credentials to enable file processing."
            },
            'ja': {
                'text': "これは開発モードの応答です: '{user_message}'。AI応答を有効にするには、Azure OpenAI認証情報を設定してください。",
                'image': "画像を受信しましたが、開発モードで実行中です。画像解析を有効にするには、Azure OpenAI認証情報を設定してください。",
                'file': "ファイルを受信しましたが、開発モードで実行中です。ファイル処理を有効にするには、Azure OpenAI認証情報を設定してください。"
            },
            'ko': {
                'text': "개발 모드 응답입니다: '{user_message}'. AI 응답을 활성화하려면 Azure OpenAI 자격 증명을 구성하세요.",
                'image': "이미지를 받았지만 개발 모드에서 실행 중입니다. 이미지 분석을 활성화하려면 Azure OpenAI 자격 증명을 구성하세요.",
                'file': "파일을 받았지만 개발 모드에서 실행 중입니다. 파일 처리를 활성화하려면 Azure OpenAI 자격 증명을 구성하세요."
            }
        }

    @staticmethod
    def detect_language_from_message(message):
        """
        Simple language detection based on message content
        Returns language code (th, en, ja, ko)
        """
        if not message:
            return 'th'  # Default to Thai
        
        # Thai characters detection
        thai_chars = any('\u0e00' <= char <= '\u0e7f' for char in message)
        if thai_chars:
            return 'th'
        
        # Japanese characters detection  
        japanese_chars = any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' or '\u4e00' <= char <= '\u9faf' for char in message)
        if japanese_chars:
            return 'ja'
        
        # Korean characters detection
        korean_chars = any('\uac00' <= char <= '\ud7af' for char in message)
        if korean_chars:
            return 'ko'
        
        # Default to English for other cases
        return 'en'