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
    """Enhanced language detection with Thai language priority for SME context"""
    if not text:
        return Config.DEFAULT_LANGUAGE
    
    # Thai detection (Primary language for SME context)
    # Thai script range: U+0E00-U+0E7F
    if any('\u0e00' <= c <= '\u0e7f' for c in text):
        return 'th'
    
    # Enhanced Thai detection with common Thai words
    thai_keywords = ['ครับ', 'ค่ะ', 'กรุณา', 'ธุรกิจ', 'การตลาด', 'เงิน', 'ขาย', 'ซื้อ', 'ร้าน', 
                    'บริษัท', 'ลูกค้า', 'สินค้า', 'บริการ', 'แผน', 'กำไร', 'ต้นทุน', 'ราคา']
    if any(keyword in text for keyword in thai_keywords):
        return 'th'
    
    # Japanese detection (hiragana, katakana, kanji)
    if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9faf' for c in text):
        return 'ja'
    
    # Korean detection (hangul)
    if any('\uac00' <= c <= '\ud7af' for c in text):
        return 'ko'
    
    # Chinese detection (simplified/traditional chinese characters)
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return 'zh'
    
    # English business keywords for international SMEs in Thailand
    english_business_keywords = ['business', 'marketing', 'sale', 'product', 'customer', 'profit', 'revenue']
    if any(keyword.lower() in text.lower() for keyword in english_business_keywords):
        return 'en'
    
    # Default to Thai for SME context (most users expected to be Thai)
    return Config.DEFAULT_LANGUAGE

def get_file_category(filename):
    """Determine file category based on extension"""
    if not filename:
        return 'unknown'
    
    file_ext = os.path.splitext(filename.lower())[1]
    
    for category, extensions in Config.ALLOWED_FILE_EXTENSIONS.items():
        if file_ext in extensions:
            return category
    
    return 'unknown'
