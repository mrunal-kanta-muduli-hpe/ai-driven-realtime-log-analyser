"""
Integration Tests for Smart Log Analyzer

Tests for end-to-end workflows and integration between components.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

# Import modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.main import main
from src.core.log_parser import LogParser
from src.core.pattern_detector import PatternDetector
from src.core.ml_engine import MLEngine
from src.integrations.jira_client import JiraClient
from src.integrations.defect_generator import DefectGenerator
from src.utils.config import Config


class TestEndToEndWorkflow:
    """Test complete log analysis workflow."""
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_log_file(self, temp_directory):
        """Create sample log file."""
        log_file = Path(temp_directory) / "test.log"
        log_entries = [
            '{"message": "Starting virtualization-aggregator service", "level": "info", "timestamp": "2025-01-15T10:00:00Z", "component": "aggregator"}',
            '{"message": "Database connection failed", "level": "error", "timestamp": "2025-01-15T10:01:00Z", "component": "postgres", "error": "connection refused"}',
            '{"message": "Database connection failed", "level": "error", "timestamp": "2025-01-15T10:02:00Z", "component": "postgres", "error": "connection refused"}',
            '{"message": "Database connection failed", "level": "error", "timestamp": "2025-01-15T10:03:00Z", "component": "postgres", "error": "connection refused"}',
            '{"message": "Kafka producer timeout", "level": "error", "timestamp": "2025-01-15T10:04:00Z", "component": "kafka", "error": "timeout"}',
            '{"message": "API request processed", "level": "info", "timestamp": "2025-01-15T10:05:00Z", "component": "rest"}',
            '{"message": "Memory usage high", "level": "warn", "timestamp": "2025-01-15T10:06:00Z", "component": "system"}',
        ]
        
        with open(log_file, 'w') as f:
            f.write('\n'.join(log_entries))
        
        return str(log_file)
    
    @pytest.fixture
    def config(self, temp_directory):
        """Create test configuration."""
        config = Config()
        config.config_data['output']['output_dir'] = temp_directory
        return config
    
    def test_full_analysis_workflow(self, config, sample_log_file, temp_directory):
        """Test complete log analysis workflow."""
        # Initialize components
        log_parser = LogParser(config)
        pattern_detector = PatternDetector(config)
        ml_engine = MLEngine(config)
        defect_generator = DefectGenerator(config)
        
        # Step 1: Parse logs
        entries = log_parser.parse_file(sample_log_file, "json")
        assert len(entries) == 7
        assert sum(1 for e in entries if e["is_error"]) == 4
        
        # Step 2: Detect patterns
        patterns = pattern_detector.detect_patterns(entries)
        assert len(patterns) > 0
        
        # Find database connection pattern
        db_pattern = next((p for p in patterns if "Database connection failed" in p["error_message"]), None)
        assert db_pattern is not None
        assert db_pattern["frequency"] == 3
        
        # Step 3: Train and classify with ML
        ml_engine.train_models(entries)
        
        # Get error entries for classification
        error_entries = [e for e in entries if e["is_error"]]
        classifications = ml_engine.classify_errors(error_entries)
        assert len(classifications) == 4
        
        # Detect anomalies
        anomalies = ml_engine.detect_anomalies(entries)
        assert isinstance(anomalies, list)
        
        # Step 4: Generate defects
        defects = defect_generator.generate_defects(patterns, entries)
        assert len(defects) > 0
        
        # Check defect structure
        assert all("summary" in d for d in defects)
        assert all("description" in d for d in defects)
        assert all("priority" in d for d in defects)
    
    def test_component_filtering_workflow(self, config, sample_log_file):
        """Test workflow with component filtering."""
        from src.core.component_filter import ComponentFilter
        
        log_parser = LogParser(config)
        component_filter = ComponentFilter(config)
        pattern_detector = PatternDetector(config)
        
        # Parse all entries
        all_entries = log_parser.parse_file(sample_log_file, "json")
        
        # Filter for postgres component only
        postgres_entries = component_filter.filter_by_component(all_entries, "postgres")
        assert len(postgres_entries) == 3
        assert all(e["component"] == "postgres" for e in postgres_entries)
        
        # Detect patterns in filtered data
        patterns = pattern_detector.detect_patterns(postgres_entries)
        
        # Should find the database connection pattern
        db_pattern = next((p for p in patterns if "Database connection failed" in p["error_message"]), None)
        assert db_pattern is not None
        assert db_pattern["frequency"] == 3
    
    @patch('src.main.sys.argv')
    def test_command_line_interface(self, mock_argv, sample_log_file, temp_directory):
        """Test command line interface."""
        # Mock command line arguments
        mock_argv.return_value = [
            'main.py',
            '--file', sample_log_file,
            '--format', 'json',
            '--output-dir', temp_directory,
            '--component', 'postgres'
        ]
        
        # This should run without errors
        # Note: In real test, we'd capture output and verify results
        try:
            # Would call main() here but need to mock sys.exit
            pass
        except SystemExit:
            pass  # Expected for CLI applications


class TestJiraIntegration:
    """Test Jira integration functionality."""
    
    @pytest.fixture
    def mock_jira_config(self):
        """Create mock Jira configuration."""
        return {
            'server': 'https://test.atlassian.net',
            'username': 'test@example.com',
            'api_token': 'test_token',
            'project_key': 'TEST'
        }
    
    @pytest.fixture
    def jira_client(self, mock_jira_config):
        """Create JiraClient instance with mock config."""
        return JiraClient(mock_jira_config)
    
    @pytest.fixture
    def sample_defect(self):
        """Create sample defect for testing."""
        return {
            'summary': 'Database Connection Error Pattern Detected',
            'description': 'Multiple database connection failures detected...',
            'priority': 'High',
            'component': 'postgres',
            'pattern_type': 'error_frequency',
            'frequency': 3,
            'first_occurrence': '2025-01-15T10:01:00Z',
            'last_occurrence': '2025-01-15T10:03:00Z'
        }
    
    @patch('requests.get')
    def test_jira_connection(self, mock_get, jira_client):
        """Test Jira connection testing."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'version': '8.20.0'}
        mock_get.return_value = mock_response
        
        result = jira_client.test_connection()
        assert result == True
        
        # Test failed connection
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = jira_client.test_connection()
        assert result == False
    
    @patch('requests.post')
    def test_jira_issue_creation(self, mock_post, jira_client, sample_defect):
        """Test Jira issue creation."""
        # Mock successful issue creation
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'key': 'TEST-123',
            'id': '12345',
            'self': 'https://test.atlassian.net/rest/api/2/issue/12345'
        }
        mock_post.return_value = mock_response
        
        result = jira_client.create_issue(sample_defect)
        
        assert result is not None
        assert result['key'] == 'TEST-123'
        assert result['success'] == True
        
        # Verify the request was made with correct data
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        request_data = json.loads(call_args[1]['data'])
        
        assert request_data['fields']['project']['key'] == 'TEST'
        assert 'Database Connection Error' in request_data['fields']['summary']
    
    @patch('requests.post')
    def test_jira_bulk_creation(self, mock_post, jira_client):
        """Test bulk issue creation."""
        # Mock successful bulk creation
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'issues': [
                {'key': 'TEST-123', 'id': '12345'},
                {'key': 'TEST-124', 'id': '12346'}
            ]
        }
        mock_post.return_value = mock_response
        
        defects = [
            {
                'summary': 'Database Error Pattern',
                'description': 'Error description 1',
                'priority': 'High',
                'component': 'postgres'
            },
            {
                'summary': 'Kafka Timeout Pattern',
                'description': 'Error description 2',
                'priority': 'Medium',
                'component': 'kafka'
            }
        ]
        
        results = jira_client.create_bulk_issues(defects)
        
        assert len(results) == 2
        assert all(r['success'] for r in results)
        assert results[0]['key'] == 'TEST-123'
        assert results[1]['key'] == 'TEST-124'


class TestMLIntegration:
    """Test machine learning integration."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
    
    @pytest.fixture
    def ml_engine(self, config):
        """Create MLEngine instance."""
        return MLEngine(config)
    
    @pytest.fixture
    def training_data(self):
        """Create training data for ML models."""
        return [
            {
                "message": "Database connection failed",
                "level": "error",
                "component": "postgres",
                "is_error": True,
                "timestamp": "2025-01-15T10:00:00Z"
            },
            {
                "message": "Database timeout",
                "level": "error",
                "component": "postgres",
                "is_error": True,
                "timestamp": "2025-01-15T10:01:00Z"
            },
            {
                "message": "Kafka producer error",
                "level": "error",
                "component": "kafka",
                "is_error": True,
                "timestamp": "2025-01-15T10:02:00Z"
            },
            {
                "message": "Service started successfully",
                "level": "info",
                "component": "aggregator",
                "is_error": False,
                "timestamp": "2025-01-15T10:03:00Z"
            },
            {
                "message": "API request processed",
                "level": "info",
                "component": "rest",
                "is_error": False,
                "timestamp": "2025-01-15T10:04:00Z"
            }
        ]
    
    def test_model_training(self, ml_engine, training_data):
        """Test ML model training."""
        # Train models
        result = ml_engine.train_models(training_data)
        
        assert result == True
        assert ml_engine.classifier is not None
        assert ml_engine.anomaly_detector is not None
        assert ml_engine.vectorizer is not None
    
    def test_error_classification(self, ml_engine, training_data):
        """Test error classification."""
        # Train first
        ml_engine.train_models(training_data)
        
        # Test classification
        test_errors = [e for e in training_data if e["is_error"]]
        classifications = ml_engine.classify_errors(test_errors)
        
        assert len(classifications) == 3
        assert all("predicted_category" in c for c in classifications)
        assert all("confidence" in c for c in classifications)
    
    def test_anomaly_detection(self, ml_engine, training_data):
        """Test anomaly detection."""
        # Train first
        ml_engine.train_models(training_data)
        
        # Test anomaly detection
        anomalies = ml_engine.detect_anomalies(training_data)
        
        assert isinstance(anomalies, list)
        # All entries should have anomaly scores
        for entry in training_data:
            assert "anomaly_score" in entry
    
    def test_model_persistence(self, ml_engine, training_data, tmp_path):
        """Test model saving and loading."""
        # Train models
        ml_engine.train_models(training_data)
        
        # Save models
        model_path = tmp_path / "test_models.pkl"
        result = ml_engine.save_models(str(model_path))
        assert result == True
        assert model_path.exists()
        
        # Create new ML engine and load models
        new_ml_engine = MLEngine(ml_engine.config)
        result = new_ml_engine.load_models(str(model_path))
        assert result == True
        assert new_ml_engine.classifier is not None
        
        # Test that loaded models work
        test_errors = [e for e in training_data if e["is_error"]]
        classifications = new_ml_engine.classify_errors(test_errors)
        assert len(classifications) == 3


class TestPerformance:
    """Test performance and scalability."""
    
    def test_large_log_processing(self, tmp_path):
        """Test processing of large log files."""
        import time
        
        # Create large log file (1000 entries)
        log_file = tmp_path / "large.log"
        entries = []
        for i in range(1000):
            entry = {
                "message": f"Test message {i}",
                "level": "error" if i % 10 == 0 else "info",
                "timestamp": f"2025-01-15T10:{i//60:02d}:{i%60:02d}Z",
                "component": f"component_{i % 5}"
            }
            entries.append(json.dumps(entry))
        
        with open(log_file, 'w') as f:
            f.write('\n'.join(entries))
        
        # Test parsing performance
        config = Config()
        log_parser = LogParser(config)
        
        start_time = time.time()
        parsed_entries = log_parser.parse_file(str(log_file), "json")
        parse_time = time.time() - start_time
        
        assert len(parsed_entries) == 1000
        assert parse_time < 5.0  # Should parse 1000 entries in under 5 seconds
    
    def test_pattern_detection_performance(self):
        """Test pattern detection performance."""
        import time
        
        # Create test data with patterns
        entries = []
        for i in range(500):
            if i % 50 == 0:
                # Create repeated error pattern
                entry = {
                    "message": "Database connection failed",
                    "is_error": True,
                    "component": "postgres",
                    "timestamp": f"2025-01-15T10:{i//60:02d}:{i%60:02d}Z"
                }
            else:
                entry = {
                    "message": f"Regular log entry {i}",
                    "is_error": False,
                    "component": f"service_{i % 3}",
                    "timestamp": f"2025-01-15T10:{i//60:02d}:{i%60:02d}Z"
                }
            entries.append(entry)
        
        config = Config()
        pattern_detector = PatternDetector(config)
        
        start_time = time.time()
        patterns = pattern_detector.detect_patterns(entries)
        detection_time = time.time() - start_time
        
        assert len(patterns) > 0
        assert detection_time < 10.0  # Should detect patterns in under 10 seconds


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
