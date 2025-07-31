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
        'simple': os.environ.get('SIMPLE_MODEL', 'gpt-4.1-nano'),
        'complex': os.environ.get('COMPLEX_MODEL', 'gpt-4.1-nano'),
        'vision': os.environ.get('VISION_MODEL', 'gpt-4.1-nano')
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
    
    # Thai SME Intelligence Configuration
    SME_INTELLIGENCE_ENABLED = os.environ.get('SME_INTELLIGENCE_ENABLED', 'true').lower() == 'true'
    CULTURAL_CONTEXT_ENABLED = os.environ.get('CULTURAL_CONTEXT_ENABLED', 'true').lower() == 'true'
    INDUSTRY_INTELLIGENCE_ENABLED = os.environ.get('INDUSTRY_INTELLIGENCE_ENABLED', 'true').lower() == 'true'
    USER_PROFILE_TIMEOUT = int(os.environ.get('USER_PROFILE_TIMEOUT', '3600'))  # 1 hour
    
    # Thai Business Context
    THAI_BUSINESS_SEASONS = {
        'peak': ['november', 'december', 'january', 'february'],  # Cool season
        'moderate': ['march', 'april', 'may'],  # Summer
        'low': ['june', 'july', 'august', 'september', 'october']  # Rainy season
    }
    
    # Cultural Intelligence Settings
    DEFAULT_FORMALITY_LEVEL = os.environ.get('DEFAULT_FORMALITY_LEVEL', 'polite')
    ENABLE_REGIONAL_CONTEXT = os.environ.get('ENABLE_REGIONAL_CONTEXT', 'true').lower() == 'true'
    BUDDHIST_VALUES_INTEGRATION = os.environ.get('BUDDHIST_VALUES_INTEGRATION', 'true').lower() == 'true'
    
    # Industry Support Configuration
    SUPPORTED_INDUSTRIES = [
        'retail', 'food', 'manufacturing', 'agriculture', 
        'services', 'technology', 'tourism', 'logistics'
    ]
    
    # Thai Government Resource Integration
    OSMEP_API_ENABLED = os.environ.get('OSMEP_API_ENABLED', 'false').lower() == 'true'
    SME_ONE_INTEGRATION = os.environ.get('SME_ONE_INTEGRATION', 'false').lower() == 'true'
    GOVERNMENT_RESOURCE_CACHE_TTL = int(os.environ.get('GOVERNMENT_RESOURCE_CACHE_TTL', '86400'))  # 24 hours
    
    # Performance Monitoring Configuration
    MONITORING_ENABLED = os.environ.get('MONITORING_ENABLED', 'true').lower() == 'true'
    METRICS_COLLECTION_ENABLED = os.environ.get('METRICS_COLLECTION_ENABLED', 'true').lower() == 'true'
    ALERTING_ENABLED = os.environ.get('ALERTING_ENABLED', 'true').lower() == 'true'
    
    # Alert Configuration
    ALERT_COOLDOWN_MINUTES = int(os.environ.get('ALERT_COOLDOWN_MINUTES', '30'))
    EMAIL_ALERTS_ENABLED = os.environ.get('EMAIL_ALERTS_ENABLED', 'false').lower() == 'true'
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    ALERT_EMAIL_TO = os.environ.get('ALERT_EMAIL_TO', '').split(',')
    
    # Performance Thresholds
    RESPONSE_TIME_WARNING_MS = int(os.environ.get('RESPONSE_TIME_WARNING_MS', '3000'))
    RESPONSE_TIME_CRITICAL_MS = int(os.environ.get('RESPONSE_TIME_CRITICAL_MS', '5000'))
    ERROR_RATE_WARNING_PERCENT = float(os.environ.get('ERROR_RATE_WARNING_PERCENT', '10.0'))
    ERROR_RATE_CRITICAL_PERCENT = float(os.environ.get('ERROR_RATE_CRITICAL_PERCENT', '25.0'))
    COST_WARNING_PER_HOUR = float(os.environ.get('COST_WARNING_PER_HOUR', '5.0'))
    CULTURAL_SCORE_WARNING = float(os.environ.get('CULTURAL_SCORE_WARNING', '0.6'))
    
    # Monitoring Intervals (seconds)
    METRICS_COLLECTION_INTERVAL = int(os.environ.get('METRICS_COLLECTION_INTERVAL', '60'))
    ALERT_CHECK_INTERVAL = int(os.environ.get('ALERT_CHECK_INTERVAL', '30'))
    TREND_ANALYSIS_INTERVAL = int(os.environ.get('TREND_ANALYSIS_INTERVAL', '300'))
    ANOMALY_DETECTION_INTERVAL = int(os.environ.get('ANOMALY_DETECTION_INTERVAL', '120'))
    
    # SLA Configuration
    SLA_RESPONSE_TIME_MS = int(os.environ.get('SLA_RESPONSE_TIME_MS', '2000'))
    SLA_UPTIME_PERCENT = float(os.environ.get('SLA_UPTIME_PERCENT', '99.9'))
    SLA_ERROR_RATE_MAX = float(os.environ.get('SLA_ERROR_RATE_MAX', '1.0'))
    SLA_CULTURAL_SCORE_MIN = float(os.environ.get('SLA_CULTURAL_SCORE_MIN', '0.8'))
    


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
