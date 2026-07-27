"""Drafter CLI entry point.

Unified command-line interface for running Drafter in either:
- App server mode (default): Starts local development server
- Compile mode (--compile): Builds static site

Usage:
    drafter [main_file.py] [options]
    drafter [main_file.py] --compile [options]

Because we set up our pyproject.toml file to point to this module's `main`,
when you run `drafter` from the command line, it will execute the `main` function
here, with a `sys.argv` like `['drafter', 'my_site.py', '--some-flag']`.
"""

from runpy import run_path

from drafter.configuration import get_system_configuration


def main():
    """Main CLI entry point: loads the system configuration and executes the user's main file as `__main__` via `runpy.run_path`."""
    system = get_system_configuration(True)

    if system.bootstrap.path is None:
        # TODO: Raise an error instead, more elegantly
        print("Error: Could not determine the path to the main user file.")
        return

    run_path(system.bootstrap.path, run_name="__main__")


if __name__ == "__main__":
    main()
