#!/usr/bin/env python3
from services.line_service_optimized import OptimizedLineService
from services.openai_service import OpenAIService
from config import Config

print("=== Service Configuration Check ===")
print(f"LINE Channel Secret configured: {bool(Config.LINE_CHANNEL_SECRET)}")
print(f"LINE Access Token configured: {bool(Config.LINE_CHANNEL_ACCESS_TOKEN)}")
print(f"Azure OpenAI configured: {bool(Config.AZURE_OPENAI_API_KEY)}")

# Test LINE service
line_service = OptimizedLineService()
print(f"\nLINE Service initialized: {line_service.config_valid}")
print(f"LINE Bot API available: {line_service.line_bot_api is not None}")

# Test OpenAI service
openai_service = OpenAIService()
print(f"\nOpenAI Service initialized: {openai_service.config_valid}")
print(f"OpenAI Client available: {openai_service.client is not None}")

# Test a simple dev response
if not openai_service.config_valid:
    response = openai_service._get_dev_response("สวัสดี", 'text')
    print(f"\nDev response: {response}")