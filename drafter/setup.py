import sys
import logging
logger = logging.getLogger('drafter')


try:
    from bottle import Bottle, abort, request, static_file

    DEFAULT_BACKEND = "bottle"
except ImportError:
    DEFAULT_BACKEND = "none"
    logger.warn("Bottle unavailable; backend will be disabled and run in test-only mode.")


def _hijack_bottle():
    def _stderr(*args):
        try:
            if args:
                first_arg = str(args[0])
                if first_arg.startswith("Bottle v") and "server starting up" in first_arg:
                    args = list(args)
                    args[0] = "Drafter server starting up (using Bottle backend)."
            print(*args, file=sys.stderr)
        except (IOError, AttributeError):
            pass

    try:
        import bottle
        bottle._stderr = _stderr
    except ImportError:
        pass


_hijack_bottle()
