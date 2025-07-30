import os

class Config:
    # LINE Bot Configuration
    LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
    AZURE_OPENAI_API_VERSION = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-01')
    
    # File Upload Configuration
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    ALLOWED_FILE_EXTENSIONS = {
        'documents': ['.pdf', '.docx', '.doc', '.txt', '.md'],
        'spreadsheets': ['.xlsx', '.xls', '.csv'],
        'presentations': ['.pptx', '.ppt'],
        'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.rs'],
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    }
    
    # Conversation Configuration
    MAX_CONVERSATION_HISTORY = 10
    SUPPORTED_LANGUAGES = ['en', 'ja', 'ko', 'zh', 'es', 'fr', 'de', 'it', 'pt', 'ru']
    DEFAULT_LANGUAGE = 'en'
    
    # Error Messages
    ERROR_MESSAGES = {
        'en': {
            'file_too_large': 'File size exceeds 20MB limit. Please upload a smaller file.',
            'unsupported_file': 'File type not supported. Supported types: PDF, DOCX, XLSX, PPTX, code files, and images.',
            'processing_error': 'Sorry, there was an error processing your request. Please try again.',
            'openai_error': 'AI service temporarily unavailable. Please try again later.',
            'invalid_image': 'Unable to process this image. Please try a different image format.',
        },
        'ja': {
            'file_too_large': 'ファイルサイズが20MBの制限を超えています。もっと小さいファイルをアップロードしてください。',
            'unsupported_file': 'ファイル形式がサポートされていません。対応形式：PDF、DOCX、XLSX、PPTX、コードファイル、画像。',
            'processing_error': '申し訳ございません。リクエストの処理中にエラーが発生しました。もう一度お試しください。',
            'openai_error': 'AIサービスが一時的に利用できません。後でもう一度お試しください。',
            'invalid_image': 'この画像を処理できません。別の画像形式をお試しください。',
        }
    }

    @classmethod
    def validate_config(cls):
        """Validate that all required environment variables are set"""
        required_vars = [
            'LINE_CHANNEL_ACCESS_TOKEN',
            'LINE_CHANNEL_SECRET',
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_ENDPOINT'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            # In development mode, just log a warning instead of failing
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}. Some features may not work.")
            return False
        
        return True
