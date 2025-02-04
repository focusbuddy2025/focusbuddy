#!/usr/bin/env python
# -*- encoding=utf8 -*-

import re

from bson import ObjectId

from src.api import BlockListType, BlockListResponse
from src.config import Config
from src.db import MongoDB

URL_REGEX = re.compile(
    r"^(https?:\/\/)?"  # Optional http or https
    r"(([A-Za-z0-9-]+\.)+[A-Za-z]{2,6})"  # Domain (e.g., example.com)
    r"(:\d{1,5})?"  # Optional port (e.g., :8080)
    r"(\/[^\s]*)?$"  # Optional path (e.g., /path/to/page)
)


class BlockListService(object):
    """class to encapsulate the blocklist service."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = MongoDB().db

    def list_blocklist(self, user_id: str) -> list[BlockListResponse]:
        """List all blocklist."""
        collection = self.db.get_collection("blocklist")
        query = {"user_id": user_id}
        blocklist_cursor = collection.find(query)
        blocklist = [
            BlockListResponse(id=str(doc["_id"]), domain=doc["domain"])
            for doc in blocklist_cursor
        ]

        return blocklist

    def add_blocklist(self, user_id: str, domain: str, list_type: BlockListType) -> (str, bool):
        """Add an url to blocklist."""
        collection = self.db.get_collection("blocklist")

        query = {
            "user_id": user_id,
            "domain": domain,
            "list_type": list_type
        }
        update = {"$setOnInsert": query}
        result = collection.update_one(query, update, upsert=True)

        # if it already exists, update nothing and return failed
        if result.matched_count > 0:
            return "", False

        return str(result.upserted_id), True

    def delete_blocklist(self, user_id: str, blocklist_id: str) -> bool:
        """Delete an url from blocklist."""
        collection = self.db.get_collection("blocklist")

        result = collection.delete_one({"_id": ObjectId(blocklist_id), "user_id": user_id})

        return result.deleted_count > 0
