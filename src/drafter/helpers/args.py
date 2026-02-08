from typing import Optional
try:
    import argparse
    HAVE_ARGPARSE = True
except Exception as e:
    HAVE_ARGPARSE = False
    
    
def get_argparser() -> "Optional[type[argparse.ArgumentParser]]":
    if not HAVE_ARGPARSE:
        return None
    return argparse.ArgumentParser # type: ignore