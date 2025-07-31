import os
import magic
import hashlib
import mimetypes
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path
import zipfile
import io
import logging

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ValidationResult:
    """Enhanced validation result with detailed information"""
    is_valid: bool
    error_code: Optional[str]
    file_type: Optional[str]
    mime_type: Optional[str]
    file_size: int
    detected_encoding: Optional[str]
    security_issues: List[str]
    metadata: Dict[str, any]

class EnhancedFileValidator:
    """
    Advanced file validation with security checks, corruption detection,
    and Thai language support
    """
    
    def __init__(self):
        # File type signatures (magic numbers)
        self.file_signatures = {
            # PDF
            'pdf': [b'%PDF-1.', b'%PDF-2.'],
            
            # Microsoft Office (ZIP-based)
            'docx': [b'PK\x03\x04'],
            'xlsx': [b'PK\x03\x04'],
            'pptx': [b'PK\x03\x04'],
            'doc': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],  # OLE format
            'xls': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
            'ppt': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
            
            # Images
            'jpg': [b'\xff\xd8\xff'],
            'jpeg': [b'\xff\xd8\xff'],
            'png': [b'\x89PNG\r\n\x1a\n'],
            'gif': [b'GIF87a', b'GIF89a'],
            'bmp': [b'BM'],
            'webp': [b'RIFF', b'WEBP'],
            
            # Archives
            'zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
            'rar': [b'Rar!\x1a\x07\x00'],
            '7z': [b'7z\xbc\xaf\x27\x1c'],
        }
        
        # Dangerous file patterns
        self.dangerous_patterns = [
            # Executable patterns
            b'MZ',  # Windows executables
            b'\x7fELF',  # Linux executables
            b'\xfe\xed\xfa',  # Mach-O executables (macOS)
            
            # Script patterns
            b'#!/bin/sh',
            b'#!/bin/bash',
            b'@echo off',
            b'<script',
            b'javascript:',
            b'vbscript:',
        ]
        
        # Thai encoding detection patterns
        self.thai_patterns = [
            # Thai Unicode ranges
            (0x0e01, 0x0e5b),  # Thai characters
            (0x0e81, 0x0edf),  # Lao characters (often mixed with Thai)
        ]
        
        # Initialize libmagic if available
        try:
            self.magic = magic.Magic(mime=True)
            self.has_magic = True
        except Exception as e:
            logger.warning(f"libmagic not available: {e}")
            self.has_magic = False
    
    def validate_file(self, file_content: bytes, filename: str) -> ValidationResult:
        """
        Comprehensive file validation with security and corruption checks
        """
        file_size = len(file_content)
        
        # Basic size check
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                error_code='empty_file',
                file_type=None,
                mime_type=None,
                file_size=file_size,
                detected_encoding=None,
                security_issues=[],
                metadata={}
            )
        
        if file_size > Config.MAX_FILE_SIZE:
            return ValidationResult(
                is_valid=False,
                error_code='file_too_large',
                file_type=None,
                mime_type=None,
                file_size=file_size,
                detected_encoding=None,
                security_issues=[],
                metadata={'max_allowed_size': Config.MAX_FILE_SIZE}
            )
        
        # Extract file extension
        file_ext = Path(filename).suffix.lower().lstrip('.')
        
        # Detect MIME type
        mime_type = self._detect_mime_type(file_content, filename)
        
        # Validate file signature
        signature_valid, detected_type = self._validate_file_signature(file_content, file_ext)
        
        # Security checks
        security_issues = self._perform_security_checks(file_content, filename)
        
        # Corruption checks
        is_corrupted, corruption_details = self._check_file_corruption(file_content, file_ext)
        
        # Encoding detection for text files
        detected_encoding = None
        if file_ext in ['txt', 'md', 'csv'] or detected_type in ['text']:
            detected_encoding = self._detect_text_encoding(file_content)
        
        # Check if file type is allowed
        if not self._is_file_type_allowed(file_ext, detected_type):
            return ValidationResult(
                is_valid=False,
                error_code='unsupported_file',
                file_type=detected_type or file_ext,
                mime_type=mime_type,
                file_size=file_size,
                detected_encoding=detected_encoding,
                security_issues=security_issues,
                metadata={'allowed_extensions': list(Config.ALLOWED_FILE_EXTENSIONS.keys())}
            )
        
        # Check for security issues
        if security_issues:
            return ValidationResult(
                is_valid=False,
                error_code='security_risk',
                file_type=detected_type or file_ext,
                mime_type=mime_type,
                file_size=file_size,
                detected_encoding=detected_encoding,
                security_issues=security_issues,
                metadata={}
            )
        
        # Check for corruption
        if is_corrupted:
            return ValidationResult(
                is_valid=False,
                error_code='file_corrupted',
                file_type=detected_type or file_ext,
                mime_type=mime_type,
                file_size=file_size,
                detected_encoding=detected_encoding,
                security_issues=security_issues,
                metadata=corruption_details
            )
        
        # File is valid
        return ValidationResult(
            is_valid=True,
            error_code=None,
            file_type=detected_type or file_ext,
            mime_type=mime_type,
            file_size=file_size,
            detected_encoding=detected_encoding,
            security_issues=[],
            metadata={
                'signature_valid': signature_valid,
                'file_hash': hashlib.sha256(file_content).hexdigest()[:16]
            }
        )
    
    def _detect_mime_type(self, file_content: bytes, filename: str) -> Optional[str]:
        """
        Detect MIME type using multiple methods
        """
        if self.has_magic:
            try:
                return self.magic.from_buffer(file_content)
            except Exception as e:
                logger.warning(f"Magic MIME detection failed: {e}")
        
        # Fallback to mimetypes based on filename
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type
    
    def _validate_file_signature(self, file_content: bytes, file_ext: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file signature against known patterns
        """
        if len(file_content) < 8:
            return False, None
        
        # Check specific file type signatures
        if file_ext in self.file_signatures:
            signatures = self.file_signatures[file_ext]
            for signature in signatures:
                if file_content.startswith(signature):
                    return True, file_ext
        
        # Check all signatures to detect actual file type
        for file_type, signatures in self.file_signatures.items():
            for signature in signatures:
                if file_content.startswith(signature):
                    return file_ext == file_type, file_type
        
        # Special handling for Office formats (ZIP-based)
        if file_content.startswith(b'PK\x03\x04'):
            detected_office_type = self._detect_office_format(file_content)
            if detected_office_type:
                return file_ext == detected_office_type, detected_office_type
        
        return True, None  # Unknown signature, assume valid
    
    def _detect_office_format(self, file_content: bytes) -> Optional[str]:
        """
        Detect specific Office format from ZIP content
        """
        try:
            zip_file = zipfile.ZipFile(io.BytesIO(file_content))
            file_list = zip_file.namelist()
            
            if 'word/document.xml' in file_list:
                return 'docx'
            elif 'xl/workbook.xml' in file_list:
                return 'xlsx'
            elif 'ppt/presentation.xml' in file_list:
                return 'pptx'
            
        except zipfile.BadZipFile:
            pass
        
        return None
    
    def _perform_security_checks(self, file_content: bytes, filename: str) -> List[str]:
        """
        Perform security checks on file content
        """
        security_issues = []
        
        # Check for dangerous file patterns
        for pattern in self.dangerous_patterns:
            if pattern in file_content:
                security_issues.append(f'Dangerous pattern detected: {pattern.hex()}')
        
        # Check filename for suspicious extensions
        if '..' in filename or '/' in filename or '\\' in filename:
            security_issues.append('Suspicious filename path')
        
        # Check for double extensions (like .pdf.exe)
        parts = filename.split('.')
        if len(parts) > 2:
            security_issues.append('Multiple file extensions detected')
        
        # Check for embedded files in Office documents
        if filename.lower().endswith(('.docx', '.xlsx', '.pptx')):
            embedded_files = self._check_embedded_files(file_content)
            if embedded_files:
                security_issues.extend(embedded_files)
        
        # Check file size anomalies
        if len(file_content) > 50 * 1024 * 1024:  # > 50MB
            security_issues.append('Unusually large file size')
        
        return security_issues
    
    def _check_embedded_files(self, file_content: bytes) -> List[str]:
        """
        Check for potentially dangerous embedded files in Office documents
        """
        issues = []
        
        try:
            zip_file = zipfile.ZipFile(io.BytesIO(file_content))
            
            for file_info in zip_file.filelist:
                filename = file_info.filename.lower()
                
                # Check for executable files
                if any(filename.endswith(ext) for ext in ['.exe', '.bat', '.cmd', '.scr', '.vbs']):
                    issues.append(f'Embedded executable: {filename}')
                
                # Check for suspicious paths
                if '..' in filename or filename.startswith('/'):
                    issues.append(f'Suspicious embedded path: {filename}')
                    
        except zipfile.BadZipFile:
            pass
        
        return issues
    
    def _check_file_corruption(self, file_content: bytes, file_ext: str) -> Tuple[bool, Dict]:
        """
        Check for file corruption using format-specific validation
        """
        corruption_details = {}
        
        try:
            if file_ext == 'pdf':
                return self._check_pdf_corruption(file_content)
            elif file_ext in ['docx', 'xlsx', 'pptx']:
                return self._check_office_corruption(file_content)
            elif file_ext in ['jpg', 'jpeg']:
                return self._check_jpeg_corruption(file_content)
            elif file_ext == 'png':
                return self._check_png_corruption(file_content)
            
        except Exception as e:
            logger.warning(f"Corruption check failed for {file_ext}: {e}")
            return True, {'error': str(e)}
        
        return False, corruption_details
    
    def _check_pdf_corruption(self, file_content: bytes) -> Tuple[bool, Dict]:
        """
        Check PDF file for corruption
        """
        try:
            import PyPDF2
            
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Basic checks
            if not pdf_reader.pages:
                return True, {'error': 'No pages found'}
            
            # Try to read first page
            first_page = pdf_reader.pages[0]
            first_page.extract_text()
            
            return False, {'pages': len(pdf_reader.pages)}
            
        except Exception as e:
            return True, {'error': str(e)}
    
    def _check_office_corruption(self, file_content: bytes) -> Tuple[bool, Dict]:
        """
        Check Office document for corruption
        """
        try:
            zip_file = zipfile.ZipFile(io.BytesIO(file_content))
            
            # Test ZIP integrity
            bad_files = zip_file.testzip()
            if bad_files:
                return True, {'corrupted_files': bad_files}
            
            # Check for required Office files
            file_list = zip_file.namelist()
            required_files = ['[Content_Types].xml', '_rels/.rels']
            
            for required_file in required_files:
                if required_file not in file_list:
                    return True, {'missing_required_file': required_file}
            
            return False, {'files_count': len(file_list)}
            
        except zipfile.BadZipFile as e:
            return True, {'error': 'Invalid ZIP structure'}
        except Exception as e:
            return True, {'error': str(e)}
    
    def _check_jpeg_corruption(self, file_content: bytes) -> Tuple[bool, Dict]:
        """
        Check JPEG file for corruption
        """
        # Check JPEG markers
        if not file_content.startswith(b'\xff\xd8\xff'):
            return True, {'error': 'Invalid JPEG header'}
        
        if not file_content.endswith(b'\xff\xd9'):
            return True, {'error': 'Missing JPEG end marker'}
        
        return False, {}
    
    def _check_png_corruption(self, file_content: bytes) -> Tuple[bool, Dict]:
        """
        Check PNG file for corruption
        """
        if not file_content.startswith(b'\x89PNG\r\n\x1a\n'):
            return True, {'error': 'Invalid PNG signature'}
        
        # Check for IHDR chunk (must be first)
        if file_content[12:16] != b'IHDR':
            return True, {'error': 'Missing IHDR chunk'}
        
        return False, {}
    
    def _detect_text_encoding(self, file_content: bytes) -> Optional[str]:
        """
        Detect text encoding with Thai language support
        """
        # Try Thai-specific encodings first
        thai_encodings = ['utf-8', 'utf-8-sig', 'tis-620', 'cp874']
        
        for encoding in thai_encodings:
            try:
                decoded_text = file_content.decode(encoding)
                
                # Check if this contains Thai characters
                if self._contains_thai_text(decoded_text):
                    return encoding
                
                # For non-Thai text, prefer UTF-8
                if encoding in ['utf-8', 'utf-8-sig']:
                    return encoding
                    
            except UnicodeDecodeError:
                continue
        
        # Fallback encodings
        fallback_encodings = ['latin1', 'cp1252', 'iso-8859-1']
        for encoding in fallback_encodings:
            try:
                file_content.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        
        return None
    
    def _contains_thai_text(self, text: str) -> bool:
        """
        Check if text contains Thai characters
        """
        for char in text:
            char_code = ord(char)
            for start, end in self.thai_patterns:
                if start <= char_code <= end:
                    return True
        return False
    
    def _is_file_type_allowed(self, file_ext: str, detected_type: Optional[str]) -> bool:
        """
        Check if file type is in allowed extensions
        """
        # Check extension against allowed list
        for category, extensions in Config.ALLOWED_FILE_EXTENSIONS.items():
            ext_with_dot = f'.{file_ext}'
            if ext_with_dot in extensions:
                return True
        
        # Check detected type if extension check failed
        if detected_type and detected_type != file_ext:
            for category, extensions in Config.ALLOWED_FILE_EXTENSIONS.items():
                ext_with_dot = f'.{detected_type}'
                if ext_with_dot in extensions:
                    return True
        
        return False

# Create singleton instance
enhanced_file_validator = EnhancedFileValidator()

# Legacy function for backward compatibility
def validate_file_upload(content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
    """Legacy validation function for backward compatibility"""
    result = enhanced_file_validator.validate_file(content, filename)
    return result.is_valid, result.error_code