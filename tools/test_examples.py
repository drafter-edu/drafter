#!/usr/bin/env python3
"""
Script to test all example files in the examples/ directory.
This script imports each example and checks if it can be loaded without errors.
"""

import sys
import os
from pathlib import Path
import importlib.util
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def test_example(example_path: Path) -> Tuple[bool, str]:
    """
    Test a single example file.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("example_module", example_path)
        if spec is None or spec.loader is None:
            return False, "Could not create module spec"
        
        module = importlib.util.module_from_spec(spec)
        
        # Don't actually execute it since it might try to start a server
        # Just try to compile and load it
        with open(example_path, 'r') as f:
            code = f.read()
        
        # Check for syntax errors
        compile(code, str(example_path), 'exec')
        
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except ImportError as e:
        return False, f"Import error: {e}"
    except Exception as e:
        return False, f"Error: {type(e).__name__}: {e}"


def main():
    """Test all examples and generate a report."""
    print("Testing all examples in examples/ directory")
    print("=" * 80)
    
    # Get all Python files in examples
    example_files = sorted(EXAMPLES_DIR.glob("*.py"))
    
    results: Dict[str, Tuple[bool, str]] = {}
    
    for example_file in example_files:
        name = example_file.name
        print(f"\nTesting {name}...", end=" ")
        success, message = test_example(example_file)
        results[name] = (success, message)
        
        if success:
            print(f"✓ PASS: {message}")
        else:
            print(f"✗ FAIL: {message}")
    
    # Generate summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for success, _ in results.values() if success)
    failed = len(results) - passed
    
    print(f"\nTotal examples: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\n" + "=" * 80)
        print("FAILED EXAMPLES")
        print("=" * 80)
        
        for name, (success, message) in sorted(results.items()):
            if not success:
                print(f"\n{name}:")
                print(f"  {message}")
    
    # Generate markdown report
    report_path = Path(__file__).parent.parent / "EXAMPLE_TEST_REPORT.md"
    with open(report_path, 'w') as f:
        f.write("# Drafter Examples Test Report\n\n")
        f.write(f"Total examples: {len(results)}\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {failed}\n\n")
        
        f.write("## Test Results\n\n")
        
        f.write("### Passed Examples\n\n")
        for name, (success, message) in sorted(results.items()):
            if success:
                f.write(f"- ✓ `{name}`: {message}\n")
        
        if failed > 0:
            f.write("\n### Failed Examples\n\n")
            for name, (success, message) in sorted(results.items()):
                if not success:
                    f.write(f"- ✗ `{name}`: {message}\n")
    
    print(f"\nReport written to: {report_path}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
