import sys
import logging
from typing import Any
logger = logging.getLogger('drafter')


# try:
#     from bottle import Bottle, abort, request, static_file

#     DEFAULT_BACKEND = "bottle"
# except ImportError:
#     DEFAULT_BACKEND = "none"
#     logger.warn("Bottle unavailable; backend will be disabled and run in test-only mode.")
DEFAULT_BACKEND = 'http.server'

def _hijack_bottle() -> None:
    """
    Hijacks the Bottle backend to allow for custom stderr messages.
    This allows us to suppress some of the Bottle messages and replace them with our own.

    Called automatically when the module is imported, as a first step to ensure that the Bottle backend is available.
    Fails silently if Bottle is not available.
    """
    def _stderr(*args: Any) -> None:
        try:
            if args:
                first_arg = str(args[0])
                if first_arg.startswith("Bottle v") and "server starting up" in first_arg:
                    mutable_args = list(args)
                    mutable_args[0] = "Drafter server starting up (using Bottle backend)."
            print(*mutable_args, file=sys.stderr)
        except (IOError, AttributeError):
            pass

    # try:
    #     import bottle
    #     bottle._stderr = _stderr
    # except ImportError:
    #     pass


_hijack_bottle()
