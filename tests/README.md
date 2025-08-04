# Testing Framework for Smart Log Analyzer

This directory contains comprehensive tests for the Smart Log Analyzer project.

## Test Structure

```
tests/
├── unit/                          # Unit tests
│   └── test_core.py              # Core component tests
├── integration/                   # Integration tests  
│   └── test_integration.py       # End-to-end workflow tests
├── generate_test_data.py         # Test data generator
└── README.md                     # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual components in isolation
- Mock external dependencies
- Fast execution
- High coverage of edge cases

**Components tested:**
- `LogParser`: Log file parsing and error detection
- `PatternDetector`: Pattern recognition algorithms
- `ComponentFilter`: Component-based filtering
- `MLEngine`: Machine learning functionality
- `JiraClient`: Jira API integration
- `DefectGenerator`: Defect report generation
- Utility functions and helpers

### Integration Tests (`tests/integration/`)
- Test component interactions
- End-to-end workflows
- Real data processing
- Performance testing

**Workflows tested:**
- Complete log analysis pipeline
- Component filtering workflows
- ML model training and prediction
- Jira integration (with mocking)
- Large dataset processing

## Running Tests

### Quick Start

```bash
# Run all tests
./run_tests.sh

# Run specific test types
./run_tests.sh unit           # Unit tests only
./run_tests.sh integration   # Integration tests only
./run_tests.sh performance   # Performance tests only
./run_tests.sh quality       # Code quality checks
```

### Manual Test Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-html

# Run unit tests with coverage
python -m pytest tests/unit/ -v --cov=src --cov-report=html

# Run integration tests
python -m pytest tests/integration/ -v

# Run specific test file
python -m pytest tests/unit/test_core.py::TestLogParser -v

# Run tests with specific markers
python -m pytest -m "not slow" -v
```

## Test Data Generation

### Generate Test Logs

```bash
# Generate 1000 random log entries
python tests/generate_test_data.py

# Generate component-specific logs
python tests/generate_test_data.py --component kafka --entries 500 --output kafka_test.log

# Generate logs without anomalies
python tests/generate_test_data.py --no-anomalies --entries 2000
```

### Test Data Features

The test data generator creates realistic log data with:
- **Error Patterns**: Database failures, timeouts, connection issues
- **Component Logs**: Service-specific log entries
- **Burst Patterns**: Cascading failure simulation
- **Anomalies**: Unusual events for anomaly detection testing
- **Realistic Timestamps**: Chronological log sequences

## Test Configuration

### pytest.ini
- Test discovery patterns
- Coverage configuration
- Test markers for categorization
- Report formatting options

### Test Markers
- `unit`: Unit tests
- `integration`: Integration tests
- `slow`: Long-running tests
- `jira`: Tests requiring Jira connection

## Test Reports

After running tests, reports are generated in the `reports/` directory:

```
reports/
├── coverage/                 # HTML coverage report
│   └── index.html
├── unit_tests.html          # Unit test results
├── integration_tests.html   # Integration test results
├── performance_tests.html   # Performance test results
└── test_summary.md         # Overall test summary
```

## Mock Configuration

### Jira API Mocking
Integration tests mock Jira API calls to avoid requiring live credentials:

```python
@patch('requests.post')
def test_jira_issue_creation(self, mock_post, jira_client):
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'key': 'TEST-123'}
    mock_post.return_value = mock_response
    # Test logic here
```

### ML Model Mocking
Machine learning components can be tested without training:

```python
@patch('sklearn.ensemble.RandomForestClassifier')
def test_ml_classification(self, mock_classifier):
    # Test ML logic with mocked classifier
```

## Performance Testing

Performance tests validate:
- Large log file processing (1000+ entries)
- Pattern detection efficiency
- Memory usage optimization
- Response time requirements

Example performance expectations:
- Parse 1000 log entries in < 5 seconds
- Detect patterns in 500 entries in < 10 seconds
- ML training on 1000 entries in < 30 seconds

## Test Data Samples

### Sample Error Pattern
```json
{
  "timestamp": "2025-01-15T10:01:00Z",
  "level": "error", 
  "message": "Database connection failed",
  "component": "postgres",
  "error": "connection refused",
  "thread": "thread-3",
  "requestId": "req-1234"
}
```

### Sample Burst Pattern
Multiple related errors occurring in sequence:
```json
[
  {"message": "Database connection failed", "timestamp": "10:01:00Z"},
  {"message": "Database connection failed", "timestamp": "10:01:05Z"}, 
  {"message": "Database connection failed", "timestamp": "10:01:10Z"},
  {"message": "Database connection failed", "timestamp": "10:01:15Z"}
]
```

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests with JUnit XML output
python -m pytest --junitxml=test_results.xml --cov=src --cov-report=xml

# Check coverage thresholds
python -m pytest --cov=src --cov-fail-under=80
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure PYTHONPATH includes src/
   export PYTHONPATH="${PYTHONPATH}:./src"
   ```

2. **Missing Dependencies**
   ```bash
   # Install all required packages
   pip install -r requirements.txt
   pip install pytest pytest-cov pytest-mock
   ```

3. **Jira Test Failures**
   ```bash
   # Skip Jira tests if no credentials
   python -m pytest -m "not jira"
   ```

4. **Performance Test Timeouts**
   ```bash
   # Run performance tests separately with longer timeout
   python -m pytest tests/integration/ -m "slow" --timeout=300
   ```

## Adding New Tests

### Unit Test Template
```python
class TestNewComponent:
    @pytest.fixture
    def component(self):
        return NewComponent()
    
    def test_basic_functionality(self, component):
        result = component.method()
        assert result == expected_value
    
    def test_error_handling(self, component):
        with pytest.raises(ExpectedError):
            component.invalid_method()
```

### Integration Test Template
```python
def test_new_workflow(self, temp_directory):
    # Setup test data
    test_file = create_test_log_file(temp_directory)
    
    # Execute workflow
    result = run_complete_workflow(test_file)
    
    # Verify results
    assert len(result.patterns) > 0
    assert result.success == True
```

## Test Coverage Goals

Target coverage levels:
- **Overall**: > 85%
- **Core modules**: > 90%  
- **Utilities**: > 80%
- **Integration code**: > 70%

Check current coverage:
```bash
python -m pytest --cov=src --cov-report=term-missing
```

## Best Practices

1. **Test Independence**: Each test should run independently
2. **Descriptive Names**: Use clear, descriptive test method names
3. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification
4. **Mock External Dependencies**: Mock APIs, file systems, and network calls
5. **Test Edge Cases**: Include boundary conditions and error scenarios
6. **Performance Awareness**: Monitor test execution time
7. **Data Cleanup**: Clean up test files and temporary data

## Contact

For test-related questions or issues:
- Review test documentation
- Check existing test examples
- Follow established patterns for new tests
