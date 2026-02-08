"""Internal URL routing constants for Drafter.

Defines reserved URL paths for WebSocket communication and asset serving.
"""

INTERNAL_ROUTES = {
    "WS": "__drafter_ws",
    "ASSETS": "__drafter_assets",
}


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
