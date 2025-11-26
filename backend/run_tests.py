#!/usr/bin/env python3
"""
Test runner script for NodeAI backend
Provides structured test execution with different test suites and reporting
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle output."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
    else:
        print(f"❌ {description} - FAILED (exit code: {result.returncode})")
    
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="NodeAI Test Runner")
    parser.add_argument("--suite", choices=["unit", "integration", "all", "fast", "slow"], 
                       default="fast", help="Test suite to run")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Number of parallel workers")
    parser.add_argument("--file", "-f", help="Run specific test file")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    
    args = parser.parse_args()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Base pytest command - use sys.executable to ensure we use the same Python interpreter
    pytest_cmd = [sys.executable, "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        pytest_cmd.append("-v")
    else:
        pytest_cmd.append("-q")
    
    # Add parallel execution
    if args.parallel:
        pytest_cmd.extend(["-n", str(args.parallel)])
    
    # Add coverage if requested
    if args.coverage:
        pytest_cmd.extend([
            "--cov=backend",
            "--cov-branch", 
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml"
        ])
    
    # Add pattern matching
    if args.pattern:
        pytest_cmd.extend(["-k", args.pattern])
    
    # Configure test suite
    if args.file:
        pytest_cmd.append(args.file)
    elif args.suite == "unit":
        pytest_cmd.extend(["-m", "unit", "tests/unit/"])
    elif args.suite == "integration":
        pytest_cmd.extend(["-m", "integration", "tests/integration/"])
    elif args.suite == "fast":
        pytest_cmd.extend(["-m", "not slow", "tests/"])
    elif args.suite == "slow":
        pytest_cmd.extend(["-m", "slow", "tests/"])
    elif args.suite == "all":
        pytest_cmd.append("tests/")
    
    # Run the tests
    exit_code = run_command(pytest_cmd, f"Running {args.suite} tests")
    
    # Generate coverage summary if coverage was requested
    if args.coverage and exit_code == 0:
        print(f"\n📊 Coverage report generated in htmlcov/index.html")
        
        # Try to show coverage summary
        try:
            coverage_cmd = [sys.executable, "-m", "coverage", "report", "--show-missing"]
            run_command(coverage_cmd, "Coverage Summary")
        except:
            pass
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()