"""
Log parsing utilities for AI Driven Realtime Log Analyser
"""

import json
import re
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from collections import deque

from core.models import LogEntry

logger = logging.getLogger(__name__)


class LogParser:
    """
    Universal log parser that can handle multiple log formats:
    - JSON logs
    - Plain text logs
    - Structured logs with timestamps
    """
    
    def __init__(self):
        # Common timestamp patterns
        self.timestamp_patterns = [
            # ISO format: 2024-01-15T10:30:45.123Z
            (r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z?)', '%Y-%m-%dT%H:%M:%S.%fZ'),
            (r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?)', '%Y-%m-%dT%H:%M:%SZ'),
            
            # Standard format: 2024-01-15 10:30:45
            (r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?)', '%Y-%m-%d %H:%M:%S.%f'),
            (r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S'),
            
            # Log format: Jan 15 10:30:45
            (r'([A-Za-z]{3} \d{1,2} \d{2}:\d{2}:\d{2})', '%b %d %H:%M:%S'),
        ]
        
        # Log level patterns
        self.level_pattern = re.compile(r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)\b', re.IGNORECASE)
        
        # Component patterns
        self.component_patterns = [
            (r'\[([A-Z_]+)\]', 1),  # [COMPONENT_NAME]
            (r'(\w+)\s*:', 1),      # Component:
            (r'component["\']:\s*["\']([^"\']+)', 1),  # JSON component field
        ]

    async def parse_file(self, file_path: Path) -> List[LogEntry]:
        """
        Parse a log file and return list of LogEntry objects
        
        Args:
            file_path: Path to the log file
            
        Returns:
            List of parsed LogEntry objects
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")
        
        logger.info(f"📖 Parsing log file: {file_path}")
        
        entries = []
        line_number = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_number += 1
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    entry = await self._parse_line(line, line_number)
                    if entry:
                        entries.append(entry)
                        
                        # Log progress for large files
                        if line_number % 10000 == 0:
                            logger.info(f"📊 Parsed {line_number} lines...")
        
        except Exception as e:
            logger.error(f"❌ Error parsing file {file_path}: {e}")
            raise
        
        logger.info(f"✅ Parsed {len(entries)} log entries from {line_number} lines")
        return entries

    async def parse_new_entries(self, file_path: Path, last_position: int) -> List[LogEntry]:
        """
        Parse new entries from a log file since last position
        
        Args:
            file_path: Path to the log file
            last_position: Last read position in bytes
            
        Returns:
            List of new LogEntry objects
        """
        if not file_path.exists():
            return []
        
        current_size = file_path.stat().st_size
        if current_size <= last_position:
            return []
        
        entries = []
        line_number = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_position)
                
                for line in f:
                    line_number += 1
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    entry = await self._parse_line(line, line_number)
                    if entry:
                        entries.append(entry)
        
        except Exception as e:
            logger.error(f"❌ Error parsing new entries from {file_path}: {e}")
        
        return entries

    async def _parse_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """
        Parse a single log line
        
        Args:
            line: The log line to parse
            line_number: Line number in the file
            
        Returns:
            LogEntry object or None if parsing fails
        """
        try:
            # Try to parse as JSON first
            if line.startswith('{') and line.endswith('}'):
                return await self._parse_json_line(line, line_number)
            else:
                return await self._parse_text_line(line, line_number)
        
        except Exception as e:
            logger.debug(f"Failed to parse line {line_number}: {e}")
            # Return a basic entry for unparseable lines
            return LogEntry(
                message=line,
                line_number=line_number,
                level="INFO"
            )

    async def _parse_json_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """Parse a JSON log line"""
        try:
            data = json.loads(line)
            
            # Extract fields from JSON
            timestamp = self._extract_timestamp_from_json(data)
            level = self._extract_level_from_json(data)
            message = self._extract_message_from_json(data)
            component = self._extract_component_from_json(data)
            thread = data.get('thread') or data.get('threadName')
            logger_name = data.get('logger') or data.get('loggerName')
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                component=component,
                message=message,
                thread=thread,
                logger=logger_name,
                raw_data=data,
                line_number=line_number
            )
            
        except json.JSONDecodeError:
            return None

    async def _parse_text_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """Parse a plain text log line"""
        # Extract timestamp
        timestamp = self._extract_timestamp_from_text(line)
        
        # Extract log level
        level = self._extract_level_from_text(line)
        
        # Extract component
        component = self._extract_component_from_text(line)
        
        # The rest is the message (clean up formatting)
        message = self._clean_message(line)
        
        return LogEntry(
            timestamp=timestamp,
            level=level or "INFO",
            component=component,
            message=message,
            line_number=line_number
        )

    def _extract_timestamp_from_json(self, data: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from JSON data"""
        # Common timestamp field names
        timestamp_fields = ['timestamp', 'time', '@timestamp', 'datetime', 'ts']
        
        for field in timestamp_fields:
            if field in data:
                return self._parse_timestamp(str(data[field]))
        
        return None

    def _extract_timestamp_from_text(self, line: str) -> Optional[datetime]:
        """Extract timestamp from text line"""
        for pattern, fmt in self.timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                timestamp_str = match.group(1)
                try:
                    if '%f' in fmt and '.' not in timestamp_str:
                        # Handle format without microseconds
                        fmt = fmt.replace('.%f', '')
                    return datetime.strptime(timestamp_str, fmt.replace('Z', ''))
                except ValueError:
                    continue
        return None

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string"""
        if not timestamp_str:
            return None
        
        # Try ISO format first
        try:
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            if 'T' in timestamp_str:
                if '.' in timestamp_str:
                    return datetime.fromisoformat(timestamp_str)
                else:
                    return datetime.fromisoformat(timestamp_str)
        except ValueError:
            pass
        
        # Try other patterns
        for pattern, fmt in self.timestamp_patterns:
            try:
                if '%f' in fmt and '.' not in timestamp_str:
                    fmt = fmt.replace('.%f', '')
                return datetime.strptime(timestamp_str, fmt.replace('Z', ''))
            except ValueError:
                continue
        
        return None

    def _extract_level_from_json(self, data: Dict[str, Any]) -> str:
        """Extract log level from JSON data"""
        level_fields = ['level', 'severity', 'levelname']
        
        for field in level_fields:
            if field in data:
                return str(data[field]).upper()
        
        return "INFO"

    def _extract_message_from_json(self, data: Dict[str, Any]) -> str:
        """Extract message from JSON data"""
        message_fields = ['message', 'msg', 'text', 'description']
        
        for field in message_fields:
            if field in data:
                return str(data[field])
        
        # If no specific message field, return the whole JSON as string
        return json.dumps(data)

    def _extract_level_from_text(self, line: str) -> Optional[str]:
        """Extract log level from text line"""
        match = self.level_pattern.search(line)
        if match:
            level = match.group(1).upper()
            # Normalize WARNING to WARN
            if level == "WARNING":
                level = "WARN"
            return level
        return None

    def _extract_component_from_json(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract component from JSON data"""
        component_fields = ['component', 'service', 'module', 'logger', 'loggerName']
        
        for field in component_fields:
            if field in data:
                return str(data[field])
        
        return None

    def _extract_component_from_text(self, line: str) -> Optional[str]:
        """Extract component from text line"""
        for pattern, group in self.component_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(group)
        return None

    def _clean_message(self, line: str) -> str:
        """Clean and extract the main message from a log line"""
        # Remove timestamp
        for pattern, _ in self.timestamp_patterns:
            line = re.sub(pattern, '', line)
        
        # Remove log level
        line = self.level_pattern.sub('', line)
        
        # Remove component brackets
        line = re.sub(r'\[[^\]]*\]', '', line)
        
        # Clean up whitespace
        line = ' '.join(line.split())
        
        return line.strip()
