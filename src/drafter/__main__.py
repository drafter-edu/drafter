import sys
from drafter.command_line import parse_args, build_site

if __name__ == "__main__":
    options = parse_args(sys.argv[1:])
    build_site(options)