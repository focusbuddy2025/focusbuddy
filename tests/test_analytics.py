#!/usr/bin/env python
# -*- encoding=utf8 -*-
import unittest

from src.api import ResponseStatus
from src.db import MongoDB
from src.service import AnalyticsListService

from tests.test_utils import get_test_app


class TestAnalytics(unittest.TestCase):
    app = get_test_app()
    db = MongoDB().db

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
        collection = self.db.get_collection("analytics")

        test_entry = {
            "user_id": "test_user",
            "daily": 120,
            "weekly": 600,
            "completed_sessions": 2,
            "active": True,
        }

        collection.insert_one(test_entry)

        response = self.service.get_analytics(user_id="test_user")
        assert response.status == ResponseStatus.SUCCESS

        assert response.model_dump() == {
            "daily": 120,
            "weekly": 600,
            "completed_sessions": 2,
            "status": ResponseStatus.SUCCESS,
        }
