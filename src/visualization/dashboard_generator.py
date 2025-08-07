"""
Dashboard generator for AI Driven Realtime Log Analyser
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

from core.models import LogEntry
from core.config import Config

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """
    Generates interactive HTML dashboards for log analysis results
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.output_dir = config.get_output_path()

    async def generate_dashboard(
        self, 
        entries: List[LogEntry], 
        component_stats: Dict, 
        error_patterns: Dict
    ) -> Path:
        """
        Generate comprehensive HTML dashboard
        
        Args:
            entries: List of log entries
            component_stats: Component statistics
            error_patterns: Error pattern data
            
        Returns:
            Path to generated dashboard file
        """
        logger.info("📋 Generating interactive dashboard...")
        
        # Prepare dashboard data
        dashboard_data = await self._prepare_dashboard_data(
            entries, component_stats, error_patterns
        )
        
        # Generate HTML dashboard
        try:
            dashboard_html = self._generate_dashboard_html(dashboard_data)
        except Exception as e:
            logger.error(f"Failed to generate dashboard HTML: {e}")
            logger.error(f"Dashboard data keys: {dashboard_data.keys()}")
            if 'timeline' in dashboard_data:
                logger.error(f"Timeline data sample: {dashboard_data['timeline'][:2] if dashboard_data['timeline'] else 'Empty'}")
            raise
        
        # Save dashboard
        dashboard_path = self.output_dir / "interactive_dashboard.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        logger.info(f"✅ Dashboard generated: {dashboard_path}")
        return dashboard_path

    async def _prepare_dashboard_data(
        self, 
        entries: List[LogEntry], 
        component_stats: Dict, 
        error_patterns: Dict
    ) -> Dict:
        """Prepare data for dashboard"""
        
        # Summary statistics
        total_entries = len(entries)
        error_count = len([e for e in entries if e.level == "ERROR"])
        warning_count = len([e for e in entries if e.level in ["WARN", "WARNING"]])
        info_count = len([e for e in entries if e.level == "INFO"])
        
        # Timeline data
        timeline_data = self._generate_timeline_data(entries)
        
        # Component breakdown
        component_breakdown = self._generate_component_breakdown(component_stats)
        
        # Top errors
        top_errors = self._get_top_error_messages(entries)
        
        # Error patterns for visualization
        pattern_data = [
            {"pattern": pattern, "count": count}
            for pattern, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return {
            "summary": {
                "total_entries": total_entries,
                "error_count": error_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "error_rate": (error_count / total_entries * 100) if total_entries > 0 else 0,
                "components": len(component_stats),
                "patterns": len(error_patterns)
            },
            "timeline": timeline_data,
            "components": component_breakdown,
            "top_errors": top_errors,
            "patterns": pattern_data,
            "generated_at": datetime.now().isoformat()
        }

    def _generate_timeline_data(self, entries: List[LogEntry]) -> List[Dict]:
        """Generate timeline data for visualization"""
        timeline = defaultdict(lambda: {"ERROR": 0, "WARN": 0, "INFO": 0})
       
        for entry in entries:
            if entry.timestamp:
                # Group by hour
                hour_key = entry.timestamp.strftime("%Y-%m-%d %H:00:00")
               
                # Map log levels to timeline keys (keep uppercase for JS compatibility)
                level_mapping = {
                    "ERROR": "ERROR",
                    "WARN": "WARN",
                    "WARNING": "WARN",  # Map WARNING to WARN for consistency
                    "INFO": "INFO"
                }
               
                if entry.level in level_mapping:
                    timeline_key = level_mapping[entry.level]
                    timeline[hour_key][timeline_key] += 1
       
        # Ensure all entries have all required fields
        result = []
        for ts, counts in sorted(timeline.items()):
            entry = {
                "timestamp": ts,
                "ERROR": counts.get("ERROR", 0),
                "WARN": counts.get("WARN", 0),
                "INFO": counts.get("INFO", 0)
            }
            result.append(entry)
        
        return result
 
    async def _parse_logs(self):
        """Parse log files and extract entries"""
        log_path = self.config.get_log_path()
       
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")
       
        logger.info(f"📖 Parsing log file: {log_path}")
       
        entries = await self.log_parser.parse_file(log_path)
        self.processed_entries = entries
       
        logger.info(f"📊 Parsed {len(entries)} log entries")
       
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
           
            # Map log levels to stats keys
            level_mapping = {
                "ERROR": "errors",
                "WARN": "warnings",
                "WARNING": "warnings",
                "INFO": "info"
            }
           
            if entry.level in level_mapping:
                stat_key = level_mapping[entry.level]
                self.component_stats[component][stat_key] += 1
       
        return entries
        

    def _generate_component_breakdown(self, component_stats: Dict) -> List[Dict]:
        """Generate component breakdown for visualization"""
        breakdown = []
        
        for component, stats in component_stats.items():
            total = stats.get("total", 0)
            errors = stats.get("errors", 0)
            warnings = stats.get("warnings", 0)
            
            breakdown.append({
                "component": component,
                "total": total,
                "errors": errors,
                "warnings": warnings,
                "error_rate": (errors / total * 100) if total > 0 else 0
            })
        
        # Sort by error count
        breakdown.sort(key=lambda x: x["errors"], reverse=True)
        return breakdown

    def _get_top_error_messages(self, entries: List[LogEntry], limit: int = 10) -> List[Dict]:
        """Get top error messages by frequency"""
        from collections import defaultdict
        import re
        
        error_messages = defaultdict(int)
        
        for entry in entries:
            if entry.level == "ERROR":
                # Normalize error message
                normalized = re.sub(r'\d+', 'X', entry.message)
                normalized = re.sub(r'[a-f0-9]{8,}', 'HASH', normalized)
                error_messages[normalized] += 1
        
        # Get top errors
        top_errors = sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {"message": msg, "count": count}
            for msg, count in top_errors
        ]

    def _generate_dashboard_html(self, data: Dict) -> str:
        """Generate complete HTML dashboard"""
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Driven Realtime Log Analyser - Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header p {{
            opacity: 0.8;
            font-size: 1.1em;
        }}
        
        .dashboard-content {{
            padding: 30px;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .summary-card {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }}
        
        .summary-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }}
        
        .summary-card.error {{
            border-color: #e74c3c;
        }}
        
        .summary-card.warning {{
            border-color: #f39c12;
        }}
        
        .summary-card.info {{
            border-color: #3498db;
        }}
        
        .summary-card.success {{
            border-color: #27ae60;
        }}
        
        .summary-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .summary-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .chart-section {{
            margin: 30px 0;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
        }}
        
        .chart-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }}
        
        .chart-container {{
            height: 400px;
            margin: 20px 0;
        }}
        
        .table-container {{
            overflow-x: auto;
            margin: 20px 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .error-rate {{
            padding: 5px 10px;
            border-radius: 20px;
            color: white;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        .error-rate.high {{ background: #e74c3c; }}
        .error-rate.medium {{ background: #f39c12; }}
        .error-rate.low {{ background: #27ae60; }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .summary-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .dashboard-content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI Driven Realtime Log Analyser</h1>
            <p>Enterprise-grade intelligent log analysis dashboard</p>
            <p>Generated on: {generated_at}</p>
        </div>
        
        <div class="dashboard-content">
            <!-- Summary Cards -->
            <div class="summary-grid">
                <div class="summary-card info">
                    <div class="summary-value">{total_entries}</div>
                    <div class="summary-label">Total Entries</div>
                </div>
                <div class="summary-card error">
                    <div class="summary-value">{error_count}</div>
                    <div class="summary-label">Errors</div>
                </div>
                <div class="summary-card warning">
                    <div class="summary-value">{warning_count}</div>
                    <div class="summary-label">Warnings</div>
                </div>
                <div class="summary-card success">
                    <div class="summary-value">{components}</div>
                    <div class="summary-label">Components</div>
                </div>
                <div class="summary-card info">
                    <div class="summary-value">{error_rate:.1f}%</div>
                    <div class="summary-label">Error Rate</div>
                </div>
                <div class="summary-card warning">
                    <div class="summary-value">{patterns}</div>
                    <div class="summary-label">Error Patterns</div>
                </div>
            </div>
            
            <!-- Timeline Chart -->
            <div class="chart-section">
                <h2 class="chart-title">Log Activity Timeline</h2>
                <div id="timeline-chart" class="chart-container"></div>
            </div>
            
            <!-- Component Breakdown -->
            <div class="chart-section">
                <h2 class="chart-title">🔧 Component Analysis</h2>
                <div id="component-chart" class="chart-container"></div>
                
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Component</th>
                                <th>Total Logs</th>
                                <th>Errors</th>
                                <th>Warnings</th>
                                <th>Error Rate</th>
                            </tr>
                        </thead>
                        <tbody>
                            {component_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Error Patterns -->
            <div class="chart-section">
                <h2 class="chart-title">🚨 Top Error Patterns</h2>
                <div id="patterns-chart" class="chart-container"></div>
            </div>
            
            <!-- Top Errors Table -->
            <div class="chart-section">
                <h2 class="chart-title">❌ Most Frequent Errors</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Error Message</th>
                                <th>Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            {error_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="footer">
            AI Driven Realtime Log Analyser v1.0 - Powered by AI/ML Technology
        </div>
    </div>

    <script>
        // Dashboard data
        const dashboardData = {dashboard_data};
        
        // Timeline Chart
        function createTimelineChart() {{
            const timelineData = dashboardData.timeline;
            
            const traces = [
                {{
                    x: timelineData.map(d => d.timestamp),
                    y: timelineData.map(d => d.ERROR),
                    name: 'Errors',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: {{ color: '#e74c3c', width: 3 }},
                    marker: {{ size: 6 }}
                }},
                {{
                    x: timelineData.map(d => d.timestamp),
                    y: timelineData.map(d => d.WARN),
                    name: 'Warnings', 
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: {{ color: '#f39c12', width: 3 }},
                    marker: {{ size: 6 }}
                }},
                {{
                    x: timelineData.map(d => d.timestamp),
                    y: timelineData.map(d => d.INFO),
                    name: 'Info',
                    type: 'scatter',
                    mode: 'lines+markers', 
                    line: {{ color: '#3498db', width: 3 }},
                    marker: {{ size: 6 }}
                }}
            ];
            
            const layout = {{
                title: '',
                xaxis: {{ title: 'Time' }},
                yaxis: {{ title: 'Log Count' }},
                hovermode: 'x unified',
                showlegend: true,
                legend: {{ x: 0, y: 1 }}
            }};
            
            Plotly.newPlot('timeline-chart', traces, layout, {{responsive: true}});
        }}
        
        // Component Chart
        function createComponentChart() {{
            const componentData = dashboardData.components;
            
            const trace = {{
                x: componentData.map(d => d.component),
                y: componentData.map(d => d.errors),
                type: 'bar',
                marker: {{
                    color: componentData.map(d => d.error_rate > 10 ? '#e74c3c' : d.error_rate > 5 ? '#f39c12' : '#27ae60')
                }}
            }};
            
            const layout = {{
                title: '',
                xaxis: {{ title: 'Component' }},
                yaxis: {{ title: 'Error Count' }}
            }};
            
            Plotly.newPlot('component-chart', [trace], layout, {{responsive: true}});
        }}
        
        // Patterns Chart
        function createPatternsChart() {{
            const patternData = dashboardData.patterns;
            
            const trace = {{
                labels: patternData.map(d => d.pattern),
                values: patternData.map(d => d.count),
                type: 'pie',
                hole: 0.4,
                marker: {{
                    colors: ['#e74c3c', '#f39c12', '#9b59b6', '#3498db', '#1abc9c', '#34495e', '#95a5a6', '#f1c40f', '#e67e22', '#2ecc71']
                }}
            }};
            
            const layout = {{
                title: '',
                showlegend: true,
                legend: {{ x: 1, y: 0.5 }}
            }};
            
            Plotly.newPlot('patterns-chart', [trace], layout, {{responsive: true}});
        }}
        
        // Initialize charts
        document.addEventListener('DOMContentLoaded', function() {{
            createTimelineChart();
            createComponentChart(); 
            createPatternsChart();
        }});
    </script>
</body>
</html>
        """
        
        # Generate component rows
        component_rows = ""
        for comp in data["components"][:10]:  # Top 10 components
            error_rate = comp["error_rate"]
            rate_class = "high" if error_rate > 10 else "medium" if error_rate > 5 else "low"
            
            component_rows += f"""
            <tr>
                <td><strong>{comp['component']}</strong></td>
                <td>{comp['total']:,}</td>
                <td>{comp['errors']:,}</td>
                <td>{comp['warnings']:,}</td>
                <td><span class="error-rate {rate_class}">{error_rate:.1f}%</span></td>
            </tr>
            """
        
        # Generate error rows
        error_rows = ""
        for error in data["top_errors"][:10]:  # Top 10 errors
            message = error["message"][:100] + "..." if len(error["message"]) > 100 else error["message"]
            error_rows += f"""
            <tr>
                <td>{message}</td>
                <td>{error['count']:,}</td>
            </tr>
            """
        
        # Format the template
        return html_template.format(
            generated_at=data["generated_at"],
            total_entries=data["summary"]["total_entries"],
            error_count=data["summary"]["error_count"],
            warning_count=data["summary"]["warning_count"],
            components=data["summary"]["components"],
            error_rate=data["summary"]["error_rate"],
            patterns=data["summary"]["patterns"],
            component_rows=component_rows,
            error_rows=error_rows,
            dashboard_data=json.dumps(data)
        )
