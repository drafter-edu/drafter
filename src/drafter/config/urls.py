"""Internal URL routing constants for Drafter.

Defines reserved URL paths for WebSocket communication and asset serving.
"""

INTERNAL_ROUTES = {
    "WS": "__drafter_ws",
    "ASSETS": "__drafter_assets",
    "LIST_FILES": "__drafter_list_files",
}
"""Reserved URL paths served by Drafter itself: the live-reload WebSocket
("WS"), static assets ("ASSETS"), and the file listing endpoint
("LIST_FILES")."""

INTERNAL_FILES = {"DRAFTER_PYODIDE_FILE": "drafter-pyodide.zip"}
"""Reserved filenames used internally, such as the zipped Drafter package
loaded into Pyodide."""


def determine_assets_url(override_asset_url) -> str:
    """Determine the asset URL based on override setting.

    Args:
        override_asset_url: User override URL (False to use default internal route).

    Returns:
        The asset URL path to use.
    """
    return (
        INTERNAL_ROUTES["ASSETS"] if not override_asset_url else str(override_asset_url)
    )
