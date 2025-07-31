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
    SUPPORTED_LANGUAGES = ['th', 'en', 'ja', 'ko', 'zh', 'es', 'fr', 'de', 'it', 'pt', 'ru']
    DEFAULT_LANGUAGE = 'th'
    
    # AI Optimization Configuration
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '60'))
    ENABLE_AI_CACHING = os.environ.get('ENABLE_AI_CACHING', 'true').lower() == 'true'
    CACHE_TTL_HOURS = int(os.environ.get('CACHE_TTL_HOURS', '24'))
    MAX_CACHE_SIZE = int(os.environ.get('MAX_CACHE_SIZE', '1000'))
    
    # Cost Management
    DAILY_COST_LIMIT = float(os.environ.get('DAILY_COST_LIMIT', '10.0'))
    TOKEN_BUDGET_PER_USER = int(os.environ.get('TOKEN_BUDGET_PER_USER', '5000'))
    ENABLE_COST_OPTIMIZATION = os.environ.get('ENABLE_COST_OPTIMIZATION', 'true').lower() == 'true'
    
    # Model Configuration
    PREFERRED_MODELS = {
        'simple': os.environ.get('SIMPLE_MODEL', 'gpt-35-turbo'),
        'complex': os.environ.get('COMPLEX_MODEL', 'gpt-4'),
        'vision': os.environ.get('VISION_MODEL', 'gpt-4')
    }
    
    # Response Optimization
    ENABLE_STREAMING = os.environ.get('ENABLE_STREAMING', 'false').lower() == 'true'
    CONTEXT_COMPRESSION_THRESHOLD = int(os.environ.get('CONTEXT_COMPRESSION_THRESHOLD', '3000'))
    MAX_RESPONSE_TOKENS = int(os.environ.get('MAX_RESPONSE_TOKENS', '1000'))
    
    # Performance Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    WEBHOOK_TIMEOUT = 25  # seconds (LINE timeout is 30s)
    REPLY_TOKEN_EXPIRY = 30  # seconds
    MAX_MESSAGES_PER_REPLY = 5  # LINE API limit
    
    # Connection Pool Configuration
    CONNECTION_POOL_SIZE = 10
    CONNECTION_MAX_RETRIES = 3
    CONNECTION_TIMEOUT = 10  # seconds
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_USER = 60  # messages per minute
    RATE_LIMIT_WINDOW = 60  # seconds
    API_RATE_LIMIT = 1000  # LINE API calls per minute
    
    # Cache Configuration
    CACHE_TTL = 300  # 5 minutes
    SIGNATURE_CACHE_TTL = 60  # 1 minute
    FLEX_MESSAGE_CACHE_TTL = 3600  # 1 hour
    


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
