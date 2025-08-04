"""
Jira Client Module

Provides integration with Jira for automated defect creation and management.
Handles authentication, issue creation, and status tracking.
"""

import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utils.config import Config
from ..utils.logger import StructuredLogger


class JiraClient:
    """Client for Jira API integration."""
    
    def __init__(self, config: Config):
        """Initialize Jira client with configuration."""
        self.config = config
        self.jira_config = config.get_jira_config()
        self.logger = StructuredLogger(__name__)
        
        # Jira settings
        self.server = self.jira_config.get("server", "")
        self.username = self.jira_config.get("username", "")
        self.api_token = self.jira_config.get("api_token", "")
        self.project = self.jira_config.get("project", "")
        
        # Validation
        self.is_configured = self._validate_configuration()
        
        # Session for requests
        self.session = requests.Session()
        if self.is_configured:
            self.session.auth = (self.username, self.api_token)
            self.session.headers.update({
                "Accept": "application/json",
                "Content-Type": "application/json"
            })
    
    def _validate_configuration(self) -> bool:
        """Validate Jira configuration."""
        required_fields = ["server", "username", "api_token", "project"]
        missing_fields = []
        
        for field in required_fields:
            if not self.jira_config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            self.logger.logger.warning(f"Jira configuration incomplete. Missing: {missing_fields}")
            return False
        
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Jira instance."""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Jira not configured properly"
            }
        
        try:
            url = f"{self.server}/rest/api/3/myself"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                user_info = response.json()
                self.logger.logger.info("Jira connection test successful")
                return {
                    "success": True,
                    "user": user_info.get("displayName", "Unknown"),
                    "account_id": user_info.get("accountId", "")
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            self.logger.logger.error(f"Jira connection test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_issue(self, defect: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Jira issue from defect template."""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Jira not configured properly"
            }
        
        try:
            # Prepare issue data
            issue_data = self._prepare_issue_data(defect)
            
            # Create issue
            url = f"{self.server}/rest/api/3/issue"
            response = self.session.post(url, json=issue_data, timeout=30)
            
            if response.status_code == 201:
                issue_info = response.json()
                issue_key = issue_info.get("key")
                
                self.logger.log_defect_generated(
                    defect_title=defect.get("title", ""),
                    severity=defect.get("severity", ""),
                    component=", ".join(defect.get("components", []))
                )
                
                return {
                    "success": True,
                    "issue_key": issue_key,
                    "issue_url": f"{self.server}/browse/{issue_key}",
                    "issue_id": issue_info.get("id")
                }
            else:
                error_details = response.json() if response.content else {"message": "Unknown error"}
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_details}",
                    "response": response.text
                }
                
        except Exception as e:
            self.logger.logger.error(f"Failed to create Jira issue: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_issue_data(self, defect: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare issue data for Jira API."""
        issue_type = defect.get("issue_type", self.jira_config.get("default_issue_type", "Bug"))
        priority = defect.get("priority", self.jira_config.get("default_priority", "Medium"))
        
        # Build description with markdown formatting
        description = self._format_description_for_jira(defect)
        
        # Prepare issue fields
        fields = {
            "project": {"key": self.project},
            "summary": defect.get("title", "Automated Log Analysis Issue"),
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {"name": issue_type}
        }
        
        # Add priority if supported
        try:
            fields["priority"] = {"name": priority}
        except:
            pass  # Priority field might not be available
        
        # Add components
        components = defect.get("components", [])
        if components:
            fields["components"] = [{"name": comp} for comp in components]
        
        # Add labels
        labels = defect.get("labels", [])
        if labels:
            fields["labels"] = labels
        
        # Add custom fields if configured
        field_mappings = self.jira_config.get("field_mappings", {})
        self._add_custom_fields(fields, defect, field_mappings)
        
        return {"fields": fields}
    
    def _format_description_for_jira(self, defect: Dict[str, Any]) -> str:
        """Format defect description for Jira."""
        description_parts = []
        
        # Basic information
        description_parts.append("*Automated Issue Detection Report*")
        description_parts.append("")
        description_parts.append(f"*Severity:* {defect.get('severity', 'Unknown').upper()}")
        description_parts.append(f"*Detection Date:* {defect.get('created_at', datetime.now().isoformat())}")
        description_parts.append(f"*Pattern ID:* {defect.get('pattern_info', {}).get('pattern_id', 'Unknown')}")
        description_parts.append("")
        
        # Main description
        if defect.get("description"):
            # Convert markdown to Jira format (simplified)
            jira_description = defect["description"].replace("## ", "*").replace("**", "*")
            description_parts.append(jira_description)
        
        # Environment information
        env_info = defect.get("environment_info", {})
        if env_info:
            description_parts.append("")
            description_parts.append("*Environment Information:*")
            for key, value in env_info.items():
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                description_parts.append(f"- {key}: {value}")
        
        # Reproduction steps
        repro_steps = defect.get("reproduction_steps", [])
        if repro_steps:
            description_parts.append("")
            description_parts.append("*Reproduction Steps:*")
            for step in repro_steps:
                description_parts.append(f"# {step}")
        
        # Suggested fixes
        suggested_fixes = defect.get("suggested_fix", [])
        if suggested_fixes:
            description_parts.append("")
            description_parts.append("*Suggested Actions:*")
            for fix in suggested_fixes:
                description_parts.append(f"- {fix}")
        
        return "\n".join(description_parts)
    
    def _add_custom_fields(self, fields: Dict[str, Any], defect: Dict[str, Any], field_mappings: Dict[str, str]):
        """Add custom fields based on configuration."""
        # Map severity to custom field if configured
        severity_field = field_mappings.get("severity_field")
        if severity_field and defect.get("severity"):
            fields[severity_field] = {"value": defect["severity"].title()}
        
        # Map component to custom field if configured
        component_field = field_mappings.get("component_field")
        if component_field and defect.get("components"):
            fields[component_field] = [{"name": comp} for comp in defect["components"]]
        
        # Map team to assignee if configured
        team_field = field_mappings.get("team_field")
        if team_field and defect.get("pattern_info", {}).get("team"):
            team = defect["pattern_info"]["team"]
            # This would need team-to-user mapping configuration
            pass
    
    def update_issue(self, issue_key: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Jira issue."""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Jira not configured properly"
            }
        
        try:
            url = f"{self.server}/rest/api/3/issue/{issue_key}"
            response = self.session.put(url, json=update_data, timeout=30)
            
            if response.status_code == 204:
                return {
                    "success": True,
                    "message": f"Issue {issue_key} updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            self.logger.logger.error(f"Failed to update Jira issue {issue_key}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Get issue details from Jira."""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Jira not configured properly"
            }
        
        try:
            url = f"{self.server}/rest/api/3/issue/{issue_key}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                issue_data = response.json()
                return {
                    "success": True,
                    "issue": issue_data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            self.logger.logger.error(f"Failed to get Jira issue {issue_key}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_issues(self, jql: str, max_results: int = 50) -> Dict[str, Any]:
        """Search for issues using JQL."""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Jira not configured properly"
            }
        
        try:
            url = f"{self.server}/rest/api/3/search"
            params = {
                "jql": jql,
                "maxResults": max_results,
                "fields": "key,summary,status,priority,created,updated"
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                search_results = response.json()
                return {
                    "success": True,
                    "total": search_results.get("total", 0),
                    "issues": search_results.get("issues", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            self.logger.logger.error(f"Failed to search Jira issues: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_bulk_issues(self, defects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple issues in bulk."""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Jira not configured properly"
            }
        
        results = {
            "success": True,
            "created_issues": [],
            "failed_issues": [],
            "total_processed": len(defects)
        }
        
        for i, defect in enumerate(defects):
            try:
                result = self.create_issue(defect)
                
                if result["success"]:
                    results["created_issues"].append({
                        "defect_id": defect.get("defect_id", f"defect_{i}"),
                        "issue_key": result["issue_key"],
                        "issue_url": result["issue_url"]
                    })
                else:
                    results["failed_issues"].append({
                        "defect_id": defect.get("defect_id", f"defect_{i}"),
                        "error": result["error"]
                    })
                    results["success"] = False
                    
            except Exception as e:
                results["failed_issues"].append({
                    "defect_id": defect.get("defect_id", f"defect_{i}"),
                    "error": str(e)
                })
                results["success"] = False
        
        self.logger.logger.info(
            f"Bulk issue creation completed: {len(results['created_issues'])} created, "
            f"{len(results['failed_issues'])} failed"
        )
        
        return results
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get project information."""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Jira not configured properly"
            }
        
        try:
            url = f"{self.server}/rest/api/3/project/{self.project}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                project_data = response.json()
                return {
                    "success": True,
                    "project": project_data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            self.logger.logger.error(f"Failed to get project info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get comprehensive connection status."""
        status = {
            "configured": self.is_configured,
            "server": self.server,
            "project": self.project,
            "username": self.username
        }
        
        if self.is_configured:
            connection_test = self.test_connection()
            status.update(connection_test)
            
            if connection_test["success"]:
                project_info = self.get_project_info()
                status["project_accessible"] = project_info["success"]
        
        return status
