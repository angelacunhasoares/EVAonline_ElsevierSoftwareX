#!/usr/bin/env python3
"""
Test runner script for EVAonline backend tests.

This script provides convenient commands to run different types of tests
with various options and configurations.

Usage:
    python run_tests.py [command] [options]

Commands:
    all         - Run all tests
    unit        - Run only unit tests
    integration - Run only integration tests
    coverage    - Run tests with coverage report
    quick       - Run tests in parallel (fast)
    api         - Run only API-related tests
    slow        - Run only slow tests

Options:
    --verbose, -v   - Verbose output
    --fail-fast     - Stop on first failure
    --html-report   - Generate HTML coverage report

Examples:
    python run_tests.py all
    python run_tests.py coverage --html-report
    python run_tests.py unit --verbose
    python run_tests.py quick
"""

import subprocess
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, cwd=backend_path, check=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ pytest not found. Please install with: pip install pytest pytest-cov")
        return False

def main():
    """Main function to handle test commands."""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    fail_fast = "--fail-fast" in sys.argv
    html_report = "--html-report" in sys.argv

    base_cmd = ["python", "-m", "pytest", "tests/"]

    if verbose:
        base_cmd.append("-v")

    if fail_fast:
        base_cmd.append("--tb=short")
    else:
        base_cmd.append("--tb=short")

    # Command-specific configurations
    if command == "all":
        cmd = base_cmd + ["--durations=10"]
        description = "Running all tests"

    elif command == "unit":
        cmd = base_cmd + ["-m", "unit"]
        description = "Running unit tests"

    elif command == "integration":
        cmd = base_cmd + ["-m", "integration"]
        description = "Running integration tests"

    elif command == "coverage":
        cmd = base_cmd + [
            "--cov=backend",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ]
        if html_report:
            cmd.extend(["--cov-report=html"])
        description = "Running tests with coverage"

    elif command == "quick":
        try:
            import pytest_xdist
            cmd = base_cmd + ["-n", "auto", "--durations=5"]
            description = "Running tests in parallel (quick mode)"
        except ImportError:
            print("❌ pytest-xdist not installed. Install with: pip install pytest-xdist")
            cmd = base_cmd + ["--durations=5"]
            description = "Running tests (quick mode)"

    elif command == "api":
        cmd = base_cmd + ["-m", "api"]
        description = "Running API tests"

    elif command == "slow":
        cmd = base_cmd + ["-m", "slow", "--durations=0"]
        description = "Running slow tests"

    elif command == "smoke":
        # Quick smoke test - just run a few critical tests
        cmd = base_cmd + [
            "tests/test_openmeteo.py::TestOpenMeteoForecastAPI::TestInitialization",
            "--tb=line"
        ]
        description = "Running smoke tests (critical functionality only)"

    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        return

    # Run the command
    success = run_command(cmd, description)

    if success:
        print(f"\n🎉 All {command} tests passed!")
        if command == "coverage" and html_report:
            html_path = backend_path / "htmlcov" / "index.html"
            if html_path.exists():
                print(f"📊 HTML coverage report: file://{html_path}")
    else:
        print(f"\n💥 {command} tests failed!")
        sys.exit(1)

    # Additional reporting for coverage
    if command == "coverage":
        print(f"\n📈 Coverage report generated in: {backend_path}/htmlcov/")
        print(f"   Open htmlcov/index.html in your browser for detailed report")

if __name__ == "__main__":
    main()
