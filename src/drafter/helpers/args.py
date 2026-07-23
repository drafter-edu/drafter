"""Guarded access to argparse for runtimes that may not provide it."""

from typing import Optional

try:
    import argparse

    HAVE_ARGPARSE = True
except Exception:
    HAVE_ARGPARSE = False


def get_argparser() -> "Optional[type[argparse.ArgumentParser]]":
    """Return the ArgumentParser class if argparse is available.

    Returns:
        The argparse.ArgumentParser class, or None when argparse could not
        be imported in the current runtime.
    """
    if not HAVE_ARGPARSE:
        return None
    return argparse.ArgumentParser  # type: ignore
