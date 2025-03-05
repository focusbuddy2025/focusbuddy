#!/usr/bin/env python
# -*- encoding=utf8 -*-
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.api import ResponseStatus, SessionStatus, SessionType
from src.config import Config
from src.db import MongoDB
from src.service import AnalyticsListService
from src.service.user import UserService

from tests.test_utils import get_test_app


class TestAnalytics(unittest.TestCase):
    app = get_test_app()
    db = MongoDB().db
    user_service = UserService(cfg=Config())
    user_id = "focusbuddy_test"
    jwt_token = user_service._generate_jwt(
        "focusbuddy_test", "focusbuddy.test@gmail.com"
    )

    def test_get_analytics_invalid_user(self):
        self.db = MongoDB().db
        self.service = AnalyticsListService(cfg=None)
        self.service.db = self.db

        response = self.service.get_analytics(user_id="test_user")
        assert response.status == ResponseStatus.FAILED
        assert response.model_dump() == {
            "daily": 0,
            "weekly": 0,
            "completed_sessions": 0,
            "status": ResponseStatus.FAILED,
        }

    def test_get_analytics_valid_user(self):
        self.db = MongoDB().db
        self.service = AnalyticsListService(cfg=None)
        self.service.db = self.db

        # Insert test values #
        collection = self.db.get_collection("focus_timer")

        test_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.COMPLETED,
            "start_date": datetime.now(ZoneInfo("America/Toronto")).strftime(
                "%m/%d/%Y"
            ),
            "start_time": datetime.now(ZoneInfo("America/Toronto")).strftime(
                "%m-%M-%S"
            ),
            "duration": 120,
            "break_duration": 30,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60,
        }

        collection.insert_one(test_entry)

        response = self.app.get(
            "/api/v1/analytics", headers={"x-auth-token": self.jwt_token}
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            {
                "daily": 1.98,
                "weekly": 1.98,
                "completed_sessions": 1,
                "status": ResponseStatus.SUCCESS,
            },
        )

    def test_get_weekly_summary_per_session_type(self):
        self.db = MongoDB().db
        self.service = AnalyticsListService(cfg=None)
        self.service.db = self.db

        # Insert test values #
        collection = self.db.get_collection("focus_timer")
        collection.delete_many({})
        test_entry_1 = {
            "user_id": self.user_id,
            "session_status": SessionStatus.COMPLETED,
            "start_date": datetime.now(ZoneInfo("America/Toronto")).strftime(
                "%m/%d/%Y"
            ),
            "start_time": datetime.now(ZoneInfo("America/Toronto")).strftime(
                "%m-%M-%S"
            ),
            "duration": 120,
            "break_duration": 10,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60,
        }

        test_entry_2 = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": datetime.now(ZoneInfo("America/Toronto")).strftime(
                "%m/%d/%Y"
            ),
            "start_time": datetime.now(ZoneInfo("America/Toronto")).strftime(
                "%H-%M-%S"
            ),
            "duration": 20,
            "break_duration": 1,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60,
        }

        test_entry_3 = {
            "user_id": self.user_id,
            "session_status": SessionStatus.COMPLETED,
            "start_date": (
                datetime.now(ZoneInfo("America/Toronto")) - timedelta(days=1)
            ).strftime("%m/%d/%Y"),
            "start_time": (
                datetime.now(ZoneInfo("America/Toronto")) - timedelta(days=1)
            ).strftime("%H-%M-%S"),
            "duration": 60,
            "break_duration": 1,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60,
        }

        collection.insert_one(test_entry_1)
        collection.insert_one(test_entry_2)
        collection.insert_one(test_entry_3)

        response = self.app.get(
            "/api/v1/analytics/weeklysummary",
            headers={"x-auth-token": self.jwt_token},
        )

        self.assertEqual(response.status_code, 200)
        expected_summary_response = [
            {
                "duration": 2.97,
                "user_id": "focusbuddy_test",
                "session_type": 0,
            }
        ]

        self.assertDictEqual(
            {"summary": expected_summary_response, "status": ResponseStatus.SUCCESS},
            response.json(),
        )
