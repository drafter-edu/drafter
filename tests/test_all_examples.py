#!/usr/bin/env python3
"""
Script to test all examples and generate a report of which ones work.
This script tries to import and validate each example without actually running the server.
"""

import os
import sys
import json
import traceback
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
import importlib.util

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class ExampleTestResult:
    """Result of testing a single example."""
    name: str
    success: bool
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    
def test_example(example_path: Path) -> ExampleTestResult:
    """
    Test a single example by trying to import it.
    
    Args:
        example_path: Path to the example Python file
        
    Returns:
        ExampleTestResult with success status and any error information
    """
    example_name = example_path.stem
    
    try:
        # Create a module spec from the file
        spec = importlib.util.spec_from_file_location(example_name, example_path)
        if spec is None or spec.loader is None:
            return ExampleTestResult(
                name=example_name,
                success=False,
                error="Could not load module spec",
                error_type="ImportError"
            )
        
        # Load the module
        module = importlib.util.module_from_spec(spec)
        sys.modules[example_name] = module
        
        # Mock start_server to prevent actual server startup
        original_start_server = None
        if 'drafter.launch' in sys.modules:
            from drafter import launch
            original_start_server = launch.start_server
            launch.start_server = lambda *args, **kwargs: None
        
        # Execute the module
        spec.loader.exec_module(module)
        
        # Restore original start_server
        if original_start_server:
            from drafter import launch
            launch.start_server = original_start_server
        
        # Clean up
        if example_name in sys.modules:
            del sys.modules[example_name]
        
        return ExampleTestResult(
            name=example_name,
            success=True
        )
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Get the full traceback
        tb = traceback.format_exc()
        
        return ExampleTestResult(
            name=example_name,
            success=False,
            error=error_msg,
            error_type=error_type
        )


def get_all_examples(examples_dir: Path) -> List[Path]:
    """Get all Python example files."""
    return sorted(examples_dir.glob("*.py"))


def generate_markdown_report(results: List[ExampleTestResult]) -> str:
    """Generate a markdown report of test results."""
    working = [r for r in results if r.success]
    failing = [r for r in results if not r.success]
    
    md = "# Drafter Examples Test Report\n\n"
    md += "This report shows which examples can be loaded successfully.\n\n"
    md += "## Summary\n\n"
    md += f"- **Total Examples:** {len(results)}\n"
    md += f"- **Working:** {len(working)} ({len(working)/len(results)*100:.1f}%)\n"
    md += f"- **Failing:** {len(failing)} ({len(failing)/len(results)*100:.1f}%)\n\n"
    
    if failing:
        md += "## Failing Examples\n\n"
        md += "| Example | Error Type | Error Message |\n"
        md += "|---------|------------|---------------|\n"
        for r in failing:
            error_msg = (r.error or "Unknown error").replace("|", "\\|")
            # Truncate long error messages
            if len(error_msg) > 100:
                error_msg = error_msg[:97] + "..."
            md += f"| {r.name} | {r.error_type or 'Unknown'} | {error_msg} |\n"
        md += "\n"
    
    if working:
        md += "## Working Examples\n\n"
        for r in working:
            md += f"- ✓ {r.name}\n"
        md += "\n"
    
    return md


def main():
    """Main function to test all examples and generate reports."""
    # Find examples directory
    examples_dir = Path(__file__).parent.parent / "examples"
    
    if not examples_dir.exists():
        print(f"Error: Examples directory not found at {examples_dir}")
        sys.exit(1)
    
    print(f"Testing examples in {examples_dir}\n")
    
    # Get all examples
    examples = get_all_examples(examples_dir)
    print(f"Found {len(examples)} examples\n")
    
    # Test each example
    results = []
    for example_path in examples:
        print(f"Testing {example_path.stem}...", end=" ")
        result = test_example(example_path)
        results.append(result)
        
        if result.success:
            print("✓")
        else:
            print(f"✗ ({result.error_type})")
            if result.error:
                # Print first line of error
                first_line = result.error.split('\n')[0]
                print(f"  {first_line[:80]}")
    
    # Print summary
    working = [r for r in results if r.success]
    failing = [r for r in results if not r.success]
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total Examples: {len(results)}")
    print(f"Working: {len(working)} ({len(working)/len(results)*100:.1f}%)")
    print(f"Failing: {len(failing)} ({len(failing)/len(results)*100:.1f}%)")
    
    # Create test-results directory
    results_dir = Path(__file__).parent / "test-results"
    results_dir.mkdir(exist_ok=True)
    
    # Write JSON report
    json_path = results_dir / "python-examples-test-report.json"
    with open(json_path, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    print(f"\nJSON report written to: {json_path}")
    
    # Write markdown report
    md_report = generate_markdown_report(results)
    md_path = results_dir / "python-examples-test-report.md"
    with open(md_path, 'w') as f:
        f.write(md_report)
    print(f"Markdown report written to: {md_path}")
    
    # Print failing examples details
    if failing:
        print(f"\n{'='*60}")
        print("FAILING EXAMPLES DETAILS")
        print(f"{'='*60}")
        for r in failing:
            print(f"\n{r.name}:")
            print(f"  Type: {r.error_type}")
            print(f"  Error: {r.error}")


if __name__ == "__main__":
    main()
