"""
Defect Generator Module

Generates structured defect reports and issue templates based on detected patterns.
Integrates with issue tracking systems like Jira for automated defect creation.
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter

from ..utils.config import Config


class DefectGenerator:
    """Generates defect reports and templates from detected patterns."""
    
    def __init__(self, config: Config):
        """Initialize defect generator with configuration."""
        self.config = config
        self.defect_templates = config.get_defect_templates()
        
        # Severity mapping
        self.severity_priority_map = {
            "critical": "P1",
            "high": "P2", 
            "medium": "P3",
            "low": "P4"
        }
        
        # Pattern to defect type mapping
        self.pattern_defect_map = {
            "connection_refused": "connection_error",
            "database_error": "database_error",
            "authentication_failure": "authentication_error",
            "startup_failure": "startup_failure",
            "timeout": "connection_error",
            "out_of_memory": "performance_error",
            "service_unavailable": "service_error"
        }
    
    def generate_defects(self, patterns: List[Dict[str, Any]], log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate defect templates from detected patterns."""
        logging.info(f"Generating defects from {len(patterns)} patterns")
        
        defects = []
        
        for pattern in patterns:
            try:
                defect = self._create_defect_from_pattern(pattern, log_entries)
                if defect:
                    defects.append(defect)
            except Exception as e:
                logging.error(f"Failed to create defect from pattern {pattern.get('pattern_id', 'unknown')}: {e}")
                continue
        
        # Merge similar defects
        merged_defects = self._merge_similar_defects(defects)
        
        logging.info(f"Generated {len(merged_defects)} defect templates")
        return merged_defects
    
    def _create_defect_from_pattern(self, pattern: Dict[str, Any], log_entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a defect template from a single pattern."""
        pattern_type = pattern.get("type", "unknown")
        pattern_id = pattern.get("pattern_id", "unknown")
        severity = pattern.get("severity", "medium")
        
        # Determine defect type from pattern
        defect_type = self._determine_defect_type(pattern)
        
        # Get template configuration
        template_config = self.defect_templates.get(defect_type, self.defect_templates.get("default", {}))
        
        # Generate title and description
        title = self._generate_title(pattern)
        description = self._generate_description(pattern, log_entries)
        
        # Get affected components
        components = pattern.get("affected_components", [])
        
        # Create defect template
        defect = {
            "defect_id": f"SLA_{pattern_id}_{int(datetime.now().timestamp())}",
            "title": title,
            "description": description,
            "severity": severity,
            "priority": self._map_severity_to_priority(severity, template_config),
            "issue_type": template_config.get("issue_type", "Bug"),
            "components": self._resolve_components(components, template_config),
            "labels": self._generate_labels(pattern, template_config),
            "pattern_info": {
                "pattern_id": pattern_id,
                "pattern_type": pattern_type,
                "defect_type": defect_type,
                "frequency": pattern.get("frequency", pattern.get("match_count", 1)),
                "first_occurrence": pattern.get("first_occurrence", "unknown"),
                "last_occurrence": pattern.get("last_occurrence", "unknown")
            },
            "environment_info": self._extract_environment_info(pattern, log_entries),
            "reproduction_steps": self._generate_reproduction_steps(pattern),
            "error_details": self._extract_error_details(pattern),
            "suggested_fix": self._generate_suggested_fix(pattern),
            "created_at": datetime.now().isoformat(),
            "auto_generated": True
        }
        
        return defect
    
    def _determine_defect_type(self, pattern: Dict[str, Any]) -> str:
        """Determine defect type from pattern information."""
        pattern_name = pattern.get("pattern_name", "")
        pattern_type = pattern.get("type", "")
        
        # Check pattern name mapping
        if pattern_name in self.pattern_defect_map:
            return self.pattern_defect_map[pattern_name]
        
        # Check pattern content for keywords
        error_message = pattern.get("error_message", "").lower()
        description = pattern.get("description", "").lower()
        
        text_to_analyze = f"{error_message} {description} {pattern_name}".lower()
        
        if any(keyword in text_to_analyze for keyword in ["database", "db", "sql", "postgres"]):
            return "database_error"
        elif any(keyword in text_to_analyze for keyword in ["connection", "refused", "timeout", "network"]):
            return "connection_error"
        elif any(keyword in text_to_analyze for keyword in ["auth", "authentication", "login", "permission"]):
            return "authentication_error"
        elif any(keyword in text_to_analyze for keyword in ["startup", "initialization", "start"]):
            return "startup_failure"
        elif any(keyword in text_to_analyze for keyword in ["memory", "oom", "performance"]):
            return "performance_error"
        elif any(keyword in text_to_analyze for keyword in ["service", "unavailable", "down"]):
            return "service_error"
        else:
            return "general_error"
    
    def _generate_title(self, pattern: Dict[str, Any]) -> str:
        """Generate a descriptive title for the defect."""
        pattern_type = pattern.get("type", "unknown")
        severity = pattern.get("severity", "medium")
        frequency = pattern.get("frequency", pattern.get("match_count", 1))
        
        # Get main error description
        if pattern.get("error_message"):
            main_error = pattern["error_message"][:100]
        elif pattern.get("description"):
            main_error = pattern["description"]
        else:
            main_error = f"Pattern {pattern.get('pattern_id', 'unknown')}"
        
        # Get affected components
        components = pattern.get("affected_components", [])
        component_str = f" in {', '.join(components[:2])}" if components else ""
        
        # Generate title based on pattern type
        if pattern_type == "error_frequency":
            title = f"Recurring Error: {main_error}{component_str} (x{frequency})"
        elif pattern_type == "temporal_clustering":
            title = f"Error Burst: {frequency} errors{component_str}"
        elif pattern_type == "component_specific":
            component = pattern.get("component", "Unknown Component")
            title = f"High Error Rate in {component} ({frequency} errors)"
        elif pattern_type == "regex_pattern":
            pattern_name = pattern.get("pattern_name", "unknown").replace("_", " ").title()
            title = f"{pattern_name} Detected{component_str} (x{frequency})"
        else:
            title = f"Log Analysis Issue: {main_error}{component_str}"
        
        # Add severity indicator for critical issues
        if severity == "critical":
            title = f"[CRITICAL] {title}"
        elif severity == "high":
            title = f"[HIGH] {title}"
        
        return title[:200]  # Limit title length
    
    def _generate_description(self, pattern: Dict[str, Any], log_entries: List[Dict[str, Any]]) -> str:
        """Generate detailed description for the defect."""
        description_parts = []
        
        # Overview
        description_parts.append("## Issue Overview")
        description_parts.append(f"Automated analysis detected a pattern in the application logs:")
        description_parts.append(f"- **Pattern Type**: {pattern.get('type', 'unknown')}")
        description_parts.append(f"- **Severity**: {pattern.get('severity', 'medium').upper()}")
        description_parts.append(f"- **Frequency**: {pattern.get('frequency', pattern.get('match_count', 1))}")
        
        if pattern.get("first_occurrence") and pattern.get("last_occurrence"):
            description_parts.append(f"- **Time Range**: {pattern['first_occurrence']} to {pattern['last_occurrence']}")
        
        # Error Details
        if pattern.get("error_message"):
            description_parts.append("\n## Error Message")
            description_parts.append(f"```\n{pattern['error_message']}\n```")
        
        # Affected Components
        components = pattern.get("affected_components", [])
        if components:
            description_parts.append("\n## Affected Components")
            for component in components:
                description_parts.append(f"- {component}")
        
        # Pattern-specific details
        self._add_pattern_specific_details(pattern, description_parts)
        
        # Sample log entries
        sample_entries = pattern.get("sample_entries", [])
        if sample_entries:
            description_parts.append("\n## Sample Log Entries")
            for i, entry in enumerate(sample_entries[:3], 1):
                description_parts.append(f"\n### Sample {i}")
                description_parts.append(f"**Timestamp**: {entry.get('timestamp', 'unknown')}")
                description_parts.append(f"**Message**: {entry.get('message', 'N/A')}")
                if entry.get('error'):
                    description_parts.append(f"**Error**: {entry['error']}")
                if entry.get('component'):
                    description_parts.append(f"**Component**: {entry['component']}")
        
        # Analysis metadata
        description_parts.append("\n## Analysis Information")
        description_parts.append(f"- **Pattern ID**: {pattern.get('pattern_id', 'unknown')}")
        description_parts.append(f"- **Detection Method**: Smart Log Analyzer")
        description_parts.append(f"- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(description_parts)
    
    def _add_pattern_specific_details(self, pattern: Dict[str, Any], description_parts: List[str]):
        """Add pattern-specific details to description."""
        pattern_type = pattern.get("type", "")
        
        if pattern_type == "temporal_clustering":
            description_parts.append("\n## Temporal Analysis")
            description_parts.append(f"- **Time Window**: {pattern.get('time_window', 'unknown')}")
            description_parts.append(f"- **Error Count in Window**: {pattern.get('error_count', 0)}")
            
            error_types = pattern.get("error_types", [])
            if error_types:
                description_parts.append("- **Error Types in Burst**:")
                for error_type in error_types:
                    description_parts.append(f"  - {error_type}")
        
        elif pattern_type == "component_specific":
            description_parts.append("\n## Component Analysis")
            description_parts.append(f"- **Component**: {pattern.get('component', 'unknown')}")
            description_parts.append(f"- **Error Rate**: {pattern.get('error_rate', 0):.1f}%")
            
            top_errors = pattern.get("top_error_types", {})
            if top_errors:
                description_parts.append("- **Top Error Types**:")
                for error, count in top_errors.items():
                    description_parts.append(f"  - {error}: {count} occurrences")
        
        elif pattern_type == "regex_pattern":
            description_parts.append("\n## Pattern Matching")
            description_parts.append(f"- **Pattern Name**: {pattern.get('pattern_name', 'unknown')}")
            description_parts.append(f"- **Regex**: `{pattern.get('regex', 'N/A')}`")
            description_parts.append(f"- **Match Count**: {pattern.get('match_count', 0)}")
        
        elif pattern_type == "error_sequence":
            description_parts.append("\n## Sequence Analysis")
            sequence = pattern.get("sequence", [])
            if sequence:
                description_parts.append("- **Error Sequence**:")
                for i, step in enumerate(sequence, 1):
                    description_parts.append(f"  {i}. {step}")
    
    def _map_severity_to_priority(self, severity: str, template_config: Dict[str, Any]) -> str:
        """Map severity to priority using template configuration."""
        severity_mapping = template_config.get("severity_mapping", {})
        
        if severity in severity_mapping:
            return severity_mapping[severity]
        
        return self.severity_priority_map.get(severity, "P3")
    
    def _resolve_components(self, pattern_components: List[str], template_config: Dict[str, Any]) -> List[str]:
        """Resolve components from pattern and template configuration."""
        components = template_config.get("components", []).copy()
        
        # Add pattern-specific components
        for component in pattern_components:
            # Map component names to Jira components
            mapped_component = self._map_component_name(component)
            if mapped_component and mapped_component not in components:
                components.append(mapped_component)
        
        return components
    
    def _map_component_name(self, component: str) -> str:
        """Map log component names to Jira component names."""
        component_mapping = {
            "kafka": "Message Queue",
            "postgres": "Database",
            "grpc": "API Services",
            "rest": "Web Services",
            "relay": "Infrastructure"
        }
        
        component_lower = component.lower()
        
        for key, value in component_mapping.items():
            if key in component_lower:
                return value
        
        # Return capitalized component name as fallback
        return component.replace("-", " ").replace("_", " ").title()
    
    def _generate_labels(self, pattern: Dict[str, Any], template_config: Dict[str, Any]) -> List[str]:
        """Generate labels for the defect."""
        labels = template_config.get("labels", []).copy()
        
        # Add pattern-specific labels
        pattern_type = pattern.get("type", "")
        if pattern_type:
            labels.append(f"pattern-{pattern_type}")
        
        severity = pattern.get("severity", "")
        if severity:
            labels.append(f"severity-{severity}")
        
        # Add component-based labels
        components = pattern.get("affected_components", [])
        for component in components[:3]:  # Limit to 3 components
            clean_component = re.sub(r'[^a-zA-Z0-9]', '-', component.lower())
            labels.append(f"component-{clean_component}")
        
        return list(set(labels))  # Remove duplicates
    
    def _extract_environment_info(self, pattern: Dict[str, Any], log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract environment information from pattern and log entries."""
        env_info = {
            "log_sources": [],
            "affected_services": pattern.get("affected_components", []),
            "time_range": {
                "start": pattern.get("first_occurrence", "unknown"),
                "end": pattern.get("last_occurrence", "unknown")
            }
        }
        
        # Extract unique file paths
        sample_entries = pattern.get("sample_entries", [])
        file_paths = set()
        for entry in sample_entries:
            if entry.get("file_path"):
                file_paths.add(entry["file_path"])
        
        env_info["log_sources"] = list(file_paths)
        
        return env_info
    
    def _generate_reproduction_steps(self, pattern: Dict[str, Any]) -> List[str]:
        """Generate reproduction steps based on pattern information."""
        steps = []
        
        pattern_type = pattern.get("type", "")
        components = pattern.get("affected_components", [])
        
        if pattern_type == "error_frequency":
            steps.append("1. Monitor application logs for the specific error message")
            steps.append("2. Check if the error occurs consistently across multiple requests")
            steps.append("3. Review the affected component configuration and connectivity")
        
        elif pattern_type == "temporal_clustering":
            steps.append("1. Monitor logs during the identified time window")
            steps.append("2. Check system resource usage during error bursts")
            steps.append("3. Review load balancing and scaling configuration")
        
        elif pattern_type == "component_specific":
            component = pattern.get("component", "unknown")
            steps.append(f"1. Access the {component} service logs")
            steps.append(f"2. Reproduce operations that trigger errors in {component}")
            steps.append(f"3. Check {component} service health and configuration")
        
        else:
            steps.append("1. Review the provided log entries and error patterns")
            steps.append("2. Attempt to reproduce the conditions that trigger the error")
            steps.append("3. Monitor system behavior and log output")
        
        if components:
            steps.append(f"4. Focus investigation on: {', '.join(components)}")
        
        return steps
    
    def _extract_error_details(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed error information from pattern."""
        error_details = {}
        
        if pattern.get("error_message"):
            error_details["primary_error"] = pattern["error_message"]
        
        if pattern.get("regex"):
            error_details["pattern_regex"] = pattern["regex"]
        
        sample_entries = pattern.get("sample_entries", [])
        if sample_entries:
            stack_traces = []
            error_codes = []
            
            for entry in sample_entries:
                if entry.get("stacktrace"):
                    stack_traces.append(entry["stacktrace"])
                
                if entry.get("error_details", {}).get("error_code"):
                    error_codes.append(entry["error_details"]["error_code"])
            
            if stack_traces:
                error_details["stack_traces"] = stack_traces[:2]  # Include first 2
            
            if error_codes:
                error_details["error_codes"] = list(set(error_codes))
        
        return error_details
    
    def _generate_suggested_fix(self, pattern: Dict[str, Any]) -> List[str]:
        """Generate suggested fix based on pattern type and content."""
        suggestions = []
        
        pattern_name = pattern.get("pattern_name", "")
        pattern_type = pattern.get("type", "")
        
        # Pattern-specific suggestions
        if pattern_name == "connection_refused":
            suggestions.extend([
                "Check database connectivity and network configuration",
                "Verify database service is running and accessible",
                "Review connection pool settings and timeouts",
                "Check firewall rules and network policies"
            ])
        
        elif pattern_name == "database_error":
            suggestions.extend([
                "Review database logs for detailed error information",
                "Check database disk space and memory usage",
                "Verify database schema and migration status",
                "Review database connection configuration"
            ])
        
        elif pattern_name == "authentication_failure":
            suggestions.extend([
                "Verify authentication credentials and certificates",
                "Check authentication service availability",
                "Review user permissions and access policies",
                "Validate authentication configuration"
            ])
        
        elif pattern_name == "out_of_memory":
            suggestions.extend([
                "Increase memory allocation for the affected service",
                "Review memory usage patterns and optimize code",
                "Check for memory leaks in the application",
                "Consider horizontal scaling or load balancing"
            ])
        
        elif pattern_type == "temporal_clustering":
            suggestions.extend([
                "Investigate system load during error burst periods",
                "Review auto-scaling configuration and thresholds",
                "Check for external factors causing load spikes",
                "Consider implementing circuit breaker patterns"
            ])
        
        # Component-specific suggestions
        components = pattern.get("affected_components", [])
        for component in components:
            if "kafka" in component.lower():
                suggestions.append("Review Kafka broker health and partition distribution")
            elif "postgres" in component.lower():
                suggestions.append("Check PostgreSQL performance metrics and query optimization")
            elif "grpc" in component.lower():
                suggestions.append("Review gRPC service configuration and network timeouts")
        
        # Generic suggestions if no specific ones found
        if not suggestions:
            suggestions.extend([
                "Review application logs for additional context",
                "Check service health and resource utilization",
                "Verify configuration settings and dependencies",
                "Consider implementing additional monitoring and alerting"
            ])
        
        return suggestions
    
    def _merge_similar_defects(self, defects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge similar defects to avoid duplication."""
        if len(defects) <= 1:
            return defects
        
        merged = []
        used_indices = set()
        
        for i, defect in enumerate(defects):
            if i in used_indices:
                continue
            
            similar_defects = [defect]
            used_indices.add(i)
            
            # Find similar defects
            for j, other_defect in enumerate(defects[i+1:], i+1):
                if j in used_indices:
                    continue
                
                if self._are_defects_similar(defect, other_defect):
                    similar_defects.append(other_defect)
                    used_indices.add(j)
            
            # Merge if we found similar defects
            if len(similar_defects) > 1:
                merged_defect = self._merge_defect_group(similar_defects)
                merged.append(merged_defect)
            else:
                merged.append(defect)
        
        return merged
    
    def _are_defects_similar(self, defect1: Dict[str, Any], defect2: Dict[str, Any]) -> bool:
        """Check if two defects are similar enough to merge."""
        # Check if they have similar titles (80% similarity)
        title1 = defect1.get("title", "").lower()
        title2 = defect2.get("title", "").lower()
        
        # Simple similarity check based on common words
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        common_words = words1.intersection(words2)
        similarity = len(common_words) / max(len(words1), len(words2))
        
        if similarity < 0.6:
            return False
        
        # Check if they affect the same components
        components1 = set(defect1.get("components", []))
        components2 = set(defect2.get("components", []))
        
        if components1 and components2 and not components1.intersection(components2):
            return False
        
        return True
    
    def _merge_defect_group(self, defects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge a group of similar defects into one."""
        if len(defects) == 1:
            return defects[0]
        
        base_defect = defects[0].copy()
        
        # Combine frequencies
        total_frequency = sum(
            defect.get("pattern_info", {}).get("frequency", 1) 
            for defect in defects
        )
        base_defect["pattern_info"]["frequency"] = total_frequency
        
        # Combine components
        all_components = set()
        for defect in defects:
            all_components.update(defect.get("components", []))
        base_defect["components"] = list(all_components)
        
        # Combine labels
        all_labels = set()
        for defect in defects:
            all_labels.update(defect.get("labels", []))
        base_defect["labels"] = list(all_labels)
        
        # Update title to reflect merging
        base_defect["title"] = f"[MERGED] {base_defect['title']} (x{total_frequency})"
        
        # Add merge information
        base_defect["merged_from"] = [
            defect.get("pattern_info", {}).get("pattern_id", "unknown") 
            for defect in defects
        ]
        
        return base_defect
