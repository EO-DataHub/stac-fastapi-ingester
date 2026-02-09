import os
import re
from collections.abc import Sequence
from typing import Any

from eodhp_utils.messagers import (
    CatalogueChangeBodyMessager,
    CatalogueChangeMessager,
    Messager,
)

from .handle_changes import create_or_update_entry, delete_entry, handle_access_policy


class IngesterMessager(CatalogueChangeBodyMessager):
    """
    This extends CatalogueChangeBodyMessager to handle update and delete messages for the ingester,
    making changes to datasets and entries in the Resource Catalogue via the handle_changes functions.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Initialise the API URL from environment variable
        self.api_url = os.getenv("FASTAPI_URL", "")

    def process_update_body(
        self, entry_body: dict | str, cat_path: str, source: str, target: str
    ) -> Sequence[CatalogueChangeMessager.Action]:

        assert isinstance(entry_body, dict)
        workspace = self.get_workspace_from_msg()

        # Handle updates to access policy
        if cat_path.endswith("meta_access_policy.json"):
            handle_access_policy(self.api_url, entry_body, workspace)
            return []

        # Remove .json suffix from cat_path
        cat_path = re.sub(".json$", "", cat_path)

        # Pass updates to the catalogue
        create_or_update_entry(self.api_url, entry_body, workspace, cat_path)
        return []

    def process_delete(
        self, input_bucket: str, input_key: str, cat_path: str, source: str, target: str
    ) -> Sequence[Messager.Action]:

        workspace = self.get_workspace_from_msg()

        # Handle updates to access policy
        if cat_path.endswith("meta_access_policy.json"):
            # Do nothing
            return []

        # Remove .json suffix from cat_path
        cat_path = re.sub(".json$", "", cat_path)

        delete_entry(self.api_url, workspace, cat_path)
        return []

    def get_workspace_from_msg(self) -> str:
        return self.input_change_msg.get("workspace", "")
