INTERNAL_ROUTES = {
    "WS": "/__drafter_ws",
    "ASSETS": "/__drafter_assets",
}


def determine_assets_url(override_asset_url) -> str:
    return (
        INTERNAL_ROUTES["ASSETS"] if not override_asset_url else str(override_asset_url)
    )
