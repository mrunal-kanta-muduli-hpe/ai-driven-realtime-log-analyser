"""
Log Parser Module

Handles parsing of various log formats including JSON and plain text.
Extracts structured information from log entries for further analysis.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..utils.config import Config


class LogParser:
    """Parser for various log formats with error detection capabilities."""
    
    def __init__(self, config: Config):
        """Initialize the log parser with configuration."""
        self.config = config
        self.error_keywords = [
            "error", "failed", "failure", "exception", "panic", 
            "fatal", "critical", "timeout", "refused", "denied"
        ]
        self.warning_keywords = [
            "warning", "warn", "deprecated", "retry", "fallback"
        ]
    
    def parse_file(self, file_path: str, format_type: str = "json") -> List[Dict[str, Any]]:
        """Parse a log file and return structured log entries."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")
        
        logging.info(f"Parsing {format_type} log file: {file_path}")
        
        if format_type.lower() == "json":
            return self._parse_json_file(file_path)
        elif format_type.lower() == "text":
            return self._parse_text_file(file_path)
        else:
            raise ValueError(f"Unsupported log format: {format_type}")
    
    def _parse_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse JSON format log file."""
        entries = []
        line_number = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line_number += 1
                line = line.strip()
                
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    
                    # Enhance entry with metadata
                    enhanced_entry = self._enhance_json_entry(entry, line_number, file_path)
                    entries.append(enhanced_entry)
                    
                except json.JSONDecodeError as e:
                    logging.warning(f"Invalid JSON at line {line_number}: {e}")
                    # Create a basic entry for invalid JSON
                    entries.append({
                        "raw_line": line,
                        "line_number": line_number,
                        "file_path": str(file_path),
                        "parse_error": str(e),
                        "timestamp": None,
                        "level": "unknown",
                        "message": line,
                        "is_error": False,
                        "is_warning": False
                    })
        
        logging.info(f"Parsed {len(entries)} entries from JSON file")
        return entries
    
    def _parse_text_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse plain text log file."""
        entries = []
        line_number = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line_number += 1
                line = line.strip()
                
                if not line:
                    continue
                
                entry = self._parse_text_line(line, line_number, file_path)
                entries.append(entry)
        
        logging.info(f"Parsed {len(entries)} entries from text file")
        return entries
    
    def _enhance_json_entry(self, entry: Dict[str, Any], line_number: int, file_path: Path) -> Dict[str, Any]:
        """Enhance JSON log entry with additional metadata."""
        enhanced = {
            "raw_entry": entry.copy(),
            "line_number": line_number,
            "file_path": str(file_path),
            "timestamp": self._extract_timestamp(entry),
            "level": self._extract_log_level(entry),
            "message": self._extract_message(entry),
            "component": self._extract_component(entry),
            "error_details": self._extract_error_details(entry),
            "stacktrace": entry.get("stacktrace", ""),
            "is_error": self._is_error_entry(entry),
            "is_warning": self._is_warning_entry(entry)
        }
        
        # Add all original fields
        for key, value in entry.items():
            if key not in enhanced:
                enhanced[key] = value
        
        return enhanced
    
    def _parse_text_line(self, line: str, line_number: int, file_path: Path) -> Dict[str, Any]:
        """Parse a single text log line."""
        # Common log patterns
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)'
        level_pattern = r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b'
        
        timestamp_match = re.search(timestamp_pattern, line)
        level_match = re.search(level_pattern, line, re.IGNORECASE)
        
        entry = {
            "raw_line": line,
            "line_number": line_number,
            "file_path": str(file_path),
            "timestamp": timestamp_match.group(1) if timestamp_match else None,
            "level": level_match.group(1).lower() if level_match else "unknown",
            "message": line,
            "component": self._extract_component_from_text(line),
            "error_details": None,
            "stacktrace": "",
            "is_error": self._is_error_text_line(line),
            "is_warning": self._is_warning_text_line(line)
        }
        
        return entry
    
    def _extract_timestamp(self, entry: Dict[str, Any]) -> Optional[str]:
        """Extract timestamp from log entry."""
        timestamp_fields = ["timestamp", "time", "@timestamp", "ts", "datetime"]
        
        for field in timestamp_fields:
            if field in entry:
                return str(entry[field])
        
        return None
    
    def _extract_log_level(self, entry: Dict[str, Any]) -> str:
        """Extract log level from entry."""
        level_fields = ["level", "severity", "priority", "log_level"]
        
        for field in level_fields:
            if field in entry:
                return str(entry[field]).lower()
        
        # Try to infer from message
        message = self._extract_message(entry)
        if message:
            level_pattern = r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b'
            match = re.search(level_pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        return "unknown"
    
    def _extract_message(self, entry: Dict[str, Any]) -> str:
        """Extract main message from log entry."""
        message_fields = ["message", "msg", "text", "description"]
        
        for field in message_fields:
            if field in entry:
                return str(entry[field])
        
        # If no specific message field, use entire entry as string
        return str(entry)
    
    def _extract_component(self, entry: Dict[str, Any]) -> Optional[str]:
        """Extract component/service identifier from log entry."""
        component_fields = ["component", "service", "module", "application", "app"]
        
        for field in component_fields:
            if field in entry:
                return str(entry[field])
        
        # Try to extract from message or other fields
        message = self._extract_message(entry)
        if message:
            # Look for common component patterns
            patterns = [
                r'virtualization-aggregator-(\w+)',
                r'(\w+)-service',
                r'Starting (\w+) service',
                r'(\w+) application'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    return match.group(1).lower()
        
        return None
    
    def _extract_component_from_text(self, line: str) -> Optional[str]:
        """Extract component from text log line."""
        patterns = [
            r'virtualization-aggregator-(\w+)',
            r'(\w+)-service',
            r'\[(\w+)\]',
            r'(\w+):',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        return None
    
    def _extract_error_details(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract error-specific details from log entry."""
        if not self._is_error_entry(entry):
            return None
        
        error_info = {}
        
        # Extract error message
        if "error" in entry:
            error_info["error_message"] = str(entry["error"])
        
        # Extract stack trace
        if "stacktrace" in entry:
            error_info["stacktrace"] = str(entry["stacktrace"])
        
        # Extract exception type
        if "exception" in entry:
            error_info["exception_type"] = str(entry["exception"])
        
        # Extract error code
        error_code_fields = ["error_code", "code", "status_code"]
        for field in error_code_fields:
            if field in entry:
                error_info["error_code"] = entry[field]
                break
        
        return error_info if error_info else None
    
    def _is_error_entry(self, entry: Dict[str, Any]) -> bool:
        """Determine if log entry represents an error."""
        # Check level
        level = self._extract_log_level(entry)
        if level in ["error", "fatal", "critical", "panic"]:
            return True
        
        # Check for error fields
        if "error" in entry or "exception" in entry:
            return True
        
        # Check message content
        message = self._extract_message(entry)
        return self._contains_error_keywords(message)
    
    def _is_warning_entry(self, entry: Dict[str, Any]) -> bool:
        """Determine if log entry represents a warning."""
        level = self._extract_log_level(entry)
        if level in ["warn", "warning"]:
            return True
        
        message = self._extract_message(entry)
        return self._contains_warning_keywords(message)
    
    def _is_error_text_line(self, line: str) -> bool:
        """Determine if text line represents an error."""
        return self._contains_error_keywords(line)
    
    def _is_warning_text_line(self, line: str) -> bool:
        """Determine if text line represents a warning."""
        return self._contains_warning_keywords(line)
    
    def _contains_error_keywords(self, text: str) -> bool:
        """Check if text contains error keywords."""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.error_keywords)
    
    def _contains_warning_keywords(self, text: str) -> bool:
        """Check if text contains warning keywords."""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.warning_keywords)
    
    def is_error(self, entry: Dict[str, Any]) -> bool:
        """Public method to check if an entry is an error."""
        return entry.get("is_error", False)
    
    def is_warning(self, entry: Dict[str, Any]) -> bool:
        """Public method to check if an entry is a warning."""
        return entry.get("is_warning", False)
    
    def get_statistics(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get parsing statistics for log entries."""
        if not entries:
            return {"total": 0, "errors": 0, "warnings": 0, "info": 0}
        
        total = len(entries)
        errors = sum(1 for entry in entries if self.is_error(entry))
        warnings = sum(1 for entry in entries if self.is_warning(entry))
        info = total - errors - warnings
        
        components = set()
        for entry in entries:
            if entry.get("component"):
                components.add(entry["component"])
        
        return {
            "total": total,
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "error_rate": (errors / total * 100) if total > 0 else 0,
            "unique_components": len(components),
            "components": list(components)
        }
