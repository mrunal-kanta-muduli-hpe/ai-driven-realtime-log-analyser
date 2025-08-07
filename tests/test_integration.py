"""
Integration tests for AI Driven Realtime Log Analyser
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
import json

# Import test configuration
from . import TEST_LOG_FILE, TEST_OUTPUT_DIR, TEST_CONFIG_FILE

# Import modules to test
from core.analyzer import SmartLogAnalyzer
from core.config import Config
from utils.log_parser import LogParser


class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_basic_analysis_flow(self):
        """Test the complete analysis flow"""
        # Load configuration
        config = Config.load(TEST_CONFIG_FILE)
        config.log_file = str(TEST_LOG_FILE)
        config.output_dir = str(TEST_OUTPUT_DIR)
        config.realtime = False
        
        # Initialize analyzer
        analyzer = SmartLogAnalyzer(config)
        
        # Run analysis
        result = asyncio.run(analyzer.run_analysis())
        
        # Verify results
        assert result is not None
        assert len(analyzer.processed_entries) > 0
        
        # Check output files exist
        output_path = Path(TEST_OUTPUT_DIR)
        assert (output_path / "analysis_results.json").exists()
        assert (output_path / "interactive_dashboard.html").exists()
    
    def test_log_parser(self):
        """Test log parsing functionality"""
        parser = LogParser()
        
        # Test with sample log file
        entries = asyncio.run(parser.parse_file(TEST_LOG_FILE))
        
        assert len(entries) > 0
        assert all(hasattr(entry, 'message') for entry in entries)
        assert all(hasattr(entry, 'level') for entry in entries)
    
    def test_config_loading(self):
        """Test configuration loading"""
        config = Config.load(TEST_CONFIG_FILE)
        
        assert config is not None
        assert hasattr(config, 'log_file')
        assert hasattr(config, 'output_dir')
        assert hasattr(config, 'analysis')
    
    def test_visualization_generation(self):
        """Test visualization generation"""
        # Load configuration
        config = Config.load(TEST_CONFIG_FILE)
        config.log_file = str(TEST_LOG_FILE)
        config.output_dir = str(TEST_OUTPUT_DIR)
        
        # Initialize analyzer
        analyzer = SmartLogAnalyzer(config)
        
        # Parse logs first
        asyncio.run(analyzer._parse_logs())
        
        # Generate visualizations
        asyncio.run(analyzer.generate_visualizations())
        
        # Verify output files
        output_path = Path(TEST_OUTPUT_DIR)
        assert (output_path / "interactive_dashboard.html").exists()
        
        # Check if some chart files were generated
        chart_files = list(output_path.glob("*.png"))
        assert len(chart_files) > 0


class TestPerformance:
    """Performance tests"""
    
    def test_large_log_processing(self):
        """Test processing of larger log files"""
        # This test would use a larger sample or generate synthetic data
        # For now, just test with existing sample
        config = Config.load(TEST_CONFIG_FILE)
        config.log_file = str(TEST_LOG_FILE)
        config.output_dir = str(TEST_OUTPUT_DIR)
        
        analyzer = SmartLogAnalyzer(config)
        
        import time
        start_time = time.time()
        
        result = asyncio.run(analyzer.run_analysis())
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust based on your needs)
        assert processing_time < 30  # 30 seconds max for sample data
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
