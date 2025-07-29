#!/usr/bin/env python3
"""
Test runner for ols_fetch_from_github module

Usage:
    python tests/run_tests.py                    # Run all tests
    python tests/run_tests.py test_config        # Run specific test module
    python tests/run_tests.py -v                 # Verbose output

Note: This script should be run from the project root directory.
"""

import unittest
import sys
import os

# Add the project root to Python path so imports work correctly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def main():
    """Main test runner function"""
    
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        return
    
    # Determine verbosity
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    verbosity = 2 if verbose else 1
    
    # Determine which tests to run
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        # Run specific test module
        test_module = sys.argv[1]
        if not test_module.startswith('test_'):
            test_module = 'test_' + test_module
        
        try:
            suite = unittest.TestLoader().loadTestsFromName(test_module)
        except ImportError as e:
            print(f"Error: Could not import test module '{test_module}': {e}")
            return 1
    else:
        # Run all tests
        test_dir = os.path.dirname(__file__)
        suite = unittest.TestLoader().discover(test_dir, pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All tests passed! ({result.testsRun} tests)")
        return 0
    else:
        failures = len(result.failures)
        errors = len(result.errors)
        print(f"\n❌ Tests failed: {failures} failures, {errors} errors out of {result.testsRun} tests")
        return 1


if __name__ == '__main__':
    sys.exit(main())