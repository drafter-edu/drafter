import sys
from drafter.builder.build import compile_site


def main():
    compile_site(config=None, client_server_config=None, argv=sys.argv[1:])