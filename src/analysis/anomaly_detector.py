"""
Anomaly detection for AI Driven Realtime Log Analyser
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import re

# Import ML libraries with fallback
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.feature_extraction.text import TfidfVectorizer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from core.models import LogEntry

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in log patterns and behavior
    
    Uses multiple approaches:
    1. Statistical anomalies (frequency-based)
    2. Pattern-based anomalies (unusual messages)
    3. Time-series anomalies (unusual timing patterns)
    4. ML-based anomalies (Isolation Forest)
    """
    
    def __init__(self):
        self.baseline_stats = {}
        self.normal_patterns = set()
        self.time_series_model = None
        
        # Anomaly thresholds
        self.frequency_threshold = 3.0  # Standard deviations
        self.pattern_similarity_threshold = 0.8
        self.time_window_minutes = 5

    async def detect_anomalies(self, entries: List[LogEntry]) -> List[Dict]:
        """
        Detect various types of anomalies in log entries
        
        Args:
            entries: List of log entries to analyze
            
        Returns:
            List of detected anomalies with metadata
        """
        logger.info(f"🔍 Detecting anomalies in {len(entries)} log entries...")
        
        if len(entries) < 10:
            logger.warning("Insufficient data for anomaly detection")
            return []
        
        anomalies = []
        
        # Detect frequency anomalies
        freq_anomalies = await self._detect_frequency_anomalies(entries)
        anomalies.extend(freq_anomalies)
        
        # Detect pattern anomalies
        pattern_anomalies = await self._detect_pattern_anomalies(entries)
        anomalies.extend(pattern_anomalies)
        
        # Detect temporal anomalies
        temporal_anomalies = await self._detect_temporal_anomalies(entries)
        anomalies.extend(temporal_anomalies)
        
        # Detect ML-based anomalies if available
        if ML_AVAILABLE and len(entries) > 50:
            ml_anomalies = await self._detect_ml_anomalies(entries)
            anomalies.extend(ml_anomalies)
        
        # Sort by severity/confidence
        anomalies.sort(key=lambda x: x.get('severity_score', 0), reverse=True)
        
        logger.info(f"🚨 Detected {len(anomalies)} anomalies")
        
        return anomalies

    async def _detect_frequency_anomalies(self, entries: List[LogEntry]) -> List[Dict]:
        """Detect anomalies based on message frequency"""
        anomalies = []
        
        # Group messages by normalized content
        message_counts = defaultdict(int)
        message_examples = {}
        
        for entry in entries:
            normalized = self._normalize_message(entry.message)
            message_counts[normalized] += 1
            if normalized not in message_examples:
                message_examples[normalized] = entry
        
        if len(message_counts) < 3:
            return anomalies
        
        # Calculate statistics
        counts = list(message_counts.values())
        mean_count = np.mean(counts)
        std_count = np.std(counts)
        
        if std_count == 0:
            return anomalies
        
        # Find anomalous frequencies
        for normalized_msg, count in message_counts.items():
            z_score = abs(count - mean_count) / std_count
            
            if z_score > self.frequency_threshold:
                severity = "HIGH" if z_score > 5.0 else "MEDIUM"
                anomaly_type = "high_frequency" if count > mean_count else "low_frequency"
                
                anomalies.append({
                    "type": "frequency_anomaly",
                    "subtype": anomaly_type,
                    "message": message_examples[normalized_msg].message,
                    "normalized_message": normalized_msg,
                    "count": count,
                    "expected_count": mean_count,
                    "z_score": z_score,
                    "severity": severity,
                    "severity_score": z_score,
                    "timestamp": message_examples[normalized_msg].timestamp,
                    "component": message_examples[normalized_msg].component
                })
        
        return anomalies

    async def _detect_pattern_anomalies(self, entries: List[LogEntry]) -> List[Dict]:
        """Detect anomalies based on unusual message patterns"""
        anomalies = []
        
        # Group by component for pattern analysis
        component_messages = defaultdict(list)
        
        for entry in entries:
            component = entry.component or "UNKNOWN"
            component_messages[component].append(entry)
        
        for component, comp_entries in component_messages.items():
            if len(comp_entries) < 5:
                continue
            
            # Analyze message patterns for this component
            normal_patterns = self._extract_normal_patterns(comp_entries)
            
            for entry in comp_entries:
                if entry.level in ["ERROR", "WARN"]:
                    similarity = self._calculate_pattern_similarity(
                        entry.message, normal_patterns
                    )
                    
                    if similarity < self.pattern_similarity_threshold:
                        anomalies.append({
                            "type": "pattern_anomaly",
                            "subtype": "unusual_message",
                            "message": entry.message,
                            "component": component,
                            "similarity_score": similarity,
                            "severity": "HIGH" if similarity < 0.3 else "MEDIUM",
                            "severity_score": 1.0 - similarity,
                            "timestamp": entry.timestamp,
                            "level": entry.level
                        })
        
        return anomalies

    async def _detect_temporal_anomalies(self, entries: List[LogEntry]) -> List[Dict]:
        """Detect anomalies based on timing patterns"""
        anomalies = []
        
        # Filter entries with timestamps
        timestamped_entries = [e for e in entries if e.timestamp]
        
        if len(timestamped_entries) < 10:
            return anomalies
        
        # Sort by timestamp
        timestamped_entries.sort(key=lambda x: x.timestamp)
        
        # Detect burst patterns (many errors in short time)
        error_entries = [e for e in timestamped_entries if e.level == "ERROR"]
        
        if len(error_entries) >= 5:
            burst_anomalies = self._detect_error_bursts(error_entries)
            anomalies.extend(burst_anomalies)
        
        # Detect unusual quiet periods
        quiet_anomalies = self._detect_quiet_periods(timestamped_entries)
        anomalies.extend(quiet_anomalies)
        
        return anomalies

    def _detect_error_bursts(self, error_entries: List[LogEntry]) -> List[Dict]:
        """Detect bursts of errors in short time periods"""
        anomalies = []
        window_size = timedelta(minutes=self.time_window_minutes)
        
        for i, entry in enumerate(error_entries):
            window_start = entry.timestamp
            window_end = window_start + window_size
            
            # Count errors in this window
            errors_in_window = 0
            window_entries = []
            
            for j in range(i, len(error_entries)):
                if error_entries[j].timestamp <= window_end:
                    errors_in_window += 1
                    window_entries.append(error_entries[j])
                else:
                    break
            
            # Detect burst (configurable threshold)
            if errors_in_window >= 10:  # 10+ errors in 5 minutes
                anomalies.append({
                    "type": "temporal_anomaly",
                    "subtype": "error_burst",
                    "start_time": window_start,
                    "end_time": window_end,
                    "error_count": errors_in_window,
                    "severity": "HIGH" if errors_in_window >= 20 else "MEDIUM",
                    "severity_score": min(errors_in_window / 10.0, 5.0),
                    "sample_messages": [e.message for e in window_entries[:3]],
                    "components": list(set(e.component for e in window_entries if e.component))
                })
        
        return anomalies

    def _detect_quiet_periods(self, entries: List[LogEntry]) -> List[Dict]:
        """Detect unusually quiet periods"""
        if len(entries) < 20:
            return []
        
        anomalies = []
        
        # Calculate normal activity intervals
        intervals = []
        for i in range(1, len(entries)):
            interval = (entries[i].timestamp - entries[i-1].timestamp).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return []
        
        # Find unusually long gaps
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        if std_interval == 0:
            return []
        
        threshold = mean_interval + 3 * std_interval
        
        for i, interval in enumerate(intervals):
            if interval > threshold and interval > 300:  # At least 5 minutes
                anomalies.append({
                    "type": "temporal_anomaly",
                    "subtype": "quiet_period",
                    "duration_seconds": interval,
                    "expected_duration": mean_interval,
                    "start_time": entries[i].timestamp,
                    "end_time": entries[i+1].timestamp,
                    "severity": "MEDIUM" if interval > 3600 else "LOW",  # 1 hour threshold
                    "severity_score": min(interval / 3600.0, 2.0)
                })
        
        return anomalies

    async def _detect_ml_anomalies(self, entries: List[LogEntry]) -> List[Dict]:
        """Detect anomalies using ML-based approaches"""
        if not ML_AVAILABLE:
            return []
        
        try:
            # Prepare features for anomaly detection
            features = await self._extract_features(entries)
            
            if len(features) < 10:
                return []
            
            # Use Isolation Forest
            isolation_forest = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42
            )
            
            anomaly_scores = isolation_forest.fit_predict(features)
            anomaly_probs = isolation_forest.score_samples(features)
            
            anomalies = []
            for i, (entry, score, prob) in enumerate(zip(entries, anomaly_scores, anomaly_probs)):
                if score == -1:  # Anomaly detected
                    anomalies.append({
                        "type": "ml_anomaly",
                        "subtype": "isolation_forest",
                        "message": entry.message,
                        "component": entry.component,
                        "level": entry.level,
                        "timestamp": entry.timestamp,
                        "anomaly_score": prob,
                        "severity": "HIGH" if prob < -0.5 else "MEDIUM",
                        "severity_score": abs(prob)
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"ML anomaly detection failed: {e}")
            return []

    async def _extract_features(self, entries: List[LogEntry]) -> np.ndarray:
        """Extract numerical features for ML anomaly detection"""
        features = []
        
        for entry in entries:
            feature_vector = [
                len(entry.message),  # Message length
                entry.message.count(' '),  # Word count
                entry.message.count('\n'),  # Line count
                len(re.findall(r'\d+', entry.message)),  # Number count
                1 if entry.level == "ERROR" else 0,  # Is error
                1 if entry.level == "WARN" else 0,   # Is warning
            ]
            
            # Add hour of day if timestamp available
            if entry.timestamp:
                feature_vector.append(entry.timestamp.hour)
                feature_vector.append(entry.timestamp.weekday())
            else:
                feature_vector.extend([0, 0])
            
            features.append(feature_vector)
        
        return np.array(features)

    def _normalize_message(self, message: str) -> str:
        """Normalize message for pattern comparison"""
        # Remove timestamps, numbers, and IDs
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}', '', message)
        normalized = re.sub(r'\d+', 'N', normalized)
        normalized = re.sub(r'[a-f0-9]{8,}', 'ID', normalized)
        normalized = ' '.join(normalized.split())
        return normalized.lower()

    def _extract_normal_patterns(self, entries: List[LogEntry]) -> List[str]:
        """Extract normal message patterns from entries"""
        # Get INFO level messages as baseline for normal patterns
        normal_entries = [e for e in entries if e.level == "INFO"]
        
        if len(normal_entries) < 3:
            normal_entries = entries  # Fall back to all entries
        
        patterns = []
        for entry in normal_entries:
            normalized = self._normalize_message(entry.message)
            patterns.append(normalized)
        
        return patterns

    def _calculate_pattern_similarity(self, message: str, normal_patterns: List[str]) -> float:
        """Calculate similarity of message to normal patterns"""
        if not normal_patterns:
            return 0.5  # Neutral similarity
        
        normalized_msg = self._normalize_message(message)
        
        # Calculate similarity using simple word overlap
        msg_words = set(normalized_msg.split())
        
        max_similarity = 0.0
        for pattern in normal_patterns:
            pattern_words = set(pattern.split())
            
            if not pattern_words:
                continue
            
            # Jaccard similarity
            intersection = len(msg_words & pattern_words)
            union = len(msg_words | pattern_words)
            
            if union > 0:
                similarity = intersection / union
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity

    async def get_anomaly_summary(self, anomalies: List[Dict]) -> Dict:
        """Get summary statistics of detected anomalies"""
        if not anomalies:
            return {"total": 0}
        
        summary = {
            "total": len(anomalies),
            "by_type": defaultdict(int),
            "by_severity": defaultdict(int),
            "by_component": defaultdict(int),
            "high_severity_count": 0,
            "avg_severity_score": 0.0
        }
        
        total_severity_score = 0.0
        
        for anomaly in anomalies:
            summary["by_type"][anomaly.get("type", "unknown")] += 1
            summary["by_severity"][anomaly.get("severity", "UNKNOWN")] += 1
            
            if anomaly.get("component"):
                summary["by_component"][anomaly["component"]] += 1
            
            if anomaly.get("severity") == "HIGH":
                summary["high_severity_count"] += 1
            
            total_severity_score += anomaly.get("severity_score", 0.0)
        
        summary["avg_severity_score"] = total_severity_score / len(anomalies)
        
        # Convert defaultdicts to regular dicts
        summary["by_type"] = dict(summary["by_type"])
        summary["by_severity"] = dict(summary["by_severity"])
        summary["by_component"] = dict(summary["by_component"])
        
        return summary
