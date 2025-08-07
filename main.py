#!/usr/bin/env python3
"""
AI Driven Realtime Log Analyser
Enterprise-grade intelligent log analysis system

This is the main entry point for the AI Driven Realtime Log Analyser system.
It provides comprehensive log analysis with AI/ML capabilities and real-time monitoring.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.analyzer import SmartLogAnalyzer
from core.config import Config
from utils.logger import setup_logging

async def run_realtime_dashboard(analyzer, port):
    """Run real-time dashboard with live updates"""
    # First run initial analysis
    await analyzer.run_analysis()
    
    # Then start real-time dashboard server
    from visualization.realtime_server import start_realtime_dashboard
    await start_realtime_dashboard(analyzer, port)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI Driven Realtime Log Analyser - Intelligent log analysis with AI/ML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run analysis on default sample logs
  python main.py

  # Analyze specific log file
  python main.py --log-file /path/to/logfile.log

  # Run with real-time monitoring
  python main.py --realtime

  # Generate visualizations only
  python main.py --visualize-only

  # Serve dashboards via HTTP
  python main.py --serve --port 8080
        """
    )

    parser.add_argument(
        "--log-file", "-f",
        default="sample-data/valogs.log",
        help="Path to log file (default: sample-data/valogs.log)"
    )

    parser.add_argument(
        "--config", "-c",
        default="configuration/default.yaml",
        help="Configuration file path"
    )

    parser.add_argument(
        "--realtime", "-r",
        action="store_true",
        help="Enable real-time log monitoring"
    )

    parser.add_argument(
        "--visualize-only", "-v",
        action="store_true",
        help="Only generate visualizations from existing analysis"
    )

    parser.add_argument(
        "--serve", "-s",
        action="store_true",
        help="Serve dashboards via HTTP server"
    )

    parser.add_argument(
        "--realtime-dashboard", "--rtd",
        action="store_true",
        help="Start real-time dashboard with live updates"
    )

    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port for HTTP server (default: 8000)"
    )

    parser.add_argument(
        "--output-dir", "-o",
        default="analysis-results",
        help="Output directory for results (default: analysis-results)"
    )

    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(debug=args.debug)
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        config = Config.load(args.config)
        
        # Update config with command line arguments
        config.update_from_args(args)

        # Initialize analyzer
        analyzer = SmartLogAnalyzer(config)

        if args.serve:
            # Serve existing dashboards
            logger.info("🌐 Starting dashboard server...")
            from visualization.server import DashboardServer
            server = DashboardServer(config.output_dir, args.port)
            server.serve()
        elif args.realtime_dashboard:
            # Start real-time dashboard with live updates
            logger.info("🚀 Starting real-time dashboard with live updates...")
            asyncio.run(run_realtime_dashboard(analyzer, args.port))
        elif args.visualize_only:
            # Generate visualizations only
            logger.info("📊 Generating visualizations...")
            asyncio.run(analyzer.generate_visualizations())
        else:
            # Run full analysis
            logger.info("🚀 Starting AI Driven Realtime Log Analysis...")
            asyncio.run(analyzer.run_analysis())

    except KeyboardInterrupt:
        logger.info("⏹️ Analysis stopped by user")
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
