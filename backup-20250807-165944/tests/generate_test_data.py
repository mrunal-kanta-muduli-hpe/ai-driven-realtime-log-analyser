"""
Test Data Generator for Smart Log Analyzer

Generates realistic test log data for testing and demonstration purposes.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import argparse


class TestDataGenerator:
    """Generate test log data with various patterns and scenarios."""
    
    def __init__(self):
        self.components = [
            "virtualization-aggregator-kafka",
            "virtualization-aggregator-postgres", 
            "virtualization-aggregator-rest",
            "nimble-virt-manager",
            "common-virtualization-provider",
            "data-services-connector-manager",
            "pcbe-cca-framework"
        ]
        
        self.error_patterns = [
            {
                "message": "Database connection failed",
                "error": "connection refused",
                "component": "postgres",
                "level": "error",
                "frequency": 0.15  # 15% chance
            },
            {
                "message": "Kafka producer timeout",
                "error": "timeout after 30s",
                "component": "kafka", 
                "level": "error",
                "frequency": 0.08  # 8% chance
            },
            {
                "message": "Memory usage exceeds threshold",
                "error": "heap memory > 85%",
                "component": "system",
                "level": "warn",
                "frequency": 0.12  # 12% chance
            },
            {
                "message": "API request rate limit exceeded",
                "error": "rate limit exceeded",
                "component": "rest",
                "level": "error", 
                "frequency": 0.05  # 5% chance
            },
            {
                "message": "SSL certificate validation failed",
                "error": "certificate expired",
                "component": "security",
                "level": "error",
                "frequency": 0.03  # 3% chance
            }
        ]
        
        self.info_messages = [
            "Service started successfully",
            "API request processed",
            "Database transaction committed",
            "Cache entry updated",
            "Health check passed",
            "Configuration loaded",
            "Session created",
            "Data synchronized",
            "Backup completed",
            "Metrics collected"
        ]
        
        self.warn_messages = [
            "High CPU usage detected",
            "Disk space running low",
            "Network latency increased",
            "Connection pool exhausted",
            "Queue size growing",
            "Response time degraded"
        ]
    
    def generate_timestamp(self, base_time, offset_minutes=0):
        """Generate timestamp with optional offset."""
        timestamp = base_time + timedelta(minutes=offset_minutes)
        return timestamp.isoformat() + "Z"
    
    def generate_log_entry(self, base_time, entry_number):
        """Generate a single log entry."""
        # Determine if this should be an error based on patterns
        for pattern in self.error_patterns:
            if random.random() < pattern["frequency"]:
                return {
                    "timestamp": self.generate_timestamp(base_time, entry_number),
                    "level": pattern["level"],
                    "message": pattern["message"],
                    "component": pattern["component"],
                    "error": pattern["error"],
                    "thread": f"thread-{random.randint(1, 10)}",
                    "requestId": f"req-{random.randint(1000, 9999)}",
                    "userId": f"user-{random.randint(1, 100)}" if random.random() < 0.3 else None
                }
        
        # Generate warning message
        if random.random() < 0.15:  # 15% warnings
            return {
                "timestamp": self.generate_timestamp(base_time, entry_number),
                "level": "warn",
                "message": random.choice(self.warn_messages),
                "component": random.choice(self.components).split("-")[-1],
                "thread": f"thread-{random.randint(1, 10)}",
                "requestId": f"req-{random.randint(1000, 9999)}"
            }
        
        # Generate info message (default)
        return {
            "timestamp": self.generate_timestamp(base_time, entry_number),
            "level": "info", 
            "message": random.choice(self.info_messages),
            "component": random.choice(self.components).split("-")[-1],
            "thread": f"thread-{random.randint(1, 10)}",
            "requestId": f"req-{random.randint(1000, 9999)}"
        }
    
    def generate_burst_pattern(self, base_time, entry_number, error_type):
        """Generate a burst of similar errors (simulates cascading failures)."""
        entries = []
        burst_size = random.randint(3, 8)
        
        for i in range(burst_size):
            entry = {
                "timestamp": self.generate_timestamp(base_time, entry_number + i),
                "level": "error",
                "message": error_type["message"],
                "component": error_type["component"],
                "error": error_type["error"],
                "thread": f"thread-{random.randint(1, 10)}",
                "requestId": f"req-{random.randint(1000, 9999)}",
                "cascade_id": f"cascade-{random.randint(100, 999)}"
            }
            entries.append(entry)
        
        return entries
    
    def generate_anomaly_pattern(self, base_time, entry_number):
        """Generate anomalous log entries (unusual patterns)."""
        anomaly_types = [
            {
                "message": "Unexpected service restart",
                "level": "error",
                "component": "system",
                "error": "abnormal termination"
            },
            {
                "message": "Data corruption detected",
                "level": "error", 
                "component": "storage",
                "error": "checksum mismatch"
            },
            {
                "message": "Security breach attempt",
                "level": "error",
                "component": "security", 
                "error": "unauthorized access"
            }
        ]
        
        anomaly = random.choice(anomaly_types)
        return {
            "timestamp": self.generate_timestamp(base_time, entry_number),
            "level": anomaly["level"],
            "message": anomaly["message"],
            "component": anomaly["component"],
            "error": anomaly["error"],
            "anomaly": True,
            "severity": "critical",
            "thread": f"thread-{random.randint(1, 10)}"
        }
    
    def generate_test_logs(self, num_entries=1000, output_file="test_logs.log", 
                          include_bursts=True, include_anomalies=True):
        """Generate comprehensive test log dataset."""
        print(f"Generating {num_entries} log entries...")
        
        base_time = datetime.now() - timedelta(hours=24)  # Start 24 hours ago
        entries = []
        entry_count = 0
        
        while entry_count < num_entries:
            # Regular log entry
            entry = self.generate_log_entry(base_time, entry_count)
            entries.append(entry)
            entry_count += 1
            
            # Occasionally generate error bursts
            if include_bursts and random.random() < 0.05:  # 5% chance
                error_type = random.choice(self.error_patterns)
                burst_entries = self.generate_burst_pattern(base_time, entry_count, error_type)
                entries.extend(burst_entries)
                entry_count += len(burst_entries)
            
            # Occasionally generate anomalies
            if include_anomalies and random.random() < 0.02:  # 2% chance
                anomaly_entry = self.generate_anomaly_pattern(base_time, entry_count)
                entries.append(anomaly_entry)
                entry_count += 1
        
        # Limit to requested number of entries
        entries = entries[:num_entries]
        
        # Write to file
        with open(output_file, 'w') as f:
            for entry in entries:
                # Remove None values
                clean_entry = {k: v for k, v in entry.items() if v is not None}
                f.write(json.dumps(clean_entry) + '\n')
        
        # Generate statistics
        error_count = sum(1 for e in entries if e.get("level") == "error")
        warn_count = sum(1 for e in entries if e.get("level") == "warn") 
        info_count = sum(1 for e in entries if e.get("level") == "info")
        anomaly_count = sum(1 for e in entries if e.get("anomaly", False))
        
        print(f"Generated {len(entries)} log entries:")
        print(f"  - Errors: {error_count} ({error_count/len(entries)*100:.1f}%)")
        print(f"  - Warnings: {warn_count} ({warn_count/len(entries)*100:.1f}%)")
        print(f"  - Info: {info_count} ({info_count/len(entries)*100:.1f}%)")
        print(f"  - Anomalies: {anomaly_count}")
        print(f"  - Output file: {output_file}")
        
        return entries
    
    def generate_component_specific_logs(self, component, num_entries=500, 
                                       output_file=None):
        """Generate logs for a specific component."""
        if output_file is None:
            output_file = f"{component}_logs.log"
        
        print(f"Generating {num_entries} entries for component: {component}")
        
        base_time = datetime.now() - timedelta(hours=12)
        entries = []
        
        # Component-specific error patterns
        component_patterns = {
            "kafka": [
                {"message": "Kafka producer timeout", "error": "timeout"},
                {"message": "Partition assignment failed", "error": "rebalance"},
                {"message": "Message serialization error", "error": "serialization"}
            ],
            "postgres": [
                {"message": "Database connection failed", "error": "connection refused"},
                {"message": "Query timeout", "error": "timeout"},
                {"message": "Deadlock detected", "error": "deadlock"}
            ],
            "rest": [
                {"message": "API request failed", "error": "bad request"},
                {"message": "Authentication failed", "error": "unauthorized"},
                {"message": "Rate limit exceeded", "error": "rate limit"}
            ]
        }
        
        patterns = component_patterns.get(component, self.error_patterns)
        
        for i in range(num_entries):
            if random.random() < 0.2:  # 20% errors for component-specific logs
                pattern = random.choice(patterns)
                entry = {
                    "timestamp": self.generate_timestamp(base_time, i),
                    "level": "error",
                    "message": pattern["message"],
                    "component": component,
                    "error": pattern["error"],
                    "thread": f"thread-{random.randint(1, 5)}",
                    "requestId": f"req-{random.randint(1000, 9999)}"
                }
            else:
                entry = {
                    "timestamp": self.generate_timestamp(base_time, i),
                    "level": random.choice(["info", "warn"]),
                    "message": random.choice(self.info_messages + self.warn_messages),
                    "component": component,
                    "thread": f"thread-{random.randint(1, 5)}",
                    "requestId": f"req-{random.randint(1000, 9999)}"
                }
            
            entries.append(entry)
        
        # Write to file
        with open(output_file, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        print(f"Generated component-specific logs: {output_file}")
        return entries


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Generate test log data")
    parser.add_argument("--entries", "-n", type=int, default=1000,
                       help="Number of log entries to generate")
    parser.add_argument("--output", "-o", type=str, default="test_logs.log",
                       help="Output file name")
    parser.add_argument("--component", "-c", type=str,
                       help="Generate logs for specific component")
    parser.add_argument("--no-bursts", action="store_true",
                       help="Disable error burst generation")
    parser.add_argument("--no-anomalies", action="store_true",
                       help="Disable anomaly generation")
    
    args = parser.parse_args()
    
    generator = TestDataGenerator()
    
    if args.component:
        generator.generate_component_specific_logs(
            component=args.component,
            num_entries=args.entries,
            output_file=args.output
        )
    else:
        generator.generate_test_logs(
            num_entries=args.entries,
            output_file=args.output,
            include_bursts=not args.no_bursts,
            include_anomalies=not args.no_anomalies
        )


if __name__ == "__main__":
    main()
