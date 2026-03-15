"""Drafter CLI entry point.

Unified command-line interface for running Drafter in either:
- App server mode (default): Starts local development server
- Compile mode (--compile): Builds static site

Usage:
    drafter [main_file.py] [options]
    drafter [main_file.py] --compile [options]
"""
from drafter.configuration import get_system_configuration
from runpy import run_path

def main():
    """Main CLI entry point that routes to app server or builder based on arguments."""
    system = get_system_configuration()
    student_file_path = system.app_common.get_full_main_file_path()
    
    if student_file_path is None:
        print("Error: Could not determine the path to the main user file.")
        return
    
    run_path(student_file_path, run_name="__main__")


if __name__ == "__main__":
    main()