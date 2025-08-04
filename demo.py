#!/usr/bin/env python3
"""
Smart Log Analyzer - Quick Demo Script

This script demonstrates the basic functionality of the Smart Log Analyzer
using the sample log files in the samplelogs directory.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import main

def run_demo():
    """Run demonstration of Smart Log Analyzer functionality."""
    print("=" * 60)
    print("SMART LOG ANALYZER - DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Check if sample logs exist
    sample_dir = Path("samplelogs")
    if not sample_dir.exists():
        print("❌ Sample logs directory not found!")
        print("Please ensure samplelogs/ directory exists with log files.")
        return
    
    log_files = list(sample_dir.glob("*.log"))
    if not log_files:
        print("❌ No log files found in samplelogs/")
        return
    
    print(f"📁 Found {len(log_files)} sample log files:")
    for log_file in log_files:
        print(f"   - {log_file.name}")
    print()
    
    # Demo 1: Analyze single file
    print("🔍 DEMO 1: Analyzing single log file...")
    print("-" * 40)
    
    # Use kafka.log as it has good error examples
    kafka_log = sample_dir / "kafka.log"
    if kafka_log.exists():
        # Simulate command line arguments
        sys.argv = [
            "demo.py",
            "--input", str(kafka_log),
            "--output", "demo_output",
            "--log-level", "INFO"
        ]
        
        try:
            main()
            print("✅ Single file analysis completed!")
        except Exception as e:
            print(f"❌ Demo 1 failed: {e}")
    
    print()
    
    # Demo 2: Component-specific analysis
    print("🎯 DEMO 2: Component-specific analysis...")
    print("-" * 40)
    
    sys.argv = [
        "demo.py",
        "--input", str(kafka_log),
        "--component", "kafka",
        "--output", "demo_output/component_analysis",
        "--log-level", "INFO"
    ]
    
    try:
        main()
        print("✅ Component-specific analysis completed!")
    except Exception as e:
        print(f"❌ Demo 2 failed: {e}")
    
    print()
    
    # Demo 3: Batch processing
    print("📦 DEMO 3: Batch processing all sample logs...")
    print("-" * 40)
    
    sys.argv = [
        "demo.py",
        "--input", str(sample_dir),
        "--batch",
        "--output", "demo_output/batch_analysis",
        "--log-level", "INFO"
    ]
    
    try:
        main()
        print("✅ Batch processing completed!")
    except Exception as e:
        print(f"❌ Demo 3 failed: {e}")
    
    print()
    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print()
    print("📊 Results saved to demo_output/ directory")
    print("📖 Check the generated JSON files for detailed analysis results")
    print()
    print("🚀 Next steps:")
    print("   1. Review the analysis results in demo_output/")
    print("   2. Try different components: --component postgres|grpc|rest")
    print("   3. Enable ML training: --train (requires more data)")
    print("   4. Configure Jira integration for automated defect creation")

if __name__ == "__main__":
    run_demo()
