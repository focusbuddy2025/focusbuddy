#!/usr/bin/env python
# -*- encoding=utf8 -*-

from datetime import datetime, timedelta

from src.api import (
    AnalyticsListResponse,
    AnalyticsWeeklySummaryResponse,
    ResponseStatus,
)
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
                daily=0, weekly=0, completed_sessions=0, status=ResponseStatus.FAILED
            )

        return AnalyticsListResponse(
            daily=analytics_result["daily"],
            weekly=analytics_result["weekly"],
            completed_sessions=analytics_result["completed_sessions"],
            status=ResponseStatus.SUCCESS,
        )

    def get_weekly_analytics_per_session_type(
        self, user_id: str
    ) -> list[AnalyticsWeeklySummaryResponse]:
        """Get weekly summary per user per session type"""
        collection = self.db.get_collection("focus_timer")
        dow = datetime.now().isoweekday()
        start_date_filter = datetime.now() - timedelta(days=(dow))
        if dow == 7:
            start_date_filter = datetime.now()
        end_date_filter = start_date_filter + timedelta(days=7)
        pipeline = []

        pipeline.append(
            {
                "$match": {
                    "$and": [
                        {
                            "start_date": {
                                "$gte": start_date_filter.strftime("%Y-%m-%d"),
                                "$lt": end_date_filter.strftime("%Y-%m-%d"),
                            }
                        },
                        {"session_status": {"$eq": 3}},
                        {"user_id": {"$eq": user_id}},
                    ]
                }
            }
        )

        pipeline.append(
            {
                "$group": {
                    "_id": {"session_type": "$session_type", "user_id": "$user_id"},
                    "duration": {"$sum": "$duration"},
                }
            }
        )

        pipeline.append({"$set": {"user_id": "$_id"}})

        pipeline.append({"$unset": ["_id"]})

        weekly_summary = collection.aggregate(pipeline)

        results = [
            AnalyticsWeeklySummaryResponse(
                duration=session["duration"],
                user_id=session["user_id"]["user_id"],
                session_type=session["user_id"]["session_type"],
            )
            for session in weekly_summary
        ]

        return results
