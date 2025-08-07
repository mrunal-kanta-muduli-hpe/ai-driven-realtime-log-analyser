#!/usr/bin/env python3
"""
Quick demonstration of Smart Log Analyzer functionality
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.log_parser import LogParser
from src.core.pattern_detector import PatternDetector
from src.core.component_filter import ComponentFilter
from src.integrations.defect_generator import DefectGenerator
from src.utils.config import Config

def main():
    print("🚀 SMART LOG ANALYZER - QUICK DEMONSTRATION")
    print("=" * 60)
    
    # Initialize components
    config = Config()
    log_parser = LogParser(config)
    pattern_detector = PatternDetector(config)
    component_filter = ComponentFilter(config)
    defect_generator = DefectGenerator(config)
    
    # Parse sample logs
    log_file = "sample_logs.log"
    print(f"📁 Analyzing {log_file}...")
    
    try:
        entries = log_parser.parse_file(log_file, "json")
        print(f"✅ Successfully parsed {len(entries)} log entries")
        
        # Show statistics
        stats = log_parser.get_statistics(entries)
        print(f"\n📊 LOG STATISTICS:")
        print(f"   Total entries: {stats['total']}")
        print(f"   Errors: {stats['errors']} ({stats['error_rate']:.1f}%)")
        print(f"   Warnings: {stats['warnings']}")
        print(f"   Info: {stats['info']}")
        
        # Show component breakdown
        component_stats = component_filter.get_component_statistics(entries)
        print(f"\n🔧 COMPONENT BREAKDOWN:")
        for component, stat in list(component_stats.items())[:5]:
            print(f"   {component}: {stat['total_entries']} entries ({stat['error_count']} errors)")
        
        # Detect patterns
        print(f"\n🔍 DETECTING PATTERNS...")
        patterns = pattern_detector.detect_patterns(entries)
        print(f"✅ Detected {len(patterns)} patterns")
        
        if patterns:
            print(f"\n📈 TOP PATTERNS:")
            for i, pattern in enumerate(patterns[:3], 1):
                print(f"   {i}. {pattern.get('type', 'Unknown')}: {pattern.get('error_message', 'N/A')}")
                print(f"      Frequency: {pattern.get('frequency', 0)}, Severity: {pattern.get('severity', 'unknown')}")
        
        # Generate defects
        if patterns:
            print(f"\n🎯 GENERATING DEFECT REPORTS...")
            defects = defect_generator.generate_defects(patterns, entries)
            print(f"✅ Generated {len(defects)} defect reports")
            
            if defects:
                print(f"\n📋 SAMPLE DEFECT REPORT:")
                sample_defect = defects[0]
                print(f"   Summary: {sample_defect.get('summary', 'N/A')}")
                print(f"   Priority: {sample_defect.get('priority', 'N/A')}")
                print(f"   Component: {sample_defect.get('component', 'N/A')}")
                print(f"   Description: {sample_defect.get('description', 'N/A')[:100]}...")
        
        # Component-specific analysis
        postgres_entries = component_filter.filter_by_component(entries, "postgres")
        if postgres_entries:
            print(f"\n🐘 POSTGRES-SPECIFIC ANALYSIS:")
            postgres_patterns = pattern_detector.detect_patterns(postgres_entries)
            print(f"   Found {len(postgres_entries)} postgres entries")
            print(f"   Detected {len(postgres_patterns)} postgres-specific patterns")
        
        # Save results
        output_file = "quick_demo_results.json"
        results = {
            "statistics": stats,
            "component_stats": component_stats,
            "patterns": patterns,
            "defects": defects if patterns else []
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")
        print(f"\n🎉 DEMONSTRATION COMPLETE!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
