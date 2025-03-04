#!/usr/bin/env python
# -*- encoding=utf8 -*-

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.api import (
    AnalyticsListResponse,
    AnalyticsWeeklySummaryResponse,
    ResponseStatus,
)
from src.config import Config
from src.db import MongoDB


def _convert_to_hours(time_in_seconds):
    """converts time from seconds to hours"""
    return round(time_in_seconds / 3600, 2)


class AnalyticsListService(object):
    """class to encapsulate the analytics service."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = MongoDB().db

    def _get_daily_focus_total(self, user_id: str) -> float:
        """Get daily summary per user"""
        collection = self.db.get_collection("focus_timer")
        start_date_filter = datetime.now(ZoneInfo("America/Toronto"))
        end_date_filter = start_date_filter + timedelta(days=1)

        start_date_str = start_date_filter.strftime("%m/%d/%Y")
        end_date_str = end_date_filter.strftime("%m/%d/%Y")

        pipeline = [
            {
                "$match": {
                    "start_date": {
                        "$gte": start_date_str,
                        "$lt": end_date_str,
                    },
                    "session_status": 3,
                    "user_id": user_id,
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_duration": {"$sum": "$duration"},
                }
            },
        ]

        daily_focus_total = list(collection.aggregate(pipeline))

        if daily_focus_total:
            return _convert_to_hours(daily_focus_total[0]["total_duration"])
        else:
            return 0

    def _get_weekly_focus_total(self, user_id: str) -> float:
        """Get weekly summary per user"""
        collection = self.db.get_collection("focus_timer")
        dow = datetime.now(ZoneInfo("America/Toronto")).isoweekday()
        start_date_filter = datetime.now(ZoneInfo("America/Toronto")) - timedelta(
            days=(dow)
        )
        if dow == 7:
            start_date_filter = datetime.now(ZoneInfo("America/Toronto"))
        end_date_filter = start_date_filter + timedelta(days=7)

        start_date_str = start_date_filter.strftime("%m/%d/%Y")
        end_date_str = end_date_filter.strftime("%m/%d/%Y")

        pipeline = [
            {
                "$match": {
                    "start_date": {
                        "$gte": start_date_str,
                        "$lt": end_date_str,
                    },
                    "session_status": 3,
                    "user_id": user_id,
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_duration": {"$sum": "$duration"},
                }
            },
        ]

        weekly_focus_total = list(collection.aggregate(pipeline))

        if weekly_focus_total:
            return _convert_to_hours(weekly_focus_total[0]["total_duration"])
        else:
            return 0

    def _all_completed_sessions(self, user_id: str) -> int:
        """Get count of all completed sessions (session_status 3) for a user"""
        collection = self.db.get_collection("focus_timer")

        pipeline = [
            {"$match": {"user_id": user_id, "session_status": 3}},
            {"$count": "total"},
        ]

        total_completed_sessions = list(collection.aggregate(pipeline))

        if total_completed_sessions:
            results = total_completed_sessions[0]["total"]
        else:
            results = 0

        return results

    def get_analytics(self, user_id: str) -> AnalyticsListResponse:
        """Get analytics per user."""
        user_col = self.db.get_collection("focus_timer")
        query = {"user_id": user_id}
        user_exists = user_col.find_one(query)
        if user_exists is None:
            return AnalyticsListResponse(
                daily=0.0,
                weekly=0.0,
                completed_sessions=0,
                status=ResponseStatus.FAILED,
            )

        daily_total = self._get_daily_focus_total(user_id)
        weekly_total = self._get_weekly_focus_total(user_id)
        completed_sessions_total = self._all_completed_sessions(user_id)

        return AnalyticsListResponse(
            daily=daily_total,
            weekly=weekly_total,
            completed_sessions=completed_sessions_total,
            status=ResponseStatus.SUCCESS,
        )


















    def get_weekly_analytics_per_session_type(
        self, user_id: str
    ) -> list[AnalyticsWeeklySummaryResponse]:
        """Get weekly summary per user per session type"""
        collection = self.db.get_collection("focus_timer")
        dow = datetime.now(ZoneInfo("America/Toronto")).isoweekday()
        start_date_filter = datetime.now(ZoneInfo("America/Toronto")) - timedelta(
            days=(dow)
        )
        if dow == 7:
            start_date_filter = datetime.now(ZoneInfo("America/Toronto"))
        end_date_filter = start_date_filter + timedelta(days=7)

        start_date_str = start_date_filter.strftime("%m/%d/%Y")
        end_date_str = end_date_filter.strftime("%m/%d/%Y")

        pipeline = [
            {
                "$match": {
                    "start_date": {
                        "$gte": start_date_str,
                        "$lt": end_date_str,
                    },
                    "session_status": {"$eq": 3},
                    "user_id": {"$eq": user_id},
                }
            },
            {
                "$group": {
                    "_id": {"session_type": "$session_type", "user_id": "$user_id"},
                    "duration": {"$sum": "$duration"},
                }
            },
        ]

        pipeline.append({"$set": {"user_id": "$_id"}})

        pipeline.append({"$unset": ["_id"]})

        weekly_summary = collection.aggregate(pipeline)

        results = [
            AnalyticsWeeklySummaryResponse(
                duration=_convert_to_hours(session["duration"]),
                user_id=session["user_id"]["user_id"],
                session_type=session["user_id"]["session_type"],
            )
            for session in weekly_summary
        ]

        return results
