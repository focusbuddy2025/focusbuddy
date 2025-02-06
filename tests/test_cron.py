#!/usr/bin/env python
# -*- encoding=utf8 -*-
import unittest
from datetime import datetime, timedelta

from bson import ObjectId
from cron.cmd import reset_collection, update_collection
from cron.db import MongoDB
from cron.main import app
from typer.testing import CliRunner


class TestAnalyticsCronReset(unittest.TestCase):
    db = MongoDB().db

    def test_reset_weekly_analytics(self):
        self.db = MongoDB().db

        # Insert test values #
        analytics_col = self.db.get_collection("analytics")
        users_col = self.db.get_collection("users")

        test_users = [
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "user_status": 4,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "user_status": 4,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "user_status": 4,
            },
        ]
        users_col.insert_many(test_users)
        assert users_col.count_documents({}) == 3

        test_analytics = [
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "daily": 120,
                "weekly": 600,
                "active": True,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "daily": 200,
                "weekly": 800,
                "active": True,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "daily": 300,
                "weekly": 1000,
                "active": True,
            },
        ]

        analytics_col.insert_many(test_analytics)
        assert analytics_col.count_documents({}) == 3

        reset_collection(period="daily")
        reset_results = analytics_col.find({})
        for result in reset_results:
            assert result["daily"] == 0

        reset_collection(period="weekly")
        reset_results = analytics_col.find({})
        for result in reset_results:
            assert result["weekly"] == 0


class TestAnalyticsCronUpdate(unittest.TestCase):
    db = MongoDB().db

    def test_update_analytics(self):
        self.db = MongoDB().db

        # Insert test values #
        session_counter_col = self.db.get_collection("session_counter")
        focus_timer_col = self.db.get_collection("focus_timer")
        analytics_col = self.db.get_collection("analytics")

        session_counter_col_filter = {"session_id": 0}
        session_counter_col_update_op = {"$set": {"session_id": 0}}

        session_counter_col.update_one(
            session_counter_col_filter, session_counter_col_update_op
        )
        analytics_col.delete_many({})

        focus_timer = [
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "session_id": 1,
                "session_status": 3,
                "start_date": datetime.today().strftime("%Y-%m-%d"),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 3600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "session_id": 2,
                "session_status": 3,
                "start_date": datetime.today().strftime("%Y-%m-%d"),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 3600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "session_id": 3,
                "session_status": 3,
                "start_date": datetime.today().strftime("%Y-%m-%d"),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 3600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            },
        ]
        focus_timer_col.insert_many(focus_timer)
        assert focus_timer_col.count_documents({}) == 3

        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "daily": 120,
                "weekly": 600,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "daily": 200,
                "weekly": 800,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "daily": 300,
                "weekly": 1000,
                "active": True,
            }
        )

        assert analytics_col.count_documents({}) == 3

        update_collection()
        update_results = analytics_col.find({})

        assert update_results[0]["daily"] == 3720
        assert update_results[0]["weekly"] == 4200
        assert update_results[1]["daily"] == 3800
        assert update_results[1]["weekly"] == 4400
        assert update_results[2]["daily"] == 3900
        assert update_results[2]["weekly"] == 4600

        max_session_id = session_counter_col.find_one({})
        assert max_session_id["session_id"] == 3

        focus_timer_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_4",
                "session_id": 4,
                "session_status": 2,
                "start_date": (datetime.today() - timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                ),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 3600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            }
        )

        focus_timer_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_5",
                "session_id": 5,
                "session_status": 3,
                "start_date": (datetime.today() + timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                ),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 3600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            }
        )
        focus_timer_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_6",
                "session_id": 6,
                "session_status": 3,
                "start_date": datetime.today().strftime("%Y-%m-%d"),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            }
        )

        assert focus_timer_col.count_documents({}) == 6

        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_4",
                "daily": 120,
                "weekly": 600,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_5",
                "daily": 200,
                "weekly": 800,
                "active": True,
            }
        )

        assert analytics_col.count_documents({}) == 5

        update_collection()
        update_results = analytics_col.find({})

        assert update_results[0]["daily"] == 3720
        assert update_results[0]["weekly"] == 4200
        assert update_results[1]["daily"] == 3800
        assert update_results[1]["weekly"] == 4400
        assert update_results[2]["daily"] == 3900
        assert update_results[2]["weekly"] == 4600
        assert update_results[3]["daily"] == 120
        assert update_results[3]["weekly"] == 600
        assert update_results[4]["daily"] == 200
        assert update_results[4]["weekly"] == 800
        assert update_results[5]["daily"] == 600
        assert update_results[5]["weekly"] == 600


class TestAnalyticsCLICronReset(unittest.TestCase):
    db = MongoDB().db
    runner = CliRunner()

    def test_reset_weekly_analytics_cli(self):
        self.db = MongoDB().db
        self.runner = CliRunner()

        # Insert test values #
        analytics_col = self.db.get_collection("analytics")
        users_col = self.db.get_collection("users")

        test_users = [
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "user_status": 4,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "user_status": 4,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "user_status": 4,
            },
        ]

        users_col.delete_many({})
        users_col.insert_many(test_users)
        assert users_col.count_documents({}) == 3

        test_analytics = [
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "daily": 120,
                "weekly": 600,
                "active": True,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "daily": 200,
                "weekly": 800,
                "active": True,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "daily": 300,
                "weekly": 1000,
                "active": True,
            },
        ]

        analytics_col.delete_many({})
        analytics_col.insert_many(test_analytics)
        assert analytics_col.count_documents({}) == 3

        reset_results = self.runner.invoke(
            app, ["reset-analytics", "--period", "weekly"]
        )
        assert reset_results.exit_code == 0
        assert "Resetting analytics" in reset_results.stdout


class TestAnalyticsCLICronUpdate(unittest.TestCase):
    db = MongoDB().db
    runner = CliRunner()

    def test_update_analytics_cli(self):
        self.db = MongoDB().db
        self.runner = CliRunner()

        # Insert test values #
        session_counter_col = self.db.get_collection("session_counter")
        focus_timer_col = self.db.get_collection("focus_timer")
        analytics_col = self.db.get_collection("analytics")

        session_counter_col.delete_many({})
        focus_timer_col.delete_many({})
        analytics_col.delete_many({})

        session_counter_col_filter = {"session_id": 0}
        session_counter_col_update_op = {"$set": {"session_id": 0}}

        session_counter_col.update_one(
            session_counter_col_filter, session_counter_col_update_op
        )

        focus_timer = [
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "session_id": 1,
                "session_status": 3,
                "start_date": datetime.today().strftime("%Y-%m-%d"),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 3600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "session_id": 2,
                "session_status": 3,
                "start_date": datetime.today().strftime("%Y-%m-%d"),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 3600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            },
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "session_id": 3,
                "session_status": 3,
                "start_date": datetime.today().strftime("%Y-%m-%d"),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 3600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            },
        ]
        focus_timer_col.insert_many(focus_timer)
        assert focus_timer_col.count_documents({}) == 3

        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "daily": 120,
                "weekly": 600,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "daily": 200,
                "weekly": 800,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "daily": 300,
                "weekly": 1000,
                "active": True,
            }
        )

        assert analytics_col.count_documents({}) == 3

        update_results = self.runner.invoke(app, ["update-analytics"])
        assert update_results.exit_code == 0
        assert "Updating analytics" in update_results.stdout

        max_session_id = session_counter_col.find_one({})
        assert max_session_id["session_id"] == 3

        focus_timer_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_4",
                "session_id": 4,
                "session_status": 2,
                "start_date": (datetime.today() - timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                ),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 3600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            }
        )

        focus_timer_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_5",
                "session_id": 5,
                "session_status": 3,
                "start_date": (datetime.today() + timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                ),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 3600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            }
        )
        focus_timer_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_6",
                "session_id": 6,
                "session_status": 3,
                "start_date": datetime.today().strftime("%Y-%m-%d"),
                "start_time": datetime.today().strftime("%H-%M-%S"),
                "duration": 600,
                "break_time": 300,
                "type": 1,
                "remaining_runtime": 1800,
                "remaining_breaktime": 0,
            }
        )

        assert focus_timer_col.count_documents({}) == 6

        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_4",
                "daily": 120,
                "weekly": 600,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_5",
                "daily": 200,
                "weekly": 800,
                "active": True,
            }
        )

        assert analytics_col.count_documents({}) == 5

        update_results = self.runner.invoke(app, ["update-analytics"])
        assert update_results.exit_code == 0
        assert "Updating analytics" in update_results.stdout

        max_session_id = session_counter_col.find_one({})
        assert max_session_id["session_id"] == 6
