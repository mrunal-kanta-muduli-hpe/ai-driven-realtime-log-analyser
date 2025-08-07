"""
Pattern Detector Module

Identifies recurring patterns, error sequences, and anomalies in log data.
Uses statistical analysis and pattern matching to detect issues.
"""

import logging
import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime, timedelta

from ..utils.config import Config


class PatternDetector:
    """Detects patterns and anomalies in log data."""
    
    def __init__(self, config: Config):
        """Initialize pattern detector with configuration."""
        self.config = config
        self.min_pattern_frequency = config.get("pattern_detection.min_frequency", 3)
        self.time_window_minutes = config.get("pattern_detection.time_window", 60)
        
        # Common error patterns to look for
        self.error_patterns = {
            "connection_refused": r"connection refused",
            "timeout": r"timeout|timed out",
            "database_error": r"database|db|sql.*error",
            "authentication_failure": r"auth.*fail|authentication.*fail|login.*fail",
            "permission_denied": r"permission denied|access denied|forbidden",
            "out_of_memory": r"out of memory|oom|memory.*exceed",
            "network_error": r"network.*error|connection.*error|socket.*error",
            "service_unavailable": r"service unavailable|service.*down|unavailable",
            "configuration_error": r"config.*error|configuration.*error|invalid.*config",
            "startup_failure": r"startup.*fail|failed.*start|initialization.*fail"
        }
    
    def detect_patterns(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect various patterns in log entries."""
        logging.info(f"Detecting patterns in {len(log_entries)} log entries")
        
        patterns = []
        
        # Error frequency patterns
        error_patterns = self._detect_error_frequency_patterns(log_entries)
        patterns.extend(error_patterns)
        
        # Temporal patterns
        temporal_patterns = self._detect_temporal_patterns(log_entries)
        patterns.extend(temporal_patterns)
        
        # Component-specific patterns
        component_patterns = self._detect_component_patterns(log_entries)
        patterns.extend(component_patterns)
        
        # Error sequence patterns
        sequence_patterns = self._detect_error_sequences(log_entries)
        patterns.extend(sequence_patterns)
        
        # Regex-based pattern matching
        regex_patterns = self._detect_regex_patterns(log_entries)
        patterns.extend(regex_patterns)
        
        logging.info(f"Detected {len(patterns)} patterns")
        return patterns
    
    def _detect_error_frequency_patterns(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns based on error message frequency."""
        error_entries = [entry for entry in log_entries if entry.get("is_error", False)]
        
        if not error_entries:
            return []
        
        # Count error messages
        error_messages = [entry.get("message", "") for entry in error_entries]
        message_counts = Counter(error_messages)
        
        patterns = []
        for message, count in message_counts.items():
            if count >= self.min_pattern_frequency:
                # Get all entries with this message
                matching_entries = [
                    entry for entry in error_entries 
                    if entry.get("message", "") == message
                ]
                
                pattern = {
                    "type": "error_frequency",
                    "pattern_id": f"freq_{hash(message) % 10000:04d}",
                    "description": f"Recurring error message (frequency: {count})",
                    "error_message": message,
                    "frequency": count,
                    "severity": self._assess_severity(count, len(log_entries)),
                    "affected_components": list(set(
                        entry.get("component") for entry in matching_entries 
                        if entry.get("component")
                    )),
                    "first_occurrence": self._get_first_occurrence(matching_entries),
                    "last_occurrence": self._get_last_occurrence(matching_entries),
                    "sample_entries": matching_entries[:3],  # Include sample entries
                    "total_entries": len(matching_entries)
                }
                
                patterns.append(pattern)
        
        return patterns
    
    def _detect_temporal_patterns(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns based on temporal clustering of errors."""
        error_entries = [entry for entry in log_entries if entry.get("is_error", False)]
        
        if len(error_entries) < 3:
            return []
        
        # Group errors by time windows
        time_windows = defaultdict(list)
        
        for entry in error_entries:
            timestamp_str = entry.get("timestamp")
            if timestamp_str:
                try:
                    # Simple timestamp parsing (adjust as needed)
                    timestamp = self._parse_timestamp(timestamp_str)
                    if timestamp:
                        window_key = self._get_time_window_key(timestamp)
                        time_windows[window_key].append(entry)
                except Exception as e:
                    logging.debug(f"Failed to parse timestamp {timestamp_str}: {e}")
                    continue
        
        patterns = []
        for window_key, entries in time_windows.items():
            if len(entries) >= self.min_pattern_frequency:
                pattern = {
                    "type": "temporal_clustering",
                    "pattern_id": f"temp_{hash(window_key) % 10000:04d}",
                    "description": f"Error burst in time window (count: {len(entries)})",
                    "time_window": window_key,
                    "error_count": len(entries),
                    "severity": self._assess_temporal_severity(len(entries)),
                    "affected_components": list(set(
                        entry.get("component") for entry in entries 
                        if entry.get("component")
                    )),
                    "error_types": list(set(
                        entry.get("message", "")[:100] for entry in entries
                    ))[:5],  # Top 5 error types
                    "sample_entries": entries[:3]
                }
                
                patterns.append(pattern)
        
        return patterns
    
    def _detect_component_patterns(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns specific to components/services."""
        error_entries = [entry for entry in log_entries if entry.get("is_error", False)]
        
        # Group by component
        component_errors = defaultdict(list)
        for entry in error_entries:
            component = entry.get("component")
            if component:
                component_errors[component].append(entry)
        
        patterns = []
        for component, entries in component_errors.items():
            if len(entries) >= self.min_pattern_frequency:
                # Analyze error types within this component
                error_types = Counter(
                    entry.get("message", "")[:100] for entry in entries
                )
                
                pattern = {
                    "type": "component_specific",
                    "pattern_id": f"comp_{hash(component) % 10000:04d}",
                    "description": f"High error rate in component: {component}",
                    "component": component,
                    "error_count": len(entries),
                    "severity": self._assess_component_severity(len(entries), component),
                    "top_error_types": dict(error_types.most_common(5)),
                    "error_rate": len(entries) / len(log_entries) * 100,
                    "first_occurrence": self._get_first_occurrence(entries),
                    "last_occurrence": self._get_last_occurrence(entries),
                    "sample_entries": entries[:3]
                }
                
                patterns.append(pattern)
        
        return patterns
    
    def _detect_error_sequences(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect recurring sequences of errors."""
        error_entries = [entry for entry in log_entries if entry.get("is_error", False)]
        
        if len(error_entries) < 3:
            return []
        
        # Look for sequences of 2-3 errors
        sequences = []
        
        for i in range(len(error_entries) - 2):
            sequence = [
                error_entries[i].get("message", "")[:50],
                error_entries[i + 1].get("message", "")[:50],
                error_entries[i + 2].get("message", "")[:50]
            ]
            sequences.append(tuple(sequence))
        
        # Count sequence frequencies
        sequence_counts = Counter(sequences)
        
        patterns = []
        for sequence, count in sequence_counts.items():
            if count >= 2:  # Lower threshold for sequences
                pattern = {
                    "type": "error_sequence",
                    "pattern_id": f"seq_{hash(sequence) % 10000:04d}",
                    "description": f"Recurring error sequence (frequency: {count})",
                    "sequence": list(sequence),
                    "frequency": count,
                    "severity": "medium" if count >= 3 else "low"
                }
                
                patterns.append(pattern)
        
        return patterns
    
    def _detect_regex_patterns(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns using predefined regex patterns."""
        error_entries = [entry for entry in log_entries if entry.get("is_error", False)]
        
        patterns = []
        
        for pattern_name, regex_pattern in self.error_patterns.items():
            matching_entries = []
            
            for entry in error_entries:
                message = entry.get("message", "")
                error_details = entry.get("error", "")
                
                # Check both message and error fields
                text_to_check = f"{message} {error_details}".lower()
                
                if re.search(regex_pattern, text_to_check, re.IGNORECASE):
                    matching_entries.append(entry)
            
            if len(matching_entries) >= self.min_pattern_frequency:
                pattern = {
                    "type": "regex_pattern",
                    "pattern_id": f"regex_{pattern_name}",
                    "description": f"Pattern detected: {pattern_name}",
                    "pattern_name": pattern_name,
                    "regex": regex_pattern,
                    "match_count": len(matching_entries),
                    "severity": self._assess_regex_pattern_severity(pattern_name, len(matching_entries)),
                    "affected_components": list(set(
                        entry.get("component") for entry in matching_entries 
                        if entry.get("component")
                    )),
                    "first_occurrence": self._get_first_occurrence(matching_entries),
                    "last_occurrence": self._get_last_occurrence(matching_entries),
                    "sample_entries": matching_entries[:3]
                }
                
                patterns.append(pattern)
        
        return patterns
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object."""
        # Common timestamp formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ", 
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _get_time_window_key(self, timestamp: datetime) -> str:
        """Get time window key for temporal grouping."""
        # Round to nearest time window
        window_minutes = self.time_window_minutes
        rounded_minutes = (timestamp.minute // window_minutes) * window_minutes
        
        window_start = timestamp.replace(minute=rounded_minutes, second=0, microsecond=0)
        return window_start.strftime("%Y-%m-%d %H:%M")
    
    def _assess_severity(self, frequency: int, total_entries: int) -> str:
        """Assess severity based on frequency and total entries."""
        error_rate = frequency / total_entries * 100
        
        if error_rate > 10 or frequency > 20:
            return "critical"
        elif error_rate > 5 or frequency > 10:
            return "high"
        elif error_rate > 1 or frequency > 5:
            return "medium"
        else:
            return "low"
    
    def _assess_temporal_severity(self, error_count: int) -> str:
        """Assess severity for temporal clustering."""
        if error_count > 15:
            return "critical"
        elif error_count > 10:
            return "high"
        elif error_count > 5:
            return "medium"
        else:
            return "low"
    
    def _assess_component_severity(self, error_count: int, component: str) -> str:
        """Assess severity for component-specific patterns."""
        # Critical components get higher severity
        critical_components = ["database", "auth", "payment", "security"]
        
        base_severity = self._assess_temporal_severity(error_count)
        
        if any(critical in component.lower() for critical in critical_components):
            if base_severity == "medium":
                return "high"
            elif base_severity == "low":
                return "medium"
        
        return base_severity
    
    def _assess_regex_pattern_severity(self, pattern_name: str, match_count: int) -> str:
        """Assess severity for regex patterns."""
        critical_patterns = ["out_of_memory", "database_error", "authentication_failure"]
        high_patterns = ["connection_refused", "service_unavailable", "startup_failure"]
        
        base_severity = self._assess_temporal_severity(match_count)
        
        if pattern_name in critical_patterns:
            if base_severity in ["low", "medium"]:
                return "high"
            elif base_severity == "high":
                return "critical"
        elif pattern_name in high_patterns:
            if base_severity == "low":
                return "medium"
        
        return base_severity
    
    def _get_first_occurrence(self, entries: List[Dict[str, Any]]) -> str:
        """Get first occurrence timestamp from entries."""
        timestamps = [entry.get("timestamp") for entry in entries if entry.get("timestamp")]
        return min(timestamps) if timestamps else "unknown"
    
    def _get_last_occurrence(self, entries: List[Dict[str, Any]]) -> str:
        """Get last occurrence timestamp from entries."""
        timestamps = [entry.get("timestamp") for entry in entries if entry.get("timestamp")]
        return max(timestamps) if timestamps else "unknown"
    
    def get_pattern_summary(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics for detected patterns."""
        if not patterns:
            return {"total_patterns": 0}
        
        severity_counts = Counter(pattern.get("severity", "unknown") for pattern in patterns)
        type_counts = Counter(pattern.get("type", "unknown") for pattern in patterns)
        
        return {
            "total_patterns": len(patterns),
            "by_severity": dict(severity_counts),
            "by_type": dict(type_counts),
            "critical_patterns": len([p for p in patterns if p.get("severity") == "critical"]),
            "high_priority_patterns": len([p for p in patterns if p.get("severity") in ["critical", "high"]])
        }
