# Smart Log Analyzer (SLA)
## Intelligent Error Pattern Detection & Automated Defect Management System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Machine Learning](https://img.shields.io/badge/ML-Enabled-green.svg)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Overview

Smart Log Analyzer (SLA) is an intelligent system that processes application logs, identifies error patterns using machine learning, and automatically creates defects in issue tracking systems like Jira. The system is designed to reduce manual effort in log analysis and accelerate issue resolution.

## 🚀 Key Features

### Phase 1 (Current)
- **JSON Log Processing**: Parse and analyze structured JSON logs
- **Error Pattern Detection**: Identify common error patterns and anomalies
- **Component-based Filtering**: Filter logs by component ID or service type
- **Basic ML Classification**: Train models to categorize error types
- **Automated Defect Creation**: Generate issue templates for manual review

### Phase 2 (Planned)
- **Advanced ML Models**: Deep learning for complex pattern recognition
- **Real-time Analysis**: Stream processing for live log monitoring
- **Jira API Integration**: Automatic defect creation and assignment
- **Root Cause Analysis**: AI-powered investigation suggestions
- **Dashboard & Visualization**: Web-based monitoring interface

## 🏗 Architecture

```
Smart Log Analyzer
├── Data Ingestion Layer
│   ├── Log File Parsers (JSON, Plain Text)
│   ├── Component ID Filters
│   └── Data Validation
├── Analysis Engine
│   ├── Pattern Recognition
│   ├── Anomaly Detection
│   ├── ML Model Training
│   └── Classification
├── Intelligence Layer
│   ├── Error Categorization
│   ├── Severity Assessment
│   ├── Impact Analysis
│   └── Recommendation Engine
└── Integration Layer
    ├── Defect Template Generation
    ├── Jira API Integration
    └── Notification System
```

## 📁 Project Structure

```
smart-log-analyser/
├── src/
│   ├── core/
│   │   ├── log_parser.py          # JSON log parsing
│   │   ├── pattern_detector.py    # Error pattern detection
│   │   ├── ml_engine.py          # Machine learning models
│   │   └── component_filter.py   # Component-based filtering
│   ├── models/
│   │   ├── error_classifier.py   # ML model definitions
│   │   ├── anomaly_detector.py   # Anomaly detection models
│   │   └── feature_extractor.py  # Feature engineering
│   ├── integrations/
│   │   ├── jira_client.py        # Jira API integration
│   │   └── defect_generator.py   # Automated defect creation
│   ├── utils/
│   │   ├── config.py             # Configuration management
│   │   ├── logger.py             # Application logging
│   │   └── helpers.py            # Utility functions
│   └── main.py                   # Main application entry point
├── data/
│   ├── models/                   # Trained ML models
│   ├── training/                 # Training datasets
│   └── processed/                # Processed log data
├── tests/
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── fixtures/                 # Test data
├── configs/
│   ├── config.yaml              # Main configuration
│   ├── jira_config.yaml         # Jira settings
│   └── ml_config.yaml           # ML model settings
├── docs/
│   ├── technical_specification.md
│   ├── user_guide.md
│   └── api_documentation.md
├── samplelogs/                  # Sample log files
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
└── docker-compose.yml          # Containerization
```

## 🛠 Technology Stack

- **Language**: Python 3.8+
- **ML Libraries**: scikit-learn, pandas, numpy
- **NLP**: NLTK, spaCy
- **API Integration**: requests, jira-python
- **Data Processing**: pandas, json
- **Web Framework**: FastAPI (for future API)
- **Containerization**: Docker

## 📊 Sample Use Cases

### Use Case 1: Database Connection Issues
**Input**: Virtualization Aggregator logs showing DB connection failures
**Analysis**: Pattern detected - recurring "connection refused" errors
**Output**: Defect created with title "Database Connection Failure in VA Services"

### Use Case 2: Component-Specific Analysis
**Input**: Component ID "virtualization-aggregator-kafka"
**Analysis**: Filter logs by component, detect service startup failures
**Output**: Categorized errors with root cause suggestions

## 🚦 Getting Started

See [Quick Start Guide](docs/user_guide.md) for detailed setup instructions.

## 📈 Roadmap

- **Q1 2025**: Basic pattern detection and defect generation
- **Q2 2025**: ML model integration and Jira automation
- **Q3 2025**: Real-time analysis and web dashboard
- **Q4 2025**: Advanced AI-powered root cause analysis

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

For questions and support, please contact the development team.
