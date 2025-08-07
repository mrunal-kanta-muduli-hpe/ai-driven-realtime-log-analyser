"""
Chart generator for AI Driven Realtime Log Analyser
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
import json

# Import plotting libraries with fallback
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from core.models import LogEntry
from core.config import Config

logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Generates static charts for log analysis visualization
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.output_dir = config.get_output_path()
        
        if MATPLOTLIB_AVAILABLE:
            # Set style
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
        else:
            logger.warning("⚠️ Matplotlib not available. Static chart generation disabled.")

    async def generate_charts(
        self, 
        entries: List[LogEntry], 
        component_stats: Dict, 
        error_patterns: Dict
    ) -> List[Path]:
        """
        Generate all static charts
        
        Args:
            entries: List of log entries
            component_stats: Component statistics
            error_patterns: Error pattern data
            
        Returns:
            List of generated chart file paths
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Cannot generate charts - matplotlib not available")
            return []
        
        logger.info("Generating static charts...")
        
        chart_paths = []
        
        try:
            # Timeline chart
            timeline_path = await self._generate_timeline_chart(entries)
            if timeline_path:
                chart_paths.append(timeline_path)
            
            # Component breakdown chart
            component_path = await self._generate_component_chart(component_stats)
            if component_path:
                chart_paths.append(component_path)
            
            # Error patterns chart
            patterns_path = await self._generate_patterns_chart(error_patterns)
            if patterns_path:
                chart_paths.append(patterns_path)
            
            # Log level distribution
            distribution_path = await self._generate_distribution_chart(entries)
            if distribution_path:
                chart_paths.append(distribution_path)
            
            # Heatmap
            heatmap_path = await self._generate_heatmap(entries)
            if heatmap_path:
                chart_paths.append(heatmap_path)
            
            logger.info(f"✅ Generated {len(chart_paths)} charts")
            
        except Exception as e:
            logger.error(f"❌ Chart generation failed: {e}")
        
        return chart_paths

    async def _generate_timeline_chart(self, entries: List[LogEntry]) -> Path:
        """Generate timeline chart showing log activity over time"""
        timestamped_entries = [e for e in entries if e.timestamp]
        
        if len(timestamped_entries) < 2:
            logger.warning("Insufficient timestamped data for timeline chart")
            return None
        
        # Group by hour and level
        from collections import defaultdict
        timeline_data = defaultdict(lambda: {"ERROR": 0, "WARN": 0, "INFO": 0})
        
        for entry in timestamped_entries:
            hour_key = entry.timestamp.replace(minute=0, second=0, microsecond=0)
            level = entry.level or "INFO"
            timeline_data[hour_key][level] += 1
        
        # Prepare data for plotting
        timestamps = sorted(timeline_data.keys())
        errors = [timeline_data[ts]["ERROR"] for ts in timestamps]
        warnings = [timeline_data[ts]["WARN"] for ts in timestamps]
        infos = [timeline_data[ts]["INFO"] for ts in timestamps]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot lines
        ax.plot(timestamps, errors, label='Errors', color='red', linewidth=2, marker='o')
        ax.plot(timestamps, warnings, label='Warnings', color='orange', linewidth=2, marker='s')
        ax.plot(timestamps, infos, label='Info', color='blue', linewidth=2, marker='^')
        
        # Formatting
        ax.set_title('Log Activity Timeline', fontsize=16, fontweight='bold')
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Log Count', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        if len(timestamps) > 24:  # More than 24 hours
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "timeline_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path

    async def _generate_component_chart(self, component_stats: Dict) -> Path:
        """Generate component breakdown chart"""
        if not component_stats:
            return None
        
        # Prepare data
        components = list(component_stats.keys())[:10]  # Top 10 components
        error_counts = [component_stats[comp].get("errors", 0) for comp in components]
        total_counts = [component_stats[comp].get("total", 0) for comp in components]
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Error count bar chart
        bars1 = ax1.bar(components, error_counts, color='red', alpha=0.7)
        ax1.set_title('Error Count by Component', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Component')
        ax1.set_ylabel('Error Count')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        # Total count bar chart
        bars2 = ax2.bar(components, total_counts, color='blue', alpha=0.7)
        ax2.set_title('Total Log Count by Component', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Component')
        ax2.set_ylabel('Total Count')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "component_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path

    async def _generate_patterns_chart(self, error_patterns: Dict) -> Path:
        """Generate error patterns chart"""
        if not error_patterns:
            return None
        
        # Get top patterns
        sorted_patterns = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
        patterns = [p[0][:30] + "..." if len(p[0]) > 30 else p[0] for p in sorted_patterns]
        counts = [p[1] for p in sorted_patterns]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Horizontal bar chart for better readability
        bars = ax.barh(patterns, counts, color='orange', alpha=0.7)
        
        ax.set_title('Top Error Patterns', fontsize=16, fontweight='bold')
        ax.set_xlabel('Occurrence Count')
        ax.set_ylabel('Error Pattern')
        
        # Add value labels on bars
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                    f'{int(width)}', ha='left', va='center')
        
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "patterns_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path

    async def _generate_distribution_chart(self, entries: List[LogEntry]) -> Path:
        """Generate log level distribution chart"""
        # Count log levels
        from collections import Counter
        level_counts = Counter(entry.level for entry in entries)
        
        # Prepare data
        levels = list(level_counts.keys())
        counts = list(level_counts.values())
        colors = {
            'ERROR': 'red',
            'WARN': 'orange', 
            'INFO': 'blue',
            'DEBUG': 'green'
        }
        bar_colors = [colors.get(level, 'gray') for level in levels]
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Bar chart
        bars = ax1.bar(levels, counts, color=bar_colors, alpha=0.7)
        ax1.set_title('Log Level Distribution', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Log Level')
        ax1.set_ylabel('Count')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        # Pie chart
        ax2.pie(counts, labels=levels, colors=bar_colors, autopct='%1.1f%%',
                startangle=90)
        ax2.set_title('Log Level Distribution (%)', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "distribution_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path

    async def _generate_heatmap(self, entries: List[LogEntry]) -> Path:
        """Generate activity heatmap by hour and day"""
        timestamped_entries = [e for e in entries if e.timestamp]
        
        if len(timestamped_entries) < 10:
            return None
        
        # Prepare data for heatmap
        import numpy as np
        heatmap_data = np.zeros((7, 24))  # 7 days, 24 hours
        
        for entry in timestamped_entries:
            if entry.level == "ERROR":  # Focus on errors for heatmap
                day_of_week = entry.timestamp.weekday()
                hour = entry.timestamp.hour
                heatmap_data[day_of_week][hour] += 1
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Create heatmap
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        hours = [f'{h:02d}:00' for h in range(24)]
        
        im = ax.imshow(heatmap_data, cmap='Reds', aspect='auto')
        
        # Set ticks and labels
        ax.set_xticks(range(24))
        ax.set_xticklabels(hours, rotation=45)
        ax.set_yticks(range(7))
        ax.set_yticklabels(days)
        
        # Add colorbar
        plt.colorbar(im, ax=ax, label='Error Count')
        
        ax.set_title('Error Activity Heatmap (Day vs Hour)', fontsize=16, fontweight='bold')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Day of Week')
        
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "heatmap.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path

    async def generate_summary_chart(self, summary_data: Dict) -> Path:
        """Generate a comprehensive summary chart"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Summary statistics
        summary = summary_data.get("summary", {})
        
        # Chart 1: Log levels pie chart
        levels = ["ERROR", "WARN", "INFO"]
        counts = [
            summary.get("error_count", 0),
            summary.get("warning_count", 0), 
            summary.get("info_count", 0)
        ]
        colors = ['red', 'orange', 'blue']
        
        ax1.pie(counts, labels=levels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Log Level Distribution')
        
        # Chart 2: Component error rates
        components_data = summary_data.get("components", [])[:8]  # Top 8
        if components_data:
            comp_names = [c["component"] for c in components_data]
            error_rates = [c["error_rate"] for c in components_data]
            
            ax2.bar(comp_names, error_rates, color='coral')
            ax2.set_title('Error Rate by Component (%)')
            ax2.set_ylabel('Error Rate (%)')
            ax2.tick_params(axis='x', rotation=45)
        
        # Chart 3: Timeline (simplified)
        timeline_data = summary_data.get("timeline", [])[:24]  # Last 24 hours
        if timeline_data:
            timestamps = [t["timestamp"] for t in timeline_data]
            errors = [t["ERROR"] for t in timeline_data]
            
            ax3.plot(range(len(timestamps)), errors, marker='o', color='red')
            ax3.set_title('Error Count Over Time')
            ax3.set_ylabel('Error Count')
            ax3.set_xlabel('Time Period')
        
        # Chart 4: Top patterns
        patterns_data = summary_data.get("patterns", [])[:5]  # Top 5
        if patterns_data:
            pattern_names = [p["pattern"][:20] + "..." if len(p["pattern"]) > 20 else p["pattern"] 
                           for p in patterns_data]
            pattern_counts = [p["count"] for p in patterns_data]
            
            ax4.barh(pattern_names, pattern_counts, color='purple', alpha=0.7)
            ax4.set_title('Top Error Patterns')
            ax4.set_xlabel('Count')
        
        plt.suptitle('AI Driven Realtime Log Analyser - Summary Dashboard', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save chart
        chart_path = self.output_dir / "summary_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
