"""
Helper Utilities Module

Provides common utility functions for the Smart Log Analyzer.
"""

import hashlib
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import gzip
import zipfile


def hash_string(text: str, algorithm: str = "md5") -> str:
    """Generate hash of a string."""
    if algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(text.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized.strip('_')


def safe_get_nested(data: Dict[str, Any], keys: Union[str, List[str]], default: Any = None) -> Any:
    """Safely get nested dictionary value."""
    if isinstance(keys, str):
        keys = keys.split('.')
    
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def normalize_log_level(level: str) -> str:
    """Normalize log level string."""
    if not level:
        return "info"
    
    level = level.lower().strip()
    
    # Map common variations
    level_mapping = {
        "warn": "warning",
        "err": "error",
        "fatal": "critical",
        "panic": "critical",
        "trace": "debug"
    }
    
    return level_mapping.get(level, level)


def extract_timestamp_components(timestamp_str: str) -> Dict[str, Any]:
    """Extract timestamp components for analysis."""
    try:
        # Try common formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S"
        ]
        
        dt = None
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                break
            except ValueError:
                continue
        
        if dt is None:
            return {"valid": False, "error": "Unable to parse timestamp"}
        
        return {
            "valid": True,
            "datetime": dt,
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "hour": dt.hour,
            "minute": dt.minute,
            "second": dt.second,
            "weekday": dt.weekday(),
            "iso_week": dt.isocalendar()[1],
            "quarter": (dt.month - 1) // 3 + 1,
            "day_of_year": dt.timetuple().tm_yday
        }
    
    except Exception as e:
        return {"valid": False, "error": str(e)}


def calculate_file_hash(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def compress_data(data: Union[str, bytes], method: str = "gzip") -> bytes:
    """Compress data using specified method."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    if method == "gzip":
        return gzip.compress(data)
    else:
        raise ValueError(f"Unsupported compression method: {method}")


def decompress_data(data: bytes, method: str = "gzip") -> str:
    """Decompress data using specified method."""
    if method == "gzip":
        return gzip.decompress(data).decode('utf-8')
    else:
        raise ValueError(f"Unsupported compression method: {method}")


def format_bytes(bytes_value: int) -> str:
    """Format bytes in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in human readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def validate_json_string(json_str: str) -> Tuple[bool, Optional[str]]:
    """Validate if string is valid JSON."""
    try:
        json.loads(json_str)
        return True, None
    except json.JSONDecodeError as e:
        return False, str(e)


def extract_patterns_from_text(text: str, patterns: List[str]) -> Dict[str, List[str]]:
    """Extract patterns from text using regex."""
    results = {}
    
    for pattern in patterns:
        try:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                results[pattern] = matches
        except re.error as e:
            results[pattern] = [f"Regex error: {e}"]
    
    return results


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dictionaries(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later ones taking precedence."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def clean_string(text: str, max_length: Optional[int] = None) -> str:
    """Clean string by removing extra whitespace and optionally truncating."""
    if not text:
        return ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Truncate if necessary
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + "..."
    
    return cleaned


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get comprehensive file information."""
    path = Path(file_path)
    
    if not path.exists():
        return {"exists": False}
    
    stat = path.stat()
    
    return {
        "exists": True,
        "size": stat.st_size,
        "size_formatted": format_bytes(stat.st_size),
        "created": datetime.fromtimestamp(stat.st_ctime),
        "modified": datetime.fromtimestamp(stat.st_mtime),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "extension": path.suffix,
        "name": path.name,
        "parent": str(path.parent)
    }


def retry_operation(operation, max_retries: int = 3, delay: float = 1.0, exponential_backoff: bool = True):
    """Retry operation with configurable backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        time.sleep(current_delay)
                        if exponential_backoff:
                            current_delay *= 2
                    else:
                        raise last_exception
            
            return None
        return wrapper
    return decorator


def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text."""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)


def extract_ip_addresses_from_text(text: str) -> List[str]:
    """Extract IP addresses from text."""
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    return re.findall(ip_pattern, text)


def extract_email_addresses_from_text(text: str) -> List[str]:
    """Extract email addresses from text."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity based on common words."""
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def create_summary_statistics(values: List[Union[int, float]]) -> Dict[str, Any]:
    """Create summary statistics for a list of numerical values."""
    if not values:
        return {"count": 0}
    
    values = [v for v in values if v is not None]
    
    if not values:
        return {"count": 0}
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    return {
        "count": n,
        "min": min(sorted_values),
        "max": max(sorted_values),
        "mean": sum(sorted_values) / n,
        "median": sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2,
        "sum": sum(sorted_values),
        "percentile_25": sorted_values[n // 4] if n >= 4 else sorted_values[0],
        "percentile_75": sorted_values[3 * n // 4] if n >= 4 else sorted_values[-1]
    }


def mask_sensitive_data(text: str, patterns: Optional[Dict[str, str]] = None) -> str:
    """Mask sensitive data in text."""
    if not patterns:
        patterns = {
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b': '[IP]',
            r'\b4[0-9]{12}(?:[0-9]{3})?\b': '[CARD]',  # Credit card pattern
            r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b': '[SSN]',  # SSN pattern
            r'password["\s]*[:=]["\s]*[^"\s]+': 'password="[MASKED]"',
            r'token["\s]*[:=]["\s]*[^"\s]+': 'token="[MASKED]"',
            r'key["\s]*[:=]["\s]*[^"\s]+': 'key="[MASKED]"'
        }
    
    masked_text = text
    for pattern, replacement in patterns.items():
        masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)
    
    return masked_text


def generate_unique_id(prefix: str = "", length: int = 8) -> str:
    """Generate a unique identifier."""
    import random
    import string
    
    timestamp = str(int(time.time()))
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    if prefix:
        return f"{prefix}_{timestamp}_{random_part}"
    else:
        return f"{timestamp}_{random_part}"


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    return bool(re.match(pattern, url))


class Timer:
    """Simple timer context manager."""
    
    def __init__(self, operation_name: str = "operation"):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
    
    def get_duration(self) -> float:
        """Get duration in seconds."""
        return self.duration
    
    def get_formatted_duration(self) -> str:
        """Get formatted duration string."""
        return format_duration(self.duration) if self.duration else "N/A"


class DataCache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if current_time >= expiry
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
