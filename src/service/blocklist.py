#!/usr/bin/env python
# -*- encoding=utf8 -*-

from src.config import Config
from src.api import ListBlockListResponse, BlockListType, ResponseStatus, BlockListResponse
from src.db import MongoDB


class BlockListService(object):
    """class to encapsulate the blocklist service."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = MongoDB().db

    def list_blocklist(self, user_id: str, list_type: BlockListType) -> ListBlockListResponse:
        """List all blocklist."""
        collection = self.db.get_collection("blocklist")
        query = {"user_id": user_id, "list_type": list_type}
        blocklist_cursor = collection.find(query)
        blocklist = [
            BlockListResponse(id=str(doc["_id"]), domain=doc["domain"])
            for doc in blocklist_cursor
        ]

        return ListBlockListResponse(blocklist=blocklist, status=ResponseStatus.SUCCESS)
