# Smart Log Analyzer - User Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- Access to log files in JSON format

### 5-Minute Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Analyze sample logs
python src/main.py --input samplelogs/kafka.log

# 3. View results
cat data/processed/analysis_results.json
```

## Installation

### Option 1: Local Installation
```bash
# Clone the repository
git clone <repository-url>
cd smart-log-analyser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Docker Installation
```bash
# Build and run container
docker-compose up --build

# Access the application
curl http://localhost:8000/health
```

## Basic Usage

### Analyzing Log Files

#### Single File Analysis
```bash
python src/main.py --input /path/to/logfile.log
```

#### Component-Specific Analysis
```bash
python src/main.py --input /path/to/logfile.log --component kafka
```

#### Batch Processing
```bash
python src/main.py --input samplelogs/ --batch
```

### Command Line Options
```
Options:
  --input PATH          Path to log file or directory
  --component TEXT      Filter by component ID
  --output PATH         Output directory (default: data/processed)
  --format TEXT         Log format: json|text (default: json)
  --batch              Process multiple files
  --train              Train new ML models
  --config PATH        Configuration file path
```

### Sample Output
```json
{
  "analysis_summary": {
    "total_entries": 1250,
    "error_count": 45,
    "patterns_detected": 3,
    "severity_distribution": {
      "critical": 5,
      "high": 15,
      "medium": 20,
      "low": 5
    }
  },
  "detected_issues": [
    {
      "id": "issue_001",
      "title": "Database Connection Failure",
      "component": "virtualization-aggregator-kafka",
      "severity": "high",
      "frequency": 12,
      "first_occurrence": "2025-01-15T10:30:00Z",
      "last_occurrence": "2025-01-15T14:45:00Z",
      "pattern": "connection_refused",
      "defect_template": {
        "title": "Database Connection Failure in VA Kafka Service",
        "description": "Recurring database connection errors...",
        "priority": "P1",
        "labels": ["database", "connectivity", "kafka"]
      }
    }
  ]
}
```

## Advanced Features

### Machine Learning Model Training

#### Training Custom Models
```bash
# Train with your own data
python src/models/train_models.py --training-data data/training/ --output data/models/

# Evaluate model performance
python src/models/evaluate.py --model data/models/error_classifier.pkl
```

#### Model Configuration
Edit `configs/ml_config.yaml`:
```yaml
models:
  error_classifier:
    algorithm: "random_forest"
    features: ["message", "stacktrace", "component"]
    parameters:
      n_estimators: 100
      max_depth: 10
  
  anomaly_detector:
    algorithm: "isolation_forest"
    contamination: 0.1
```

### Component Filtering

#### Filter by Service Type
```bash
python src/main.py --input logs/ --component-type kafka
```

#### Custom Component Mapping
Edit `configs/component_mapping.yaml`:
```yaml
components:
  virtualization-aggregator-kafka:
    type: "message_queue"
    priority: "high"
    team: "platform"
  
  virtualization-aggregator-postgres:
    type: "database"
    priority: "critical"
    team: "data"
```

### Jira Integration

#### Setup Jira Configuration
Edit `configs/jira_config.yaml`:
```yaml
jira:
  server: "https://your-company.atlassian.net"
  username: "your-email@company.com"
  api_token: "your-api-token"
  project: "INFRA"
  
defect_templates:
  database_error:
    issue_type: "Bug"
    priority: "High"
    components: ["Database"]
    labels: ["automated", "log-analysis"]
```

#### Create Defects Automatically
```bash
# Analyze and create Jira tickets
python src/main.py --input logs/ --create-defects --jira-config configs/jira_config.yaml
```

## Configuration

### Main Configuration File
`configs/config.yaml`:
```yaml
# Application settings
app:
  name: "Smart Log Analyzer"
  version: "1.0.0"
  log_level: "INFO"

# Processing settings
processing:
  batch_size: 1000
  max_file_size: "1GB"
  supported_formats: ["json", "text"]
  
# ML settings
machine_learning:
  model_path: "data/models/"
  retrain_threshold: 0.85
  feature_extraction:
    use_tfidf: true
    max_features: 5000
    ngram_range: [1, 2]

# Output settings
output:
  format: "json"
  include_raw_logs: false
  generate_reports: true
```

### Environment Variables
```bash
# Optional environment variables
export SLA_CONFIG_PATH="/path/to/config.yaml"
export SLA_LOG_LEVEL="DEBUG"
export SLA_MODEL_PATH="/path/to/models/"
export JIRA_API_TOKEN="your-token"
```

## Troubleshooting

### Common Issues

#### Issue: "ModuleNotFoundError"
```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Or specific package
pip install scikit-learn pandas numpy
```

#### Issue: "Memory Error" with Large Files
```bash
# Solution: Use batch processing
python src/main.py --input large_file.log --batch-size 500
```

#### Issue: "JSON Decode Error"
```bash
# Solution: Specify correct format
python src/main.py --input file.log --format text

# Or validate JSON format
python -c "import json; json.load(open('file.log'))"
```

#### Issue: Poor Classification Accuracy
```bash
# Solution: Retrain models with more data
python src/models/train_models.py --training-data data/training/ --epochs 50

# Or adjust model parameters in ml_config.yaml
```

### Debug Mode
```bash
# Run with debug logging
python src/main.py --input logs/ --log-level DEBUG

# Check log outputs
tail -f logs/application.log
```

### Performance Optimization

#### For Large Log Files
```yaml
# Adjust config.yaml
processing:
  batch_size: 500  # Reduce memory usage
  parallel_processing: true
  chunk_size: "100MB"
```

#### For Better Accuracy
```yaml
# Increase model complexity
machine_learning:
  feature_extraction:
    max_features: 10000
    use_word_embeddings: true
  model_parameters:
    n_estimators: 200
    max_depth: 15
```

### Getting Help

1. **Check Documentation**: Review all files in `/docs` directory
2. **Sample Data**: Use files in `/samplelogs` for testing
3. **Configuration**: Verify all YAML files are properly formatted
4. **Logs**: Check `logs/application.log` for detailed error messages
5. **Community**: Submit issues or questions to the project repository

### System Requirements

#### Minimum Requirements
- Python 3.8+
- 4GB RAM
- 2GB disk space
- CPU: 2 cores

#### Recommended Requirements
- Python 3.9+
- 8GB RAM
- 10GB disk space
- CPU: 4+ cores
- SSD storage for better I/O performance

### Performance Expectations

| Log File Size | Processing Time | Memory Usage |
|---------------|-----------------|--------------|
| 1MB | 5 seconds | 100MB |
| 10MB | 30 seconds | 200MB |
| 100MB | 5 minutes | 500MB |
| 1GB | 30 minutes | 2GB |

## Next Steps

After successfully setting up and running basic analysis:

1. **Customize Configuration**: Modify settings for your specific environment
2. **Train Custom Models**: Use your historical log data for better accuracy
3. **Setup Jira Integration**: Automate defect creation workflow
4. **Monitor Performance**: Track system metrics and accuracy over time
5. **Scale Deployment**: Consider containerized deployment for production use

For advanced usage and enterprise features, refer to the [Technical Specification](technical_specification.md).
