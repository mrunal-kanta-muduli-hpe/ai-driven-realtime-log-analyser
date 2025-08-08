"""
Core AI Driven Realtime Log Analyser implementation
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import re

from core.config import Config
from core.models import LogEntry, AnalysisResult, ComponentType
from analysis.pattern_detector import PatternDetector
from analysis.ml_classifier import MLClassifier
from analysis.anomaly_detector import AnomalyDetector
from utils.log_parser import LogParser
from visualization.dashboard_generator import DashboardGenerator
from visualization.chart_generator import ChartGenerator

logger = logging.getLogger(__name__)


class SmartLogAnalyzer:
    """
    Main AI Driven Realtime Log Analyser class
    
    Combines all functionality:
    - Log parsing and processing
    - Pattern detection
    - ML-based classification
    - Anomaly detection
    - Real-time monitoring
    - Visualization generation
    """

    def __init__(self, config: Config):
        self.config = config
        self.log_parser = LogParser()
        self.pattern_detector = PatternDetector()
        self.ml_classifier = MLClassifier()
        self.anomaly_detector = AnomalyDetector()
        self.dashboard_generator = DashboardGenerator(config)
        self.chart_generator = ChartGenerator(config)
        
        # Analysis state
        self.processed_entries: List[LogEntry] = []
        self.analysis_results: List[AnalysisResult] = []
        self.component_stats: Dict[str, Dict] = defaultdict(dict)
        self.error_patterns: Dict[str, int] = defaultdict(int)
        
        # Real-time monitoring state
        self.is_monitoring = False
        self.last_position = 0
        
        logger.info("AI Driven Realtime Log Analyser initialized")

    async def run_analysis(self) -> Dict:
        """
        Run complete log analysis
        
        Returns:
            Dict containing analysis results and statistics
        """
        start_time = time.time()
        
        try:
            # Ensure output directory exists
            self.config.get_output_path().mkdir(parents=True, exist_ok=True)
            
            logger.info("Starting log analysis...")
            
            # Phase 1: Parse and load logs
            await self._parse_logs()
            
            # Phase 2: Train ML models if enabled
            if self.config.analysis.enable_ml_classification:
                await self._train_models()
            
            # Phase 3: Analyze patterns and detect anomalies
            await self._analyze_patterns()
            
            # Phase 4: Generate analysis results
            results = await self._generate_analysis_results()
            
            # Phase 5: Create visualizations
            await self.generate_visualizations()
            
            # Phase 6: Start real-time monitoring if enabled
            if self.config.realtime:
                await self._start_realtime_monitoring()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            logger.info(f"✅ Analysis completed in {processing_time:.2f} seconds")
            
            return {
                "status": "success",
                "processing_time": processing_time,
                "total_entries": len(self.processed_entries),
                "errors_detected": len([e for e in self.processed_entries if e.level == "ERROR"]),
                "results": results,
                "output_dir": str(self.config.get_output_path())
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            raise

    async def _parse_logs(self):
        """Parse log files and extract entries"""
        log_path = self.config.get_log_path()
        
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")
        
        logger.info(f"Parsing log file: {log_path}")
        
        entries = await self.log_parser.parse_file(log_path)
        self.processed_entries = entries
        
        logger.info(f"Parsed {len(entries)} log entries")
        
        # Update component statistics
        for entry in entries:
            component = entry.component or "UNKNOWN"
            if component not in self.component_stats:
                self.component_stats[component] = {
                    "total": 0,
                    "errors": 0,
                    "warnings": 0,
                    "info": 0
                }
            
            self.component_stats[component]["total"] += 1
            level = entry.level.lower()
            if level in self.component_stats[component]:
                self.component_stats[component][level] += 1

    async def _train_models(self):
        """Train ML models on the parsed data"""
        logger.info("Training ML models...")
        
        # Prepare training data
        training_data = []
        labels = []
        
        for entry in self.processed_entries:
            if entry.level in ["ERROR", "WARN"]:
                training_data.append(entry.message)
                labels.append(entry.level)
        
        if training_data:
            await self.ml_classifier.train(training_data, labels)
            logger.info(f"✅ ML model trained on {len(training_data)} samples")
        else:
            logger.warning("⚠️ No training data available for ML models")

    async def _analyze_patterns(self):
        """Analyze patterns and detect anomalies"""
        logger.info("🔍 Analyzing patterns and detecting anomalies...")
        
        error_entries = [e for e in self.processed_entries if e.level == "ERROR"]
        
        # Detect patterns
        patterns = await self.pattern_detector.detect_patterns(error_entries)
        
        # Update pattern statistics
        for pattern in patterns:
            self.error_patterns[pattern["pattern"]] = pattern["count"]
        
        # Detect anomalies if enabled
        if self.config.analysis.enable_anomaly_detection:
            anomalies = await self.anomaly_detector.detect_anomalies(self.processed_entries)
            logger.info(f"Detected {len(anomalies)} anomalies")
        
        logger.info(f"Detected {len(patterns)} error patterns")

    async def _generate_analysis_results(self) -> Dict:
        """Generate consolidated analysis results"""
        results = {
            "summary": {
                "total_entries": len(self.processed_entries),
                "error_count": len([e for e in self.processed_entries if e.level == "ERROR"]),
                "warning_count": len([e for e in self.processed_entries if e.level == "WARN"]),
                "info_count": len([e for e in self.processed_entries if e.level == "INFO"]),
            },
            "component_stats": dict(self.component_stats),
            "error_patterns": dict(self.error_patterns),
            "top_errors": self._get_top_errors(),
            "timeline": self._generate_timeline_data(),
            "generated_at": datetime.now().isoformat()
        }
        
        # Save results to file
        results_file = self.config.get_output_path() / "analysis_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"💾 Analysis results saved to: {results_file}")
        
        return results

    def _get_top_errors(self, limit: int = 10) -> List[Dict]:
        """Get top error messages by frequency"""
        error_messages = defaultdict(int)
        
        for entry in self.processed_entries:
            if entry.level == "ERROR":
                # Normalize error message for better grouping
                normalized = re.sub(r'\d+', 'X', entry.message)
                error_messages[normalized] += 1
        
        # Sort by frequency and return top errors
        top_errors = sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {"message": msg, "count": count}
            for msg, count in top_errors
        ]

    def _generate_timeline_data(self) -> List[Dict]:
        """Generate timeline data for visualization"""
        timeline = defaultdict(lambda: {"error": 0, "warning": 0, "info": 0})
        
        for entry in self.processed_entries:
            if entry.timestamp:
                # Group by hour
                hour_key = entry.timestamp.strftime("%Y-%m-%d %H:00:00")
                # Normalize level names
                level_key = "warning" if entry.level in ["WARN", "WARNING"] else entry.level.lower()
                timeline[hour_key][level_key] += 1
        
        return [
            {"timestamp": ts, **counts}
            for ts, counts in sorted(timeline.items())
        ]

    async def generate_visualizations(self):
        """Generate all visualizations"""
        logger.info("Generating visualizations...")
        
        if not self.processed_entries:
            logger.warning("⚠️ No data available for visualization")
            return
        
        output_path = self.config.get_output_path()
        
        # Generate dashboard
        if self.config.visualization.generate_html_dashboard:
            dashboard_path = await self.dashboard_generator.generate_dashboard(
                self.processed_entries, 
                self.component_stats,
                self.error_patterns
            )
            logger.info(f"📋 Dashboard generated: {dashboard_path}")
        
        # Generate static charts
        if self.config.visualization.generate_static_charts:
            chart_paths = await self.chart_generator.generate_charts(
                self.processed_entries,
                self.component_stats,
                self.error_patterns
            )
            logger.info(f"Charts generated: {len(chart_paths)} files")

    async def _start_realtime_monitoring(self):
        """Start real-time log monitoring with auto-refresh"""
        logger.info("🔄 Starting real-time monitoring with auto-refresh...")
        self.is_monitoring = True
        
        log_path = self.config.get_log_path()
        last_refresh = time.time()
        refresh_interval = 5.0  # Refresh visualizations every 5 seconds if new data
        
        # Monitor for new log entries
        while self.is_monitoring:
            try:
                # Check for new content in log file
                new_entries = await self.log_parser.parse_new_entries(
                    log_path, 
                    self.last_position
                )
                
                if new_entries:
                    logger.info(f"📥 Found {len(new_entries)} new log entries")
                    
                    # Process new entries
                    for entry in new_entries:
                        self.processed_entries.append(entry)
                        
                        # Real-time analysis for critical errors
                        if entry.level == "ERROR":
                            await self._process_realtime_error(entry)
                    
                    # Update last position
                    self.last_position = log_path.stat().st_size
                    
                    # Re-analyze patterns with new data
                    await self._update_analysis_with_new_data()
                    
                    # Refresh visualizations if enough time has passed
                    current_time = time.time()
                    if current_time - last_refresh >= refresh_interval:
                        logger.info("🔄 Refreshing visualizations with new data...")
                        await self.generate_visualizations()
                        last_refresh = current_time
                
                # Wait before next check
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"❌ Real-time monitoring error: {e}")
                await asyncio.sleep(5.0)

    async def _process_realtime_error(self, entry: LogEntry):
        """Process error in real-time"""
        # Classify error if ML is enabled
        if self.config.analysis.enable_ml_classification:
            classification = await self.ml_classifier.classify([entry.message])
            if classification:
                logger.warning(f"🚨 Real-time error detected: {classification[0]} - {entry.message[:100]}...")

    async def _update_analysis_with_new_data(self):
        """Update analysis patterns and statistics with new data"""
        try:
            # Update error patterns from recent entries
            recent_entries = self.processed_entries[-10:]  # Last 10 entries
            for entry in recent_entries:
                if entry.level in ["ERROR", "WARNING"]:
                    # Extract error pattern
                    pattern = self.pattern_detector.extract_pattern(entry.message)
                    if pattern:
                        self.error_patterns[pattern] += 1

            # Update component statistics
            for entry in recent_entries:
                if entry.component:
                    if entry.component not in self.component_stats:
                        self.component_stats[entry.component] = {
                            'total': 0,
                            'errors': 0,
                            'warnings': 0
                        }
                    
                    self.component_stats[entry.component]['total'] += 1
                    if entry.level == 'ERROR':
                        self.component_stats[entry.component]['errors'] += 1
                    elif entry.level == 'WARNING':
                        self.component_stats[entry.component]['warnings'] += 1

        except Exception as e:
            logger.error(f"❌ Error updating analysis with new data: {e}")

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_monitoring = False
        logger.info("⏹️ Real-time monitoring stopped")
