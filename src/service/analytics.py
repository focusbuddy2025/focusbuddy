#!/usr/bin/env python
# -*- encoding=utf8 -*-

from src.api import AnalyticsListResponse, ResponseStatus
from src.config import Config
from src.db import MongoDB


class AnalyticsListService(object):
    """class to encapsulate the analytics service."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = MongoDB().db

    def get_analytics(self, user_id: str) -> AnalyticsListResponse:
        """Get analytics per user."""
        collection = self.db.get_collection("analytics")
        query = {"user_id": user_id}
        analytics_result: dict = collection.find_one(query)
        if analytics_result is None:
            return AnalyticsListResponse(
                daily=0, weekly=0, status=ResponseStatus.FAILED
            )

        return AnalyticsListResponse(
            daily=analytics_result["daily"],
            weekly=analytics_result["weekly"],
            status=ResponseStatus.SUCCESS,
        )
