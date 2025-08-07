"""
Configuration management for AI Driven Realtime Log Analyser
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class AnalysisConfig:
    """Analysis configuration"""
    batch_size: int = 1000
    max_errors_to_analyze: int = 10000
    min_confidence_threshold: float = 0.7
    enable_ml_classification: bool = True
    enable_anomaly_detection: bool = True
    pattern_recognition_window: int = 100


@dataclass
class VisualizationConfig:
    """Visualization configuration"""
    generate_html_dashboard: bool = True
    generate_static_charts: bool = True
    chart_formats: List[str] = None
    max_chart_points: int = 1000
    color_scheme: str = "default"

    def __post_init__(self):
        if self.chart_formats is None:
            self.chart_formats = ["png", "html"]


@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "localhost"
    port: int = 8000
    auto_open_browser: bool = True
    enable_cors: bool = True


@dataclass
class Config:
    """Main configuration class"""
    log_file: str = "samplelogs/valogs.log"
    output_dir: str = "output"
    realtime: bool = False
    debug: bool = False
    
    analysis: AnalysisConfig = None
    visualization: VisualizationConfig = None
    server: ServerConfig = None

    def __post_init__(self):
        if self.analysis is None:
            self.analysis = AnalysisConfig()
        if self.visualization is None:
            self.visualization = VisualizationConfig()
        if self.server is None:
            self.server = ServerConfig()

    @classmethod
    def load(cls, config_path: str = "configs/default.yaml") -> "Config":
        """Load configuration from file"""
        config_file = Path(config_path)
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Convert nested dicts to dataclasses
            if 'analysis' in data:
                data['analysis'] = AnalysisConfig(**data['analysis'])
            if 'visualization' in data:
                data['visualization'] = VisualizationConfig(**data['visualization'])
            if 'server' in data:
                data['server'] = ServerConfig(**data['server'])
            
            return cls(**data)
        else:
            # Return default config
            return cls()

    def save(self, config_path: str):
        """Save configuration to file"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False, indent=2)

    def update_from_args(self, args):
        """Update configuration from command line arguments"""
        self.log_file = args.log_file
        self.output_dir = args.output_dir
        self.realtime = args.realtime
        self.debug = args.debug
        self.server.port = args.port

    def get_log_path(self) -> Path:
        """Get absolute path to log file"""
        log_path = Path(self.log_file)
        if not log_path.is_absolute():
            # Make relative to project root (parent of src directory)
            project_root = Path(__file__).parent.parent.parent
            log_path = project_root / log_path
        return log_path

    def get_output_path(self) -> Path:
        """Get absolute path to output directory"""
        output_path = Path(self.output_dir)
        if not output_path.is_absolute():
            # Make relative to project root (parent of src directory)
            project_root = Path(__file__).parent.parent.parent
            output_path = project_root / output_path
        return output_path
