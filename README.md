# 🚀 AI Driven Realtime Log Analyser

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Real-time](https://img.shields.io/badge/realtime-enabled-brightgreen.svg)](#real-time-features)

Enterprise-grade intelligent log analysis system with AI/ML capabilities, real-time monitoring, and automatic dashboard refresh.

## ✨ Features

### 🤖 AI/ML Capabilities
- **Machine Learning Classification**: TF-IDF + Naive Bayes for intelligent error categorization
- **Pattern Detection**: Automatic discovery of known and unknown error patterns
- **Anomaly Detection**: Isolation Forest algorithm for outlier identification
- **Smart Component Recognition**: Automatic infrastructure component detection

### 🔄 Real-time Processing
- **Live Log Monitoring**: 1-second polling for new log entries
- **Auto-refreshing Dashboard**: WebSocket-powered live updates (no manual refresh!)
- **Real-time Statistics**: Live counters and metrics
- **Instant Notifications**: Immediate processing of critical errors

### 📊 Visualization & Dashboards
- **Interactive HTML Dashboards**: Rich, responsive web dashboards
- **Static Chart Generation**: PNG charts for reports and documentation
- **Timeline Analysis**: Log activity over time with trend analysis
- **Error Heatmaps**: Activity patterns by time and component
- **HTTP Server**: Built-in web server for dashboard viewing

### 🤖 Intelligence Features
- **ML Classification**: Automatic error categorization and severity assessment
- **Pattern Recognition**: Both known and discovered error patterns
- **Frequency Analysis**: Statistical analysis of log patterns
- **Temporal Analysis**: Time-based anomaly detection
- **Component Insights**: Per-component error analysis and statistics

## 🏗 Project Structure

```
ai-driven-realtime-log-analyser/
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
├── configs/
│   └── default.yaml          # Default configuration
├── samplelogs/               # Sample log files (ALWAYS read from here)
│   ├── valogs.log           # VA component logs
│   └── COMMON\ VIRTUALIZATION\ PROVIDER.log
├── src/
│   ├── core/                # Core components
│   │   ├── analyzer.py      # Main analyzer class
│   │   ├── config.py        # Configuration management
│   │   └── models.py        # Data models
│   ├── analysis/            # Analysis engines
│   │   ├── pattern_detector.py   # Pattern detection
│   │   ├── ml_classifier.py      # ML classification
│   │   └── anomaly_detector.py   # Anomaly detection
│   ├── visualization/       # Visualization components
│   │   ├── dashboard_generator.py # HTML dashboard generation
│   │   ├── chart_generator.py     # Static chart generation
│   │   └── server.py             # HTTP server
│   └── utils/              # Utilities
│       ├── log_parser.py    # Log parsing
│       └── logger.py        # Logging setup
├── output/                  # Generated reports and charts
└── tests/                  # Test files
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the project directory
cd /home/dev/repo/ws/mrunal/mycode/ai-driven-realtime-log-analyser

# Install dependencies
pip install -r requirements.txt
```

### 2. Basic Usage

```bash
# Run analysis on default sample logs
python main.py

# Analyze specific log file
python main.py --log-file /path/to/your/logfile.log

# Run with real-time monitoring
python main.py --realtime

# Generate visualizations only
python main.py --visualize-only

# Serve dashboards via HTTP
python main.py --serve --port 8080
```

### Sample Log Location

**Important**: The sample logs are always read from:
```
/home/dev/repo/ws/mrunal/mycode/ai-driven-realtime-log-analyser/samplelogs/
```

This directory contains:
- `valogs.log` - Virtualization Aggregator logs
- `COMMON VIRTUALIZATION PROVIDER.log` - CVP component logs

The system can be configured to monitor this directory for new/updated log files.

## 📋 Configuration

Configuration is managed through YAML files. The default configuration is in `configs/default.yaml`:

```yaml
# Log file settings
log_file: "samplelogs/valogs.log"
output_dir: "output"
realtime: false

# Analysis settings
analysis:
  enable_ml_classification: true
  enable_anomaly_detection: true
  min_confidence_threshold: 0.7

# Visualization settings
visualization:
  generate_html_dashboard: true
  generate_static_charts: true
```

## 🎯 Usage Examples

### Basic Analysis
```bash
# Analyze default logs and generate dashboard
python main.py

# View results
python main.py --serve
```

### Advanced Analysis
```bash
# Full analysis with all features
python main.py --log-file samplelogs/valogs.log --debug

# Real-time monitoring
python main.py --realtime --output-dir /tmp/analysis
```

### Visualization Only
```bash
# Generate charts from existing analysis
python main.py --visualize-only

# Serve dashboards
python main.py --serve --port 8080
```

## 📊 Output

The analyzer generates:

1. **Interactive Dashboard** (`output/interactive_dashboard.html`)
   - Summary statistics
   - Timeline charts
   - Component breakdown
   - Error patterns
   - Top error messages

2. **Static Charts** (`output/*.png`)
   - Timeline chart
   - Component analysis
   - Error patterns
   - Distribution charts
   - Activity heatmaps

3. **Analysis Results** (`output/analysis_results.json`)
   - Complete analysis data in JSON format
   - Component statistics
   - Error patterns
   - Timeline data

## 🔧 Components Supported

The system automatically detects and analyzes logs from:

- **VA** - Virtualization Aggregator
- **CVP** - Common Virtualization Provider  
- **VM** - Virtual Manager
- **VMOPS** - Virtual Machine Operations
- **DSC** - Data Services Connector
- **NVM** - Nimble Virt Manager
- **PCBE** - PCBE CCA Framework

## 🤖 AI/ML Features

### Pattern Detection
- **Known Patterns**: Pre-defined error patterns (connection errors, auth failures, etc.)
- **Discovered Patterns**: Machine learning-based pattern discovery
- **Pattern Confidence**: Confidence scoring for pattern matches

### Anomaly Detection
- **Frequency Anomalies**: Unusual message frequencies
- **Pattern Anomalies**: Unusual message patterns
- **Temporal Anomalies**: Unusual timing patterns
- **ML Anomalies**: Isolation Forest-based detection

### Classification
- **Error Categorization**: Automatic error type classification
- **Severity Assessment**: Severity prediction for log entries
- **Component Inference**: Automatic component detection from log content

## 🌐 Web Dashboard

The interactive dashboard provides:

- **Real-time Statistics**: Live summary cards
- **Interactive Charts**: Plotly-powered visualizations
- **Component Analysis**: Detailed component breakdown
- **Error Timeline**: Time-series analysis
- **Pattern Visualization**: Error pattern distribution
- **Responsive Design**: Mobile-friendly interface

Access via: `http://localhost:8000` (or custom port)

## 🔄 Real-time Monitoring

Enable real-time monitoring with `--realtime` flag:

- Monitors log files for new entries
- Processes new logs automatically
- Updates analysis results
- Detects critical errors in real-time
- Maintains analysis state

## 🛠 Development

### Adding New Components

1. Update `ComponentType` enum in `src/core/models.py`
2. Add component detection logic in `LogEntry._infer_component()`
3. Update visualization templates if needed

### Adding New Analysis Features

1. Create new analyzer in `src/analysis/`
2. Integrate with main analyzer in `src/core/analyzer.py`
3. Update configuration schema in `src/core/config.py`

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Performance

- **Batch Processing**: Configurable batch sizes for large files
- **Memory Efficient**: Streaming processing for large logs
- **Parallel Processing**: Async/await for concurrent operations
- **Caching**: Model caching for improved performance

## 🔒 Security

- **Input Validation**: Secure log file parsing
- **Path Sanitization**: Prevents directory traversal
- **Error Handling**: Graceful handling of malformed logs
- **Resource Limits**: Configurable processing limits

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the logs in debug mode: `python main.py --debug`
- Review configuration in `configs/default.yaml`
- Verify sample logs in `samplelogs/` directory

---

**AI Driven Realtime Log Analyser v1.0** - Powered by AI/ML Technology 🚀
