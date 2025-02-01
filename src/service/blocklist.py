#!/usr/bin/env python
# -*- encoding=utf8 -*-

from src.config import Config
from src.api import ListBlockListResponse, BlockListType, ResponseStatus, BlockListResponse, EditBlockListResponse
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

    def add_blocklist(self, user_id: str, website_url: str, list_type: BlockListType) -> EditBlockListResponse:
        """Add an url to blocklist."""
        collection = self.db.get_collection("blocklist")
        new_entry = {
            "user_id": user_id,
            "website_url": website_url,
            "list_type": list_type
        }
        # Do we need to save this as a result?
        collection.insert_one(new_entry)

        return EditBlockListResponse(
            status=ResponseStatus.SUCCESS,
            user_id=user_id,
            website_url=website_url,
            list_type=list_type
        )
    
    def delete_blocklist(self, user_id: str, website_url: str, list_type: BlockListType) -> EditBlockListResponse:
        """Delete an url from blocklist."""
        collection = self.db.get_collection("blocklist")
        query = {
            "user_id": user_id,
            "domain": website_url,
            "list_type": list_type
        }
        result = collection.delete_one(query)
        # if nothing was deleted, return a failed response
        if result.deleted_count == 0:
            return EditBlockListResponse(
                status=ResponseStatus.FAILED,
                user_id=user_id,
                website_url=website_url,
                list_type=list_type
            )
        return EditBlockListResponse(
            status=ResponseStatus.SUCCESS,
            user_id=user_id,
            website_url=website_url,
            list_type=list_type
        )