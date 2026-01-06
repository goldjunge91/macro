#!/usr/bin/env python
"""
Test runner script for the macro application.
Provides a simple interface to run tests with common options.
"""
import sys
import subprocess

def main():
    """Run the test suite"""
    print("=" * 60)
    print("Running Macro Test Suite")
    print("=" * 60)
    print()
    
    # Run pytest with common options
    args = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    # Add any command-line arguments passed to this script
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    
    result = subprocess.run(args)
    
    print()
    print("=" * 60)
    if result.returncode == 0:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
