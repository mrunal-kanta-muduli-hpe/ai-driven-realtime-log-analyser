"""
Test configuration and utilities for AI Driven Realtime Log Analyser
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for testing
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Test configuration
TEST_LOG_FILE = project_root / "sample-data" / "valogs.log"
TEST_OUTPUT_DIR = project_root / "test-results"
TEST_CONFIG_FILE = project_root / "configuration" / "default.yaml"

# Ensure test results directory exists
TEST_OUTPUT_DIR.mkdir(exist_ok=True)
