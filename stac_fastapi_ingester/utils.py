from typing import Optional


def construct_catalog_url(
    api_url: str, catalog_path: Optional[str] = None, catalog_id: Optional[str] = None
) -> str:
    if catalog_path and catalog_id:
        combined_url = f"{api_url}/{catalog_path}/{catalog_id}"
    elif catalog_path:
        combined_url = f"{api_url}/{catalog_path}"
    elif catalog_id:
        combined_url = f"{api_url}/{catalog_id}"
    else:
        raise ValueError("Either catalog_path or catalog_id must be provided")
    return combined_url
