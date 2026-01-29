"""
System routes for the Drafter framework.
"""

from drafter.router.defaults.about import default_about
from drafter.router.defaults.index import default_index
from drafter.router.defaults.reset import default_reset
from drafter.router.defaults.reload import default_reload
from drafter.router.defaults.error import default_error

_SYSTEM_ERROR_ROUTE = "--error"
_SYSTEM_ABOUT_ROUTE = "--about"
_SYSTEM_RESET_ROUTE = "--reset"
_SYSTEM_RELOAD_ROUTE = "--reload"
_SYSTEM_INDEX_ROUTE = "index"

_SYSTEM_ROUTES = {
    _SYSTEM_ERROR_ROUTE: default_error,
    _SYSTEM_ABOUT_ROUTE: default_about,
    _SYSTEM_RESET_ROUTE: default_reset,
    _SYSTEM_RELOAD_ROUTE: default_reload,
    _SYSTEM_INDEX_ROUTE: default_index,
}
