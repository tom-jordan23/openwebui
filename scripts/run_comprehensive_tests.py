#!/usr/bin/env python3
"""
Comprehensive Test Runner
Command-line interface for the comprehensive testing framework
"""

import os
import sys
import asyncio
import argparse
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from testing.comprehensive_testing import (
    ComprehensiveTestFramework, 
    TestType, 
    register_example_tests
)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def parse_test_types(test_types_str: str) -> List[TestType]:
    """Parse test types from command line argument"""
    if not test_types_str:
        return list(TestType)
    
    type_map = {t.value: t for t in TestType}
    requested_types = [t.strip() for t in test_types_str.split(',')]
    
    valid_types = []
    for type_str in requested_types:
        if type_str in type_map:
            valid_types.append(type_map[type_str])
        else:
            print(f"Warning: Unknown test type '{type_str}'. Available types: {list(type_map.keys())}")
    
    return valid_types if valid_types else list(TestType)

def save_test_report(report: Dict[str, Any], output_dir: str):
    """Save test report in multiple formats"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON report
    json_path = Path(output_dir) / f"test_report_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"JSON report saved: {json_path}")
    
    # Save HTML report
    html_path = Path(output_dir) / f"test_report_{timestamp}.html"
    html_content = generate_html_report(report)
    with open(html_path, 'w') as f:
        f.write(html_content)
    print(f"HTML report saved: {html_path}")
    
    # Save JUnit XML report
    junit_path = Path(output_dir) / f"test_report_{timestamp}.xml"
    junit_content = generate_junit_xml(report)
    with open(junit_path, 'w') as f:
        f.write(junit_content)
    print(f"JUnit XML report saved: {junit_path}")

def generate_html_report(report: Dict[str, Any]) -> str:
    """Generate HTML test report"""
    summary = report.get('test_execution_summary', {})
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OpenWebUI Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        .error {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .status-passed {{ background-color: #d4edda; }}
        .status-failed {{ background-color: #f8d7da; }}
        .status-error {{ background-color: #fff3cd; }}
    </style>
</head>
<body>
    <h1>OpenWebUI Comprehensive Test Report</h1>
    
    <div class="summary">
        <h2>Test Execution Summary</h2>
        <p><strong>Execution Time:</strong> {summary.get('start_time', 'N/A')} - {summary.get('end_time', 'N/A')}</p>
        <p><strong>Total Duration:</strong> {summary.get('total_duration_seconds', 0):.2f} seconds</p>
        <p><strong>Total Tests:</strong> {summary.get('total_tests', 0)}</p>
        <p><strong>Passed:</strong> <span class="success">{summary.get('passed', 0)}</span></p>
        <p><strong>Failed:</strong> <span class="failure">{summary.get('failed', 0)}</span></p>
        <p><strong>Errors:</strong> <span class="error">{summary.get('errors', 0)}</span></p>
        <p><strong>Success Rate:</strong> {summary.get('success_rate', 0):.1f}%</p>
    </div>
    
    <h2>Results by Test Type</h2>
    <table>
        <tr>
            <th>Test Type</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Errors</th>
            <th>Total</th>
        </tr>
"""
    
    for test_type, results in report.get('results_by_type', {}).items():
        total = results.get('passed', 0) + results.get('failed', 0) + results.get('error', 0)
        html += f"""
        <tr>
            <td>{test_type}</td>
            <td class="success">{results.get('passed', 0)}</td>
            <td class="failure">{results.get('failed', 0)}</td>
            <td class="error">{results.get('error', 0)}</td>
            <td>{total}</td>
        </tr>
        """
    
    html += """
    </table>
    
    <h2>Failed Tests</h2>
    <table>
        <tr>
            <th>Test ID</th>
            <th>Test Type</th>
            <th>Duration (s)</th>
            <th>Error Message</th>
        </tr>
    """
    
    for failed_test in report.get('failed_tests', []):
        html += f"""
        <tr class="status-failed">
            <td>{failed_test.get('test_id', 'N/A')}</td>
            <td>{failed_test.get('test_type', 'N/A')}</td>
            <td>{failed_test.get('duration', 0):.2f}</td>
            <td>{failed_test.get('error_message', 'N/A')}</td>
        </tr>
        """
    
    html += """
    </table>
    
    <h2>Slowest Tests</h2>
    <table>
        <tr>
            <th>Test ID</th>
            <th>Test Type</th>
            <th>Duration (s)</th>
        </tr>
    """
    
    for slow_test in report.get('slowest_tests', [])[:10]:
        html += f"""
        <tr>
            <td>{slow_test.get('test_id', 'N/A')}</td>
            <td>{slow_test.get('test_type', 'N/A')}</td>
            <td>{slow_test.get('duration_seconds', 0):.2f}</td>
        </tr>
        """
    
    html += """
    </table>
</body>
</html>
    """
    
    return html

def generate_junit_xml(report: Dict[str, Any]) -> str:
    """Generate JUnit XML test report"""
    summary = report.get('test_execution_summary', {})
    
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite 
    name="OpenWebUI Comprehensive Tests"
    tests="{summary.get('total_tests', 0)}"
    failures="{summary.get('failed', 0)}"
    errors="{summary.get('errors', 0)}"
    time="{summary.get('total_duration_seconds', 0):.2f}"
    timestamp="{summary.get('start_time', '')}"
>
"""
    
    for test_result in report.get('detailed_results', []):
        test_name = test_result.get('test_id', 'unknown')
        test_class = test_result.get('test_type', 'unknown')
        duration = test_result.get('duration_seconds', 0)
        status = test_result.get('status', 'unknown')
        
        xml += f'    <testcase name="{test_name}" classname="{test_class}" time="{duration:.2f}"'
        
        if status == 'failed':
            error_msg = test_result.get('error_message', 'Test failed')
            xml += f'>\n        <failure message="{error_msg}"></failure>\n    </testcase>\n'
        elif status == 'error':
            error_msg = test_result.get('error_message', 'Test error')
            xml += f'>\n        <error message="{error_msg}"></error>\n    </testcase>\n'
        else:
            xml += ' />\n'
    
    xml += '</testsuite>\n'
    return xml

def print_summary(report: Dict[str, Any]):
    """Print test summary to console"""
    summary = report.get('test_execution_summary', {})
    
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST EXECUTION SUMMARY")
    print("="*60)
    
    print(f"Start Time: {summary.get('start_time', 'N/A')}")
    print(f"End Time: {summary.get('end_time', 'N/A')}")
    print(f"Duration: {summary.get('total_duration_seconds', 0):.2f} seconds")
    print(f"Total Tests: {summary.get('total_tests', 0)}")
    print(f"Passed: {summary.get('passed', 0)}")
    print(f"Failed: {summary.get('failed', 0)}")
    print(f"Errors: {summary.get('errors', 0)}")
    print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
    
    if summary.get('failed', 0) > 0 or summary.get('errors', 0) > 0:
        print("\n" + "-"*40)
        print("FAILED TESTS:")
        print("-"*40)
        for failed_test in report.get('failed_tests', []):
            print(f"❌ {failed_test.get('test_id', 'N/A')} ({failed_test.get('test_type', 'N/A')})")
            if failed_test.get('error_message'):
                print(f"   Error: {failed_test.get('error_message')}")
    
    performance_regressions = report.get('performance_regressions', 0)
    if performance_regressions > 0:
        print(f"\n⚠️  Performance Regressions Detected: {performance_regressions}")
    
    print("\n" + "="*60)

async def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="OpenWebUI Comprehensive Test Runner")
    
    parser.add_argument(
        '--config', 
        default='config/testing/framework_config.yaml',
        help='Path to test configuration file'
    )
    
    parser.add_argument(
        '--types',
        help='Comma-separated list of test types to run (unit,integration,e2e,performance,load,chaos,security,ai_validation)'
    )
    
    parser.add_argument(
        '--tags',
        help='Comma-separated list of tags to filter tests'
    )
    
    parser.add_argument(
        '--output-dir',
        default='test_reports',
        help='Directory to save test reports'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show which tests would be run without executing them'
    )
    
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first test failure'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    import logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        print("Failed to load configuration. Using defaults.")
        config = {}
    
    print("OpenWebUI Comprehensive Test Framework")
    print("="*50)
    
    # Parse test types and tags
    test_types = parse_test_types(args.types)
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else None
    
    print(f"Test Types: {[t.value for t in test_types]}")
    print(f"Tags Filter: {tags}")
    print(f"Configuration: {args.config}")
    print(f"Output Directory: {args.output_dir}")
    
    # Initialize test framework
    framework = ComprehensiveTestFramework(config)
    
    # Register example tests
    register_example_tests(framework)
    
    if args.dry_run:
        # Show tests that would be run
        tests_to_run = framework._filter_tests(test_types, tags)
        print(f"\nTests that would be executed ({len(tests_to_run)}):")
        for test in tests_to_run:
            print(f"  - {test.test_id} ({test.test_type.value}) [{test.priority}]")
        return
    
    try:
        # Run the test suite
        print(f"\nStarting test execution...")
        report = await framework.run_test_suite(test_types, tags)
        
        # Print summary
        print_summary(report)
        
        # Save reports
        save_test_report(report, args.output_dir)
        
        # Exit with appropriate code
        summary = report.get('test_execution_summary', {})
        failed_tests = summary.get('failed', 0)
        error_tests = summary.get('errors', 0)
        
        if failed_tests > 0 or error_tests > 0:
            print("\n❌ Tests failed. See report for details.")
            sys.exit(1)
        else:
            print("\n✅ All tests passed!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())