"""
Configuration Management Module

Handles loading and managing configuration from YAML files and environment variables.
Provides centralized access to application settings.
"""

import os
import yaml
import logging
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """Configuration manager for the Smart Log Analyzer."""
    
    def __init__(self, config_path: str = "configs/config.yaml"):
        """Initialize configuration from file and environment variables."""
        self.config_path = config_path
        self.config_data = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file and environment variables."""
        # Load from file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as file:
                    self.config_data = yaml.safe_load(file) or {}
                logging.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logging.warning(f"Failed to load config file {self.config_path}: {e}")
                self.config_data = {}
        else:
            logging.warning(f"Config file not found: {self.config_path}, using defaults")
            self.config_data = self._get_default_config()
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "app": {
                "name": "Smart Log Analyzer",
                "version": "1.0.0",
                "log_level": "INFO"
            },
            "processing": {
                "batch_size": 1000,
                "max_file_size": "1GB",
                "supported_formats": ["json", "text"],
                "parallel_processing": False
            },
            "pattern_detection": {
                "min_frequency": 3,
                "time_window": 60,
                "enable_regex_patterns": True,
                "enable_temporal_analysis": True
            },
            "machine_learning": {
                "model_path": "data/models/",
                "retrain_threshold": 0.85,
                "feature_extraction": {
                    "use_tfidf": True,
                    "max_features": 5000,
                    "ngram_range": [1, 2],
                    "use_word_embeddings": False
                },
                "models": {
                    "error_classifier": {
                        "algorithm": "random_forest",
                        "parameters": {
                            "n_estimators": 100,
                            "max_depth": 10,
                            "random_state": 42
                        }
                    },
                    "anomaly_detector": {
                        "algorithm": "isolation_forest",
                        "parameters": {
                            "contamination": 0.1,
                            "random_state": 42
                        }
                    }
                }
            },
            "output": {
                "format": "json",
                "include_raw_logs": False,
                "generate_reports": True,
                "max_sample_entries": 5
            },
            "component_mappings": {
                "virtualization-aggregator-kafka": {
                    "type": "message_queue",
                    "priority": "high",
                    "team": "platform"
                },
                "virtualization-aggregator-postgres": {
                    "type": "database",
                    "priority": "critical",
                    "team": "data"
                },
                "virtualization-aggregator-grpc": {
                    "type": "rpc_service",
                    "priority": "high",
                    "team": "platform"
                },
                "virtualization-aggregator-rest": {
                    "type": "web_service",
                    "priority": "high",
                    "team": "platform"
                }
            },
            "jira": {
                "enabled": False,
                "server": "",
                "username": "",
                "api_token": "",
                "project": "INFRA",
                "default_issue_type": "Bug",
                "default_priority": "Medium"
            },
            "defect_templates": {
                "database_error": {
                    "issue_type": "Bug",
                    "priority": "High",
                    "components": ["Database"],
                    "labels": ["automated", "log-analysis", "database"]
                },
                "connection_error": {
                    "issue_type": "Bug", 
                    "priority": "Medium",
                    "components": ["Infrastructure"],
                    "labels": ["automated", "log-analysis", "connectivity"]
                },
                "authentication_error": {
                    "issue_type": "Bug",
                    "priority": "High",
                    "components": ["Security"],
                    "labels": ["automated", "log-analysis", "security"]
                }
            }
        }
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        # Application settings
        if os.getenv("SLA_LOG_LEVEL"):
            self.config_data.setdefault("app", {})["log_level"] = os.getenv("SLA_LOG_LEVEL")
        
        # Model path
        if os.getenv("SLA_MODEL_PATH"):
            self.config_data.setdefault("machine_learning", {})["model_path"] = os.getenv("SLA_MODEL_PATH")
        
        # Jira settings
        if os.getenv("JIRA_SERVER"):
            self.config_data.setdefault("jira", {})["server"] = os.getenv("JIRA_SERVER")
        
        if os.getenv("JIRA_USERNAME"):
            self.config_data.setdefault("jira", {})["username"] = os.getenv("JIRA_USERNAME")
        
        if os.getenv("JIRA_API_TOKEN"):
            self.config_data.setdefault("jira", {})["api_token"] = os.getenv("JIRA_API_TOKEN")
            self.config_data.setdefault("jira", {})["enabled"] = True
        
        if os.getenv("JIRA_PROJECT"):
            self.config_data.setdefault("jira", {})["project"] = os.getenv("JIRA_PROJECT")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'app.name')."""
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self.config_data
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.config_data.get(section, {})
    
    def get_jira_config(self) -> Dict[str, Any]:
        """Get Jira configuration with validation."""
        jira_config = self.get_section("jira")
        
        # Validate required fields if Jira is enabled
        if jira_config.get("enabled", False):
            required_fields = ["server", "username", "api_token", "project"]
            missing_fields = [field for field in required_fields if not jira_config.get(field)]
            
            if missing_fields:
                logging.warning(f"Jira enabled but missing required fields: {missing_fields}")
                jira_config["enabled"] = False
        
        return jira_config
    
    def get_ml_config(self) -> Dict[str, Any]:
        """Get machine learning configuration."""
        return self.get_section("machine_learning")
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return self.get_section("processing")
    
    def get_component_mappings(self) -> Dict[str, Any]:
        """Get component mappings configuration."""
        return self.get_section("component_mappings")
    
    def get_defect_templates(self) -> Dict[str, Any]:
        """Get defect template configurations."""
        return self.get_section("defect_templates")
    
    def is_jira_enabled(self) -> bool:
        """Check if Jira integration is enabled and properly configured."""
        jira_config = self.get_jira_config()
        return jira_config.get("enabled", False)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation results."""
        issues = []
        warnings = []
        
        # Check model path
        model_path = self.get("machine_learning.model_path")
        if model_path and not os.path.exists(model_path):
            warnings.append(f"Model path does not exist: {model_path}")
        
        # Check Jira config if enabled
        if self.get("jira.enabled", False):
            required_jira_fields = ["server", "username", "api_token", "project"]
            for field in required_jira_fields:
                if not self.get(f"jira.{field}"):
                    issues.append(f"Jira enabled but missing required field: {field}")
        
        # Check processing limits
        batch_size = self.get("processing.batch_size", 1000)
        if batch_size <= 0:
            issues.append("Processing batch_size must be greater than 0")
        
        # Check pattern detection settings
        min_frequency = self.get("pattern_detection.min_frequency", 3)
        if min_frequency < 1:
            issues.append("Pattern detection min_frequency must be at least 1")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    def save_config(self, output_path: Optional[str] = None):
        """Save current configuration to file."""
        output_path = output_path or self.config_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as file:
            yaml.dump(self.config_data, file, default_flow_style=False, indent=2)
        
        logging.info(f"Configuration saved to {output_path}")
    
    def reload_config(self):
        """Reload configuration from file."""
        self._load_config()
        logging.info("Configuration reloaded")
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"Config(path={self.config_path}, sections={list(self.config_data.keys())})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Config(path={self.config_path}, data_keys={list(self.config_data.keys())})"
