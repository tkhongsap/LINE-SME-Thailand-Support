# SME Prompts System

This module contains the centralized prompt management system for the Thai SME Support LINE OA chatbot.

## Overview

The `SMEPrompts` class provides Thai-first, multi-language prompts specifically designed for supporting Thai SMEs (Small and Medium Enterprises) in areas like:

- Financial literacy and funding access
- Digital marketing and social media
- Online presence and e-commerce
- Business operations and HR
- Legal compliance and regulations

## Features

### 1. Multi-Language Support
- **Primary**: Thai (`th`) - Default language for Thai SME context
- **Secondary**: English (`en`) - Fallback for international users
- **Additional**: Japanese (`ja`), Korean (`ko`) for regional support

### 2. Context-Aware Prompts
- **Conversation**: General business advisory chat
- **Image Analysis**: Business document and product image analysis
- **File Analysis**: Business document processing

### 3. Auto Language Detection
- Detects Thai characters (Unicode: `\u0e00-\u0e7f`)
- Detects Japanese characters (Hiragana, Katakana, Kanji)
- Detects Korean characters (Hangul)
- Falls back to English for other scripts

### 4. User Context Integration
- Business type (e.g., restaurant, retail, manufacturing)
- Location (Bangkok, provinces)
- Business stage (startup, growth, established)
- Number of employees

## Usage

### Basic Usage

```python
from prompts.sme_prompts import SMEPrompts

# Get system prompt for Thai conversation
prompt = SMEPrompts.get_system_prompt('th', 'conversation')

# Auto-detect language from user message
language = SMEPrompts.detect_language_from_message("สวัสดีครับ")
# Returns: 'th'

# Get error messages
errors = SMEPrompts.get_error_messages()
error_msg = errors['th']['processing_error']
```

### With User Context

```python
user_context = {
    'business_type': 'ร้านอาหาร',
    'location': 'กรุงเทพฯ',
    'stage': 'เริ่มต้น',
    'employees': 5
}

prompt = SMEPrompts.get_system_prompt('th', 'conversation', user_context)
```

## Prompt Design Principles

### Thai SME Context
- Uses Thai government resources (OSMEP, SME One) as references
- Understands Thai regulations (PDPA, tax laws, licensing)
- Provides culturally appropriate business advice
- Uses colloquial, friendly Thai language

### Practical Focus
- Actionable advice over theoretical concepts
- Step-by-step guidance
- Local resource recommendations
- Real-world Thai business examples

### Multi-Channel Integration
- Optimized for LINE messaging platform
- Supports rich media responses
- Compatible with chatbot limitations
- Designed for mobile-first interactions

## Error Messages

Comprehensive error handling in all supported languages:

- `openai_error`: AI service issues
- `invalid_image`: Image processing problems
- `processing_error`: General processing errors
- `unsupported_file`: File type not supported
- `file_too_large`: File size exceeds limits

## Development Mode

When Azure OpenAI is not configured, the system provides development-friendly responses in the user's detected language, maintaining the user experience while indicating the development state.

## File Structure

```
prompts/
├── sme_prompts.py    # Main prompts class
└── README.md         # This documentation
```

## Integration

The prompts system integrates with:

- `services/openai_service.py` - AI response generation
- `routes/webhook.py` - LINE webhook handling
- `config.py` - Application configuration

## Extending

To add new languages:

1. Add language detection logic in `detect_language_from_message()`
2. Add prompts in the language dictionaries
3. Add error messages and dev responses
4. Update `config.py` SUPPORTED_LANGUAGES if needed

To add new context types:

1. Add new context type to prompt dictionaries
2. Update the context_type parameter documentation
3. Test with all supported languages

## Thai SME Resources Referenced

- OSMEP (Office of Small and Medium Enterprises Promotion)
- SME One information portal
- Department of Business Development (DBD)
- Personal Data Protection Act (PDPA)
- Thai e-commerce regulations
- LINE for Business guidelines