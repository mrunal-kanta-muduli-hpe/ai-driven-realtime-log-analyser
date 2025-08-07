"""
Pattern detection for AI Driven Realtime Log Analyser
"""

import re
import logging
from typing import List, Dict, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass

from core.models import LogEntry, ErrorPattern

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """Represents a pattern match"""
    pattern: str
    confidence: float
    examples: List[str]
    count: int


class PatternDetector:
    """
    Detects patterns in log entries, especially error patterns
    """
    
    def __init__(self):
        # Pre-defined error patterns
        self.known_patterns = [
            # Connection errors
            (r'connection\s+(refused|timeout|failed)', 'Connection Error'),
            (r'failed\s+to\s+connect', 'Connection Error'),
            (r'cannot\s+connect', 'Connection Error'),
            
            # Authentication errors
            (r'authentication\s+(failed|error)', 'Authentication Error'),
            (r'unauthorized|forbidden', 'Authorization Error'),
            (r'invalid\s+(credentials|token|password)', 'Authentication Error'),
            
            # Resource errors
            (r'out\s+of\s+(memory|disk|space)', 'Resource Error'),
            (r'insufficient\s+(resources|memory|disk)', 'Resource Error'),
            (r'quota\s+exceeded', 'Resource Error'),
            
            # Network errors
            (r'network\s+(error|timeout|unreachable)', 'Network Error'),
            (r'dns\s+(resolution|lookup)\s+(failed|error)', 'Network Error'),
            (r'host\s+(unreachable|not\s+found)', 'Network Error'),
            
            # Database errors
            (r'database\s+(connection|error|timeout)', 'Database Error'),
            (r'sql\s+(error|exception)', 'Database Error'),
            (r'deadlock\s+detected', 'Database Error'),
            
            # File system errors
            (r'file\s+(not\s+found|missing)', 'File Error'),
            (r'permission\s+denied', 'Permission Error'),
            (r'no\s+such\s+(file|directory)', 'File Error'),
            
            # API errors
            (r'api\s+(error|timeout|failed)', 'API Error'),
            (r'http\s+(error|status)\s+[45]\d{2}', 'HTTP Error'),
            (r'service\s+(unavailable|timeout)', 'Service Error'),
            
            # Configuration errors
            (r'configuration\s+(error|invalid)', 'Configuration Error'),
            (r'missing\s+(configuration|property)', 'Configuration Error'),
            (r'invalid\s+(configuration|setting)', 'Configuration Error'),
        ]
        
        # Normalization patterns (to group similar errors)
        self.normalization_patterns = [
            (r'\d+', 'N'),                    # Numbers -> N
            (r'[a-f0-9]{8,}', 'HASH'),        # Hashes -> HASH
            (r'\b\d+\.\d+\.\d+\.\d+\b', 'IP'), # IPs -> IP
            (r'["\'][^"\']*["\']', 'STRING'),  # Quoted strings -> STRING
            (r':\d+', ':PORT'),               # Ports -> :PORT
            (r'/[^\s]+', '/PATH'),            # File paths -> /PATH
        ]

    async def detect_patterns(self, log_entries: List[LogEntry]) -> List[Dict]:
        """
        Detect patterns in log entries
        
        Args:
            log_entries: List of log entries to analyze
            
        Returns:
            List of detected patterns with metadata
        """
        logger.info(f"🔍 Analyzing patterns in {len(log_entries)} log entries...")
        
        # Filter error and warning entries
        error_entries = [e for e in log_entries if e.level in ['ERROR', 'WARN']]
        
        if not error_entries:
            logger.info("No error/warning entries found for pattern analysis")
            return []
        
        logger.info(f"📊 Analyzing {len(error_entries)} error/warning entries")
        
        patterns = []
        
        # Detect known patterns
        known_patterns = await self._detect_known_patterns(error_entries)
        patterns.extend(known_patterns)
        
        # Detect new patterns using clustering
        new_patterns = await self._detect_new_patterns(error_entries)
        patterns.extend(new_patterns)
        
        # Sort by frequency
        patterns.sort(key=lambda x: x['count'], reverse=True)
        
        logger.info(f"✅ Detected {len(patterns)} patterns")
        
        return patterns

    async def _detect_known_patterns(self, entries: List[LogEntry]) -> List[Dict]:
        """Detect known error patterns"""
        pattern_matches = defaultdict(list)
        
        for entry in entries:
            message = entry.message.lower()
            
            for pattern_regex, pattern_name in self.known_patterns:
                if re.search(pattern_regex, message, re.IGNORECASE):
                    pattern_matches[pattern_name].append({
                        'message': entry.message,
                        'timestamp': entry.timestamp,
                        'component': entry.component
                    })
        
        results = []
        for pattern_name, matches in pattern_matches.items():
            if len(matches) >= 2:  # Only report patterns with multiple occurrences
                results.append({
                    'pattern': pattern_name,
                    'type': 'known',
                    'count': len(matches),
                    'examples': [m['message'] for m in matches[:3]],
                    'components': list(set(m['component'] for m in matches if m['component'])),
                    'confidence': 0.9
                })
        
        return results

    async def _detect_new_patterns(self, entries: List[LogEntry]) -> List[Dict]:
        """Detect new patterns using message clustering"""
        # Normalize messages
        normalized_messages = defaultdict(list)
        
        for entry in entries:
            normalized = self._normalize_message(entry.message)
            normalized_messages[normalized].append(entry)
        
        results = []
        for normalized, group_entries in normalized_messages.items():
            if len(group_entries) >= 3:  # Pattern must occur at least 3 times
                # Calculate pattern confidence based on similarity
                confidence = self._calculate_pattern_confidence(group_entries)
                
                if confidence >= 0.6:  # Minimum confidence threshold
                    results.append({
                        'pattern': normalized,
                        'type': 'discovered',
                        'count': len(group_entries),
                        'examples': [e.message for e in group_entries[:3]],
                        'components': list(set(e.component for e in group_entries if e.component)),
                        'confidence': confidence
                    })
        
        return results

    def _normalize_message(self, message: str) -> str:
        """Normalize a message for pattern matching"""
        normalized = message.lower()
        
        # Apply normalization patterns
        for pattern, replacement in self.normalization_patterns:
            normalized = re.sub(pattern, replacement, normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized

    def _calculate_pattern_confidence(self, entries: List[LogEntry]) -> float:
        """Calculate confidence score for a pattern"""
        if len(entries) < 2:
            return 0.0
        
        messages = [e.message for e in entries]
        
        # Calculate similarity based on common words
        all_words = []
        for msg in messages:
            words = set(msg.lower().split())
            all_words.append(words)
        
        if not all_words:
            return 0.0
        
        # Find common words across all messages
        common_words = set.intersection(*all_words)
        total_unique_words = set.union(*all_words)
        
        if not total_unique_words:
            return 0.0
        
        # Confidence is ratio of common words to total unique words
        confidence = len(common_words) / len(total_unique_words)
        
        # Boost confidence for frequently occurring patterns
        frequency_boost = min(len(entries) / 10.0, 0.3)
        
        return min(confidence + frequency_boost, 1.0)

    async def get_pattern_statistics(self, entries: List[LogEntry]) -> Dict:
        """Get comprehensive pattern statistics"""
        patterns = await self.detect_patterns(entries)
        
        stats = {
            'total_patterns': len(patterns),
            'known_patterns': len([p for p in patterns if p['type'] == 'known']),
            'discovered_patterns': len([p for p in patterns if p['type'] == 'discovered']),
            'high_confidence_patterns': len([p for p in patterns if p['confidence'] >= 0.8]),
            'patterns_by_component': defaultdict(int),
            'top_patterns': patterns[:10]
        }
        
        # Count patterns by component
        for pattern in patterns:
            for component in pattern.get('components', []):
                stats['patterns_by_component'][component] += 1
        
        return stats

    def create_pattern_objects(self, pattern_data: List[Dict]) -> List[ErrorPattern]:
        """Convert pattern data to ErrorPattern objects"""
        patterns = []
        
        for data in pattern_data:
            pattern = ErrorPattern(
                pattern=data['pattern'],
                count=data['count'],
                severity=self._determine_severity(data),
                component=data.get('components', [None])[0],
                examples=data.get('examples', [])
            )
            patterns.append(pattern)
        
        return patterns

    def _determine_severity(self, pattern_data: Dict) -> str:
        """Determine severity based on pattern characteristics"""
        count = pattern_data['count']
        confidence = pattern_data['confidence']
        pattern_name = pattern_data['pattern'].lower()
        
        # High severity indicators
        if any(keyword in pattern_name for keyword in ['critical', 'fatal', 'crash', 'exception']):
            return 'HIGH'
        
        # Medium-high severity
        if any(keyword in pattern_name for keyword in ['error', 'failed', 'timeout']):
            if count >= 10 or confidence >= 0.8:
                return 'HIGH'
            return 'MEDIUM'
        
        # Warning level
        if any(keyword in pattern_name for keyword in ['warn', 'deprecated']):
            return 'LOW'
        
        # Default based on frequency
        if count >= 20:
            return 'HIGH'
        elif count >= 5:
            return 'MEDIUM'
        else:
            return 'LOW'
