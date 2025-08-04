#!/usr/bin/env python3
"""
Smart Log Analyzer - Main Application Entry Point

This is the primary entry point for the Smart Log Analyzer system.
It orchestrates log processing, pattern detection, and defect generation.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from src.core.log_parser import LogParser
from src.core.pattern_detector import PatternDetector
from src.core.component_filter import ComponentFilter
from src.core.ml_engine import MLEngine
from src.integrations.defect_generator import DefectGenerator
from src.utils.config import Config
from src.utils.logger import setup_logging


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Smart Log Analyzer - Intelligent Error Pattern Detection"
    )
    
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to log file or directory"
    )
    
    parser.add_argument(
        "--component", "-c",
        type=str,
        help="Filter by component ID (e.g., kafka, postgres)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/processed",
        help="Output directory (default: data/processed)"
    )
    
    parser.add_argument(
        "--format", "-f",
        type=str,
        default="json",
        choices=["json", "text"],
        help="Log format (default: json)"
    )
    
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process multiple files in directory"
    )
    
    parser.add_argument(
        "--train",
        action="store_true",
        help="Train new ML models"
    )
    
    parser.add_argument(
        "--create-defects",
        action="store_true",
        help="Create defects automatically"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="configs/config.yaml",
        help="Configuration file path"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    return parser.parse_args()


def process_single_file(file_path: str, config: Config, args: argparse.Namespace) -> Dict[str, Any]:
    """Process a single log file."""
    logging.info(f"Processing log file: {file_path}")
    
    # Initialize components
    parser = LogParser(config)
    pattern_detector = PatternDetector(config)
    component_filter = ComponentFilter(config)
    ml_engine = MLEngine(config)
    defect_generator = DefectGenerator(config)
    
    # Parse logs
    log_entries = parser.parse_file(file_path, args.format)
    logging.info(f"Parsed {len(log_entries)} log entries")
    
    # Filter by component if specified
    if args.component:
        log_entries = component_filter.filter_by_component(log_entries, args.component)
        logging.info(f"Filtered to {len(log_entries)} entries for component: {args.component}")
    
    # Detect patterns
    patterns = pattern_detector.detect_patterns(log_entries)
    logging.info(f"Detected {len(patterns)} error patterns")
    
    # ML analysis
    if args.train:
        ml_engine.train_models(log_entries)
        logging.info("ML models trained successfully")
    
    classifications = ml_engine.classify_errors(log_entries)
    anomalies = ml_engine.detect_anomalies(log_entries)
    
    # Generate analysis results
    analysis_results = {
        "file_path": file_path,
        "analysis_summary": {
            "total_entries": len(log_entries),
            "error_count": len([entry for entry in log_entries if parser.is_error(entry)]),
            "patterns_detected": len(patterns),
            "anomalies_found": len(anomalies),
            "component_filter": args.component
        },
        "detected_patterns": patterns,
        "classifications": classifications,
        "anomalies": anomalies,
        "detected_issues": []
    }
    
    # Generate defect templates
    if patterns:
        defect_templates = defect_generator.generate_defects(patterns, log_entries)
        analysis_results["detected_issues"] = defect_templates
        
        if args.create_defects:
            # TODO: Integrate with Jira API
            logging.info("Defect creation requested - implement Jira integration")
    
    return analysis_results


def process_batch(directory_path: str, config: Config, args: argparse.Namespace) -> List[Dict[str, Any]]:
    """Process multiple log files in a directory."""
    directory = Path(directory_path)
    
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")
    
    log_files = list(directory.glob("*.log")) + list(directory.glob("*.json"))
    
    if not log_files:
        raise ValueError(f"No log files found in directory: {directory_path}")
    
    logging.info(f"Found {len(log_files)} log files to process")
    
    results = []
    for log_file in log_files:
        try:
            result = process_single_file(str(log_file), config, args)
            results.append(result)
        except Exception as e:
            logging.error(f"Error processing {log_file}: {e}")
            continue
    
    return results


def save_results(results: List[Dict[str, Any]], output_dir: str) -> None:
    """Save analysis results to output directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save individual results
    for i, result in enumerate(results):
        filename = f"analysis_result_{i+1}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logging.info(f"Saved results to: {filepath}")
    
    # Save summary report
    summary = {
        "total_files_processed": len(results),
        "total_errors_found": sum(r["analysis_summary"]["error_count"] for r in results),
        "total_patterns_detected": sum(r["analysis_summary"]["patterns_detected"] for r in results),
        "total_issues_generated": sum(len(r["detected_issues"]) for r in results),
        "processing_timestamp": str(Path().cwd()),
        "files_summary": [
            {
                "file": r["file_path"],
                "errors": r["analysis_summary"]["error_count"],
                "patterns": r["analysis_summary"]["patterns_detected"],
                "issues": len(r["detected_issues"])
            }
            for r in results
        ]
    }
    
    summary_path = output_path / "analysis_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logging.info(f"Saved summary report to: {summary_path}")


def main():
    """Main application entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    logging.info("Starting Smart Log Analyzer")
    
    try:
        # Load configuration
        config = Config(args.config)
        logging.info(f"Loaded configuration from: {args.config}")
        
        # Process logs
        if args.batch:
            results = process_batch(args.input, config, args)
        else:
            result = process_single_file(args.input, config, args)
            results = [result]
        
        # Save results
        save_results(results, args.output)
        
        # Print summary
        total_errors = sum(r["analysis_summary"]["error_count"] for r in results)
        total_patterns = sum(r["analysis_summary"]["patterns_detected"] for r in results)
        total_issues = sum(len(r["detected_issues"]) for r in results)
        
        print("\n" + "="*60)
        print("SMART LOG ANALYZER - ANALYSIS COMPLETE")
        print("="*60)
        print(f"Files Processed: {len(results)}")
        print(f"Errors Found: {total_errors}")
        print(f"Patterns Detected: {total_patterns}")
        print(f"Issues Generated: {total_issues}")
        print(f"Results Saved To: {args.output}")
        print("="*60)
        
        if total_issues > 0:
            print("\nHigh-priority issues detected! Review generated defect templates.")
        
        logging.info("Smart Log Analyzer completed successfully")
        
    except Exception as e:
        logging.error(f"Application error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
