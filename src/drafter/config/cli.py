import argparse


def parse_command_line_args(argv):
    parser = argparse.ArgumentParser(description="Launch the Drafter App Server.")

    parser.add_argument(
        "main_filename", help="The main Python file to run in the App Server."
    )

    parser.add_argument("--engine", type=str, choices=["skulpt", "pyodide"])
    parser.add_argument(
        "--mount_drafter_locally",
        action="store_true",
        help="Mount the Drafter package directory locally in the web environment.",
    )

    return parser.parse_args(argv)
