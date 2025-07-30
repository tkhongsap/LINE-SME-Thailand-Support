import os
from config import Config

def validate_file_upload(content, filename):
    """Validate uploaded file size and type"""
    # Check file size
    if len(content) > Config.MAX_FILE_SIZE:
        return False, 'file_too_large'
    
    # Check file extension
    if not filename:
        return False, 'unsupported_file'
    
    file_ext = os.path.splitext(filename.lower())[1]
    
    # Check if extension is allowed
    all_extensions = []
    for ext_list in Config.ALLOWED_FILE_EXTENSIONS.values():
        all_extensions.extend(ext_list)
    
    if file_ext not in all_extensions:
        return False, 'unsupported_file'
    
    return True, None

def detect_language(text):
    """Simple language detection based on common words/characters"""
    if not text:
        return Config.DEFAULT_LANGUAGE
    
    # Japanese detection (hiragana, katakana, kanji)
    if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9faf' for c in text):
        return 'ja'
    
    # Korean detection (hangul)
    if any('\uac00' <= c <= '\ud7af' for c in text):
        return 'ko'
    
    # Chinese detection (simplified/traditional chinese characters)
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return 'zh'
    
    # Default to English for now (could be enhanced with proper language detection library)
    return 'en'

def get_file_category(filename):
    """Determine file category based on extension"""
    if not filename:
        return 'unknown'
    
    file_ext = os.path.splitext(filename.lower())[1]
    
    for category, extensions in Config.ALLOWED_FILE_EXTENSIONS.items():
        if file_ext in extensions:
            return category
    
    return 'unknown'
