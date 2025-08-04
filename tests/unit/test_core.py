"""
Unit Tests for Smart Log Analyzer Core Components

Tests for log parser, pattern detector, and other core functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# Import modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.core.log_parser import LogParser
from src.core.pattern_detector import PatternDetector
from src.core.component_filter import ComponentFilter
from src.utils.config import Config
from src.utils.helpers import *


class TestLogParser:
    """Test cases for LogParser class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
    
    @pytest.fixture
    def log_parser(self, config):
        """Create LogParser instance."""
        return LogParser(config)
    
    @pytest.fixture
    def sample_json_log(self):
        """Create sample JSON log content."""
        return [
            '{"message": "Starting application", "level": "info", "timestamp": "2025-01-15T10:00:00Z"}',
            '{"message": "Database connection failed", "level": "error", "timestamp": "2025-01-15T10:01:00Z", "error": "connection refused"}',
            '{"message": "Retry connection", "level": "warn", "timestamp": "2025-01-15T10:01:30Z"}',
            '{"message": "Application ready", "level": "info", "timestamp": "2025-01-15T10:02:00Z"}'
        ]
    
    def test_parse_json_log(self, log_parser, sample_json_log):
        """Test parsing JSON log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write('\n'.join(sample_json_log))
            f.flush()
            
            entries = log_parser.parse_file(f.name, "json")
            
            assert len(entries) == 4
            assert entries[0]["message"] == "Starting application"
            assert entries[1]["is_error"] == True
            assert entries[2]["is_warning"] == True
            assert entries[3]["level"] == "info"
            
            # Cleanup
            Path(f.name).unlink()
    
    def test_error_detection(self, log_parser):
        """Test error detection in log entries."""
        error_entry = {
            "message": "Database connection failed",
            "level": "error",
            "error": "connection refused"
        }
        
        enhanced_entry = log_parser._enhance_json_entry(error_entry, 1, Path("test.log"))
        
        assert enhanced_entry["is_error"] == True
        assert enhanced_entry["is_warning"] == False
    
    def test_component_extraction(self, log_parser):
        """Test component extraction from log entries."""
        entry = {
            "message": "Starting virtualization-aggregator-kafka service"
        }
        
        component = log_parser._extract_component(entry)
        assert component == "kafka"
    
    def test_statistics(self, log_parser, sample_json_log):
        """Test log statistics calculation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write('\n'.join(sample_json_log))
            f.flush()
            
            entries = log_parser.parse_file(f.name, "json")
            stats = log_parser.get_statistics(entries)
            
            assert stats["total"] == 4
            assert stats["errors"] == 1
            assert stats["warnings"] == 1
            assert stats["info"] == 2
            assert stats["error_rate"] == 25.0
            
            # Cleanup
            Path(f.name).unlink()


class TestPatternDetector:
    """Test cases for PatternDetector class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
    
    @pytest.fixture
    def pattern_detector(self, config):
        """Create PatternDetector instance."""
        return PatternDetector(config)
    
    @pytest.fixture
    def sample_log_entries(self):
        """Create sample log entries for testing."""
        return [
            {
                "message": "Database connection failed",
                "is_error": True,
                "component": "postgres",
                "timestamp": "2025-01-15T10:00:00Z"
            },
            {
                "message": "Database connection failed",
                "is_error": True,
                "component": "postgres",
                "timestamp": "2025-01-15T10:01:00Z"
            },
            {
                "message": "Database connection failed",
                "is_error": True,
                "component": "postgres",
                "timestamp": "2025-01-15T10:02:00Z"
            },
            {
                "message": "Service timeout",
                "is_error": True,
                "component": "kafka",
                "timestamp": "2025-01-15T10:03:00Z"
            }
        ]
    
    def test_error_frequency_patterns(self, pattern_detector, sample_log_entries):
        """Test detection of error frequency patterns."""
        patterns = pattern_detector._detect_error_frequency_patterns(sample_log_entries)
        
        assert len(patterns) >= 1
        db_pattern = next((p for p in patterns if "Database connection failed" in p["error_message"]), None)
        assert db_pattern is not None
        assert db_pattern["frequency"] == 3
        assert db_pattern["type"] == "error_frequency"
    
    def test_component_patterns(self, pattern_detector, sample_log_entries):
        """Test detection of component-specific patterns."""
        patterns = pattern_detector._detect_component_patterns(sample_log_entries)
        
        postgres_pattern = next((p for p in patterns if p["component"] == "postgres"), None)
        assert postgres_pattern is not None
        assert postgres_pattern["error_count"] == 3
        assert postgres_pattern["type"] == "component_specific"
    
    def test_regex_patterns(self, pattern_detector, sample_log_entries):
        """Test regex-based pattern detection."""
        patterns = pattern_detector._detect_regex_patterns(sample_log_entries)
        
        # Should detect database_error pattern
        db_pattern = next((p for p in patterns if p["pattern_name"] == "database_error"), None)
        assert db_pattern is not None
        assert db_pattern["match_count"] == 3
    
    def test_severity_assessment(self, pattern_detector):
        """Test severity assessment for patterns."""
        # High frequency should get high severity
        high_severity = pattern_detector._assess_severity(15, 100)
        assert high_severity in ["high", "critical"]
        
        # Low frequency should get low severity
        low_severity = pattern_detector._assess_severity(2, 100)
        assert low_severity in ["low", "medium"]


class TestComponentFilter:
    """Test cases for ComponentFilter class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
    
    @pytest.fixture
    def component_filter(self, config):
        """Create ComponentFilter instance."""
        return ComponentFilter(config)
    
    @pytest.fixture
    def sample_log_entries(self):
        """Create sample log entries for testing."""
        return [
            {
                "message": "Kafka service started",
                "component": "kafka",
                "is_error": False
            },
            {
                "message": "Database connection failed",
                "component": "postgres",
                "is_error": True
            },
            {
                "message": "API request processed",
                "component": "rest",
                "is_error": False
            },
            {
                "message": "Database timeout",
                "component": "postgres",
                "is_error": True
            }
        ]
    
    def test_filter_by_component(self, component_filter, sample_log_entries):
        """Test filtering by specific component."""
        postgres_entries = component_filter.filter_by_component(sample_log_entries, "postgres")
        
        assert len(postgres_entries) == 2
        assert all(entry["component"] == "postgres" for entry in postgres_entries)
    
    def test_filter_by_severity(self, component_filter, sample_log_entries):
        """Test filtering by severity level."""
        error_entries = component_filter.filter_by_severity(sample_log_entries, "error")
        
        assert len(error_entries) == 2
        assert all(entry["is_error"] for entry in error_entries)
    
    def test_group_by_component(self, component_filter, sample_log_entries):
        """Test grouping entries by component."""
        groups = component_filter.group_by_component(sample_log_entries)
        
        assert "postgres" in groups
        assert "kafka" in groups
        assert "rest" in groups
        assert len(groups["postgres"]) == 2
        assert len(groups["kafka"]) == 1
        assert len(groups["rest"]) == 1
    
    def test_component_statistics(self, component_filter, sample_log_entries):
        """Test component statistics calculation."""
        stats = component_filter.get_component_statistics(sample_log_entries)
        
        assert "postgres" in stats
        assert stats["postgres"]["total_entries"] == 2
        assert stats["postgres"]["error_count"] == 2
        assert stats["postgres"]["error_rate"] == 100.0


class TestHelpers:
    """Test cases for helper utilities."""
    
    def test_hash_string(self):
        """Test string hashing."""
        text = "test string"
        hash_md5 = hash_string(text, "md5")
        hash_sha256 = hash_string(text, "sha256")
        
        assert len(hash_md5) == 32
        assert len(hash_sha256) == 64
        assert hash_md5 != hash_sha256
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        unsafe_name = 'file<name>with:invalid"chars'
        safe_name = sanitize_filename(unsafe_name)
        
        assert '<' not in safe_name
        assert '>' not in safe_name
        assert ':' not in safe_name
        assert '"' not in safe_name
    
    def test_safe_get_nested(self):
        """Test safe nested dictionary access."""
        data = {
            "level1": {
                "level2": {
                    "value": "found"
                }
            }
        }
        
        # Existing path
        value = safe_get_nested(data, "level1.level2.value")
        assert value == "found"
        
        # Non-existing path
        value = safe_get_nested(data, "level1.nonexistent.value", default="default")
        assert value == "default"
    
    def test_extract_timestamp_components(self):
        """Test timestamp component extraction."""
        timestamp = "2025-01-15T10:30:45.123Z"
        components = extract_timestamp_components(timestamp)
        
        assert components["valid"] == True
        assert components["year"] == 2025
        assert components["month"] == 1
        assert components["day"] == 15
        assert components["hour"] == 10
        assert components["minute"] == 30
        assert components["second"] == 45
    
    def test_format_bytes(self):
        """Test byte formatting."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1024 * 1024) == "1.0 MB"
        assert format_bytes(1024 * 1024 * 1024) == "1.0 GB"
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(0.5) == "500ms"
        assert format_duration(30) == "30.0s"
        assert format_duration(90) == "1.5m"
        assert format_duration(3600) == "1.0h"
    
    def test_validate_json_string(self):
        """Test JSON string validation."""
        valid_json = '{"key": "value"}'
        invalid_json = '{"key": value}'
        
        is_valid, error = validate_json_string(valid_json)
        assert is_valid == True
        assert error is None
        
        is_valid, error = validate_json_string(invalid_json)
        assert is_valid == False
        assert error is not None
    
    def test_chunk_list(self):
        """Test list chunking."""
        data = list(range(10))
        chunks = chunk_list(data, 3)
        
        assert len(chunks) == 4
        assert chunks[0] == [0, 1, 2]
        assert chunks[1] == [3, 4, 5]
        assert chunks[3] == [9]
    
    def test_calculate_text_similarity(self):
        """Test text similarity calculation."""
        text1 = "database connection failed"
        text2 = "database connection error"
        text3 = "service started successfully"
        
        similarity_high = calculate_text_similarity(text1, text2)
        similarity_low = calculate_text_similarity(text1, text3)
        
        assert similarity_high > similarity_low
        assert 0 <= similarity_high <= 1
        assert 0 <= similarity_low <= 1
    
    def test_mask_sensitive_data(self):
        """Test sensitive data masking."""
        text = "User email: john@example.com and IP: 192.168.1.1"
        masked = mask_sensitive_data(text)
        
        assert "john@example.com" not in masked
        assert "192.168.1.1" not in masked
        assert "[EMAIL]" in masked
        assert "[IP]" in masked


class TestTimer:
    """Test cases for Timer utility."""
    
    def test_timer_context_manager(self):
        """Test Timer as context manager."""
        import time
        
        with Timer("test_operation") as timer:
            time.sleep(0.1)  # Sleep for 100ms
        
        assert timer.get_duration() >= 0.1
        assert "ms" in timer.get_formatted_duration() or "s" in timer.get_formatted_duration()


class TestDataCache:
    """Test cases for DataCache utility."""
    
    def test_cache_operations(self):
        """Test basic cache operations."""
        cache = DataCache(default_ttl=1)  # 1 second TTL
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test non-existent key
        assert cache.get("nonexistent") is None
        
        # Test TTL expiration
        import time
        cache.set("short_lived", "value", ttl=0.1)  # 100ms TTL
        time.sleep(0.2)
        assert cache.get("short_lived") is None
        
        # Test clear
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key2") is None
        assert cache.size() == 0


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
