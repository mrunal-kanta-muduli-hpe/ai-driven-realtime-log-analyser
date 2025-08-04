"""
Component Filter Module

Filters log entries based on component IDs, service types, and other criteria.
Provides functionality to focus analysis on specific system components.
"""

import logging
import re
from typing import List, Dict, Any, Set, Optional

from ..utils.config import Config


class ComponentFilter:
    """Filters log entries by component, service, or other criteria."""
    
    def __init__(self, config: Config):
        """Initialize component filter with configuration."""
        self.config = config
        
        # Load component mappings from config
        self.component_mappings = config.get("component_mappings", {})
        
        # Common component patterns
        self.component_patterns = {
            "kafka": [
                r"kafka",
                r"virtualization-aggregator-kafka",
                r"message.*queue",
                r"streaming"
            ],
            "postgres": [
                r"postgres",
                r"postgresql", 
                r"virtualization-aggregator-postgres",
                r"database",
                r"db"
            ],
            "grpc": [
                r"grpc",
                r"virtualization-aggregator-grpc",
                r"rpc"
            ],
            "rest": [
                r"rest",
                r"virtualization-aggregator-rest",
                r"http",
                r"api"
            ],
            "relay": [
                r"relay",
                r"virtualization.*relay"
            ]
        }
    
    def filter_by_component(self, log_entries: List[Dict[str, Any]], component: str) -> List[Dict[str, Any]]:
        """Filter log entries by specific component."""
        logging.info(f"Filtering {len(log_entries)} entries by component: {component}")
        
        filtered_entries = []
        
        for entry in log_entries:
            if self._matches_component(entry, component):
                filtered_entries.append(entry)
        
        logging.info(f"Filtered to {len(filtered_entries)} entries")
        return filtered_entries
    
    def filter_by_component_type(self, log_entries: List[Dict[str, Any]], component_type: str) -> List[Dict[str, Any]]:
        """Filter log entries by component type (e.g., database, message_queue)."""
        logging.info(f"Filtering {len(log_entries)} entries by component type: {component_type}")
        
        filtered_entries = []
        
        for entry in log_entries:
            entry_component = self._extract_component(entry)
            if entry_component and self._get_component_type(entry_component) == component_type:
                filtered_entries.append(entry)
        
        logging.info(f"Filtered to {len(filtered_entries)} entries")
        return filtered_entries
    
    def filter_by_severity(self, log_entries: List[Dict[str, Any]], min_severity: str = "error") -> List[Dict[str, Any]]:
        """Filter log entries by minimum severity level."""
        severity_order = ["debug", "info", "warning", "error", "critical", "fatal"]
        min_level = severity_order.index(min_severity.lower()) if min_severity.lower() in severity_order else 0
        
        filtered_entries = []
        
        for entry in log_entries:
            entry_level = entry.get("level", "info").lower()
            if entry_level in severity_order:
                entry_level_idx = severity_order.index(entry_level)
                if entry_level_idx >= min_level:
                    filtered_entries.append(entry)
            elif entry.get("is_error", False):
                # If we can't determine level but it's marked as error
                filtered_entries.append(entry)
        
        logging.info(f"Filtered to {len(filtered_entries)} entries with severity >= {min_severity}")
        return filtered_entries
    
    def filter_by_time_range(self, log_entries: List[Dict[str, Any]], start_time: str = None, end_time: str = None) -> List[Dict[str, Any]]:
        """Filter log entries by time range."""
        if not start_time and not end_time:
            return log_entries
        
        filtered_entries = []
        
        for entry in log_entries:
            timestamp = entry.get("timestamp")
            if not timestamp:
                continue
            
            # Simple string comparison for now (assumes ISO format)
            include_entry = True
            
            if start_time and timestamp < start_time:
                include_entry = False
            
            if end_time and timestamp > end_time:
                include_entry = False
            
            if include_entry:
                filtered_entries.append(entry)
        
        logging.info(f"Filtered to {len(filtered_entries)} entries within time range")
        return filtered_entries
    
    def filter_by_error_pattern(self, log_entries: List[Dict[str, Any]], pattern: str) -> List[Dict[str, Any]]:
        """Filter log entries by error pattern (regex)."""
        filtered_entries = []
        
        for entry in log_entries:
            message = entry.get("message", "")
            error_details = entry.get("error", "")
            
            text_to_search = f"{message} {error_details}"
            
            if re.search(pattern, text_to_search, re.IGNORECASE):
                filtered_entries.append(entry)
        
        logging.info(f"Filtered to {len(filtered_entries)} entries matching pattern: {pattern}")
        return filtered_entries
    
    def group_by_component(self, log_entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group log entries by component."""
        groups = {}
        
        for entry in log_entries:
            component = self._extract_component(entry) or "unknown"
            
            if component not in groups:
                groups[component] = []
            
            groups[component].append(entry)
        
        logging.info(f"Grouped entries into {len(groups)} components")
        return groups
    
    def get_component_statistics(self, log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about components in log entries."""
        component_stats = {}
        groups = self.group_by_component(log_entries)
        
        for component, entries in groups.items():
            error_count = sum(1 for entry in entries if entry.get("is_error", False))
            warning_count = sum(1 for entry in entries if entry.get("is_warning", False))
            
            component_stats[component] = {
                "total_entries": len(entries),
                "error_count": error_count,
                "warning_count": warning_count,
                "error_rate": (error_count / len(entries) * 100) if entries else 0,
                "component_type": self._get_component_type(component),
                "first_entry": entries[0].get("timestamp") if entries else None,
                "last_entry": entries[-1].get("timestamp") if entries else None
            }
        
        return component_stats
    
    def _matches_component(self, entry: Dict[str, Any], target_component: str) -> bool:
        """Check if log entry matches target component."""
        entry_component = self._extract_component(entry)
        
        if not entry_component:
            return False
        
        # Direct match
        if entry_component.lower() == target_component.lower():
            return True
        
        # Pattern matching
        if target_component.lower() in self.component_patterns:
            patterns = self.component_patterns[target_component.lower()]
            
            # Check component field
            for pattern in patterns:
                if re.search(pattern, entry_component, re.IGNORECASE):
                    return True
            
            # Check message content
            message = entry.get("message", "")
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return True
        
        # Partial match
        if target_component.lower() in entry_component.lower():
            return True
        
        return False
    
    def _extract_component(self, entry: Dict[str, Any]) -> Optional[str]:
        """Extract component identifier from log entry."""
        # First check if component is already extracted
        if entry.get("component"):
            return entry["component"]
        
        # Try to extract from various fields
        component_fields = ["component", "service", "module", "application", "app", "source"]
        
        for field in component_fields:
            if field in entry:
                return str(entry[field])
        
        # Try to extract from message
        message = entry.get("message", "")
        if message:
            # Look for common component patterns
            patterns = [
                r'virtualization-aggregator-(\w+)',
                r'(\w+)-service',
                r'Starting (\w+) service',
                r'(\w+) application',
                r'\[(\w+)\]',
                r'(\w+):'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    return match.group(1).lower()
        
        # Try to extract from file path
        file_path = entry.get("file_path", "")
        if file_path:
            # Look for component names in file path
            for component_name in self.component_patterns.keys():
                if component_name in file_path.lower():
                    return component_name
        
        return None
    
    def _get_component_type(self, component: str) -> str:
        """Get component type from component name."""
        if not component:
            return "unknown"
        
        component_lower = component.lower()
        
        # Check configured mappings first
        for comp, config in self.component_mappings.items():
            if comp.lower() == component_lower:
                return config.get("type", "unknown")
        
        # Fallback to pattern-based detection
        type_patterns = {
            "database": ["postgres", "postgresql", "db", "database", "mysql", "mongodb"],
            "message_queue": ["kafka", "rabbitmq", "mq", "queue", "streaming"],
            "web_service": ["rest", "http", "api", "web", "service"],
            "rpc_service": ["grpc", "rpc"],
            "cache": ["redis", "memcached", "cache"],
            "storage": ["storage", "s3", "blob", "file"],
            "monitoring": ["prometheus", "grafana", "monitoring", "metrics"],
            "security": ["auth", "authentication", "security", "oauth"],
            "proxy": ["proxy", "nginx", "apache", "lb", "loadbalancer"]
        }
        
        for comp_type, patterns in type_patterns.items():
            if any(pattern in component_lower for pattern in patterns):
                return comp_type
        
        return "application"
    
    def get_available_components(self, log_entries: List[Dict[str, Any]]) -> Set[str]:
        """Get list of all available components in log entries."""
        components = set()
        
        for entry in log_entries:
            component = self._extract_component(entry)
            if component:
                components.add(component)
        
        return components
    
    def create_component_filter_suggestions(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create filter suggestions based on log content."""
        component_stats = self.get_component_statistics(log_entries)
        suggestions = []
        
        for component, stats in component_stats.items():
            if stats["error_count"] > 0:
                suggestion = {
                    "filter_type": "component",
                    "value": component,
                    "reason": f"Component has {stats['error_count']} errors ({stats['error_rate']:.1f}% error rate)",
                    "priority": "high" if stats["error_rate"] > 10 else "medium",
                    "expected_results": stats["error_count"]
                }
                suggestions.append(suggestion)
        
        # Sort by error count descending
        suggestions.sort(key=lambda x: x["expected_results"], reverse=True)
        
        return suggestions[:10]  # Top 10 suggestions
