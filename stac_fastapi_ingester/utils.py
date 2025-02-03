from typing import Optional


def construct_catalog_url(
    api_url: str, catalog_path: Optional[str] = None, catalog_id: Optional[str] = None
) -> str:
    if catalog_path and catalog_id:
        combined_url = f"{api_url}/catalogs/{catalog_path}/catalogs/{catalog_id}"
    elif catalog_path:
        combined_url = f"{api_url}/catalogs/{catalog_path}/catalogs"
    elif catalog_id:
        combined_url = f"{api_url}/catalogs/{catalog_id}"
    return combined_url
