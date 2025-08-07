"""
Data models for AI Driven Realtime Log Analyser
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ComponentType(Enum):
    """Supported component types"""
    VIRTUALIZATION_AGGREGATOR = "VA"
    COMMON_VIRTUALIZATION_PROVIDER = "CVP"
    VIRTUAL_MANAGER = "VM"
    VMOPS = "VMOPS"
    DATA_SERVICES_CONNECTOR = "DSC"
    NIMBLE_VIRT_MANAGER = "NVM"
    PCBE_CCA = "PCBE"
    UNKNOWN = "UNKNOWN"


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: Optional[datetime] = None
    level: str = "INFO"
    component: Optional[str] = None
    message: str = ""
    thread: Optional[str] = None
    logger: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    line_number: int = 0
    
    def __post_init__(self):
        # Normalize level
        if self.level:
            self.level = self.level.upper()
        
        # Determine component type if not set
        if not self.component and self.message:
            self.component = self._infer_component()
    
    def _infer_component(self) -> str:
        """Infer component from message content"""
        message_lower = self.message.lower()
        
        if any(keyword in message_lower for keyword in ["virtualization", "aggregator"]):
            return ComponentType.VIRTUALIZATION_AGGREGATOR.value
        elif any(keyword in message_lower for keyword in ["common", "provider"]):
            return ComponentType.COMMON_VIRTUALIZATION_PROVIDER.value
        elif "vmops" in message_lower:
            return ComponentType.VMOPS.value
        elif any(keyword in message_lower for keyword in ["nimble", "virt"]):
            return ComponentType.NIMBLE_VIRT_MANAGER.value
        elif "pcbe" in message_lower:
            return ComponentType.PCBE_CCA.value
        elif any(keyword in message_lower for keyword in ["data", "connector"]):
            return ComponentType.DATA_SERVICES_CONNECTOR.value
        
        return ComponentType.UNKNOWN.value
    
    def is_error(self) -> bool:
        """Check if this is an error entry"""
        return self.level in ["ERROR", "FATAL"]
    
    def is_warning(self) -> bool:
        """Check if this is a warning entry"""
        return self.level == "WARN"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level,
            "component": self.component,
            "message": self.message,
            "thread": self.thread,
            "logger": self.logger,
            "line_number": self.line_number,
            "raw_data": self.raw_data
        }


@dataclass
class AnalysisResult:
    """Represents analysis results for a log entry or pattern"""
    entry_id: str
    analysis_type: str  # "pattern", "anomaly", "classification"
    confidence: float
    result: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ErrorPattern:
    """Represents a detected error pattern"""
    pattern: str
    count: int
    severity: str = "MEDIUM"
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    component: Optional[str] = None
    examples: List[str] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []


@dataclass
class ComponentStats:
    """Statistics for a specific component"""
    component: str
    total_entries: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    debug_count: int = 0
    first_entry: Optional[datetime] = None
    last_entry: Optional[datetime] = None
    top_errors: List[str] = None
    
    def __post_init__(self):
        if self.top_errors is None:
            self.top_errors = []
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage"""
        if self.total_entries == 0:
            return 0.0
        return (self.error_count / self.total_entries) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "component": self.component,
            "total_entries": self.total_entries,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "debug_count": self.debug_count,
            "error_rate": self.error_rate,
            "first_entry": self.first_entry.isoformat() if self.first_entry else None,
            "last_entry": self.last_entry.isoformat() if self.last_entry else None,
            "top_errors": self.top_errors
        }


@dataclass
class AnalysisSummary:
    """Overall analysis summary"""
    total_entries: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    unique_components: int = 0
    patterns_detected: int = 0
    anomalies_detected: int = 0
    processing_time: float = 0.0
    analysis_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()
    
    @property
    def error_rate(self) -> float:
        """Calculate overall error rate"""
        if self.total_entries == 0:
            return 0.0
        return (self.total_errors / self.total_entries) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_entries": self.total_entries,
            "total_errors": self.total_errors,
            "total_warnings": self.total_warnings,
            "unique_components": self.unique_components,
            "patterns_detected": self.patterns_detected,
            "anomalies_detected": self.anomalies_detected,
            "processing_time": self.processing_time,
            "error_rate": self.error_rate,
            "analysis_timestamp": self.analysis_timestamp.isoformat()
        }
