#!/usr/bin/env python
# -*- encoding=utf8 -*-
import unittest
from datetime import datetime, timedelta

from bson import ObjectId
from cron.cmd import AnalyticsCron
from cron.db import MongoDB
from cron.main import app
from typer.testing import CliRunner


class TestAnalyticsCronReset(unittest.TestCase):
    db = MongoDB().db

    def test_reset_weekly_analytics(self):
        self.db = MongoDB().db
        self.analytics_cron = AnalyticsCron(cfg=None)
        self.analytics_cron.db = self.db
        # Insert test values #
        analytics_col = self.db.get_collection("analytics")
        users_col = self.db.get_collection("users")
        users_col.delete_many({})
        users_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "user_status": 4,
            }
        )
        users_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "user_status": 4,
            }
        )
        users_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "user_status": 4,
            }
        )

        self.assertEqual(users_col.count_documents({}), 3)
        analytics_col.delete_many({})
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "daily": 120,
                "weekly": 600,
                "completed_sessions": 1,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "daily": 200,
                "weekly": 800,
                "completed_sessions": 2,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "daily": 300,
                "weekly": 1000,
                "completed_sessions": 10,
                "active": True,
            }
        )

        self.assertEqual(analytics_col.count_documents({}), 3)

        self.analytics_cron.reset_collection(period="daily")
        reset_results = analytics_col.find({})
        for result in reset_results:
            self.assertEqual(result["daily"], 0)
            self.assertNotEqual(result["weekly"], 0)

        self.analytics_cron.reset_collection(period="weekly")
        reset_results = analytics_col.find({})
        for result in reset_results:
            self.assertEqual(result["daily"], 0)
            self.assertEqual(result["weekly"], 0)


class TestAnalyticsCronUpdate(unittest.TestCase):
    # db = MongoDB().db

    def test_update_analytics(self):
        self.db = MongoDB().db
        self.analytics_cron = AnalyticsCron(cfg=None)
        self.analytics_cron.db = self.db

        # Insert test values #
        session_counter_col = self.db.get_collection("session_counter")
        focus_timer_col = self.db.get_collection("focus_timer")
        analytics_col = self.db.get_collection("analytics")

        session_counter_col_filter = {"session_id": 0}
        session_counter_col_update_op = {"$set": {"session_id": 0}}

        session_counter_col.update_one(
            session_counter_col_filter, session_counter_col_update_op
        )
        focus_timer_col.delete_many({})

        focus_timer_col.insert_one(
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
            }
        )
        focus_timer_col.insert_one(
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
            }
        )
        focus_timer_col.insert_one(
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
            }
        )

        self.assertEqual(focus_timer_col.count_documents({}), 3)
        analytics_col.delete_many({})
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "daily": 120,
                "weekly": 600,
                "completed_sessions": 1,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "daily": 200,
                "weekly": 800,
                "completed_sessions": 2,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "daily": 300,
                "weekly": 1000,
                "completed_sessions": 5,
                "active": True,
            }
        )

        self.assertEqual(analytics_col.count_documents({}), 3)
        self.analytics_cron.update_collection()
        update_results = analytics_col.find({})

        self.assertEqual(update_results[0]["daily"], 3720)
        self.assertEqual(update_results[0]["weekly"], 4200)
        self.assertEqual(update_results[0]["completed_sessions"], 2)
        self.assertEqual(update_results[1]["daily"], 3800)
        self.assertEqual(update_results[1]["weekly"], 4400)
        self.assertEqual(update_results[1]["completed_sessions"], 3)
        self.assertEqual(update_results[2]["daily"], 3900)
        self.assertEqual(update_results[2]["weekly"], 4600)
        self.assertEqual(update_results[2]["completed_sessions"], 6)

        max_session_id = session_counter_col.find_one({})
        self.assertEqual(max_session_id["session_id"], 3)

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

        self.assertEqual(focus_timer_col.count_documents({}), 6)

        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_4",
                "daily": 120,
                "weekly": 600,
                "completed_sessions": 1,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_5",
                "daily": 200,
                "weekly": 800,
                "completed_sessions": 2,
                "active": True,
            }
        )

        self.assertEqual(analytics_col.count_documents({}), 5)

        self.analytics_cron.update_collection()
        update_results = analytics_col.find({})

        self.assertEqual(update_results[0]["daily"], 3720)
        self.assertEqual(update_results[0]["weekly"], 4200)
        self.assertEqual(update_results[0]["completed_sessions"], 2)
        self.assertEqual(update_results[1]["daily"], 3800)
        self.assertEqual(update_results[1]["weekly"], 4400)
        self.assertEqual(update_results[1]["completed_sessions"], 3)
        self.assertEqual(update_results[2]["daily"], 3900)
        self.assertEqual(update_results[2]["weekly"], 4600)
        self.assertEqual(update_results[2]["completed_sessions"], 6)
        self.assertEqual(update_results[3]["daily"], 120)
        self.assertEqual(update_results[3]["weekly"], 600)
        self.assertEqual(update_results[3]["completed_sessions"], 1)
        self.assertEqual(update_results[4]["daily"], 200)
        self.assertEqual(update_results[4]["weekly"], 800)
        self.assertEqual(update_results[4]["completed_sessions"], 2)
        self.assertEqual(update_results[5]["daily"], 600)
        self.assertEqual(update_results[5]["weekly"], 600)
        self.assertEqual(update_results[5]["completed_sessions"], 1)


class TestAnalyticsCLICronReset(unittest.TestCase):
    db = MongoDB().db

    def test_reset_weekly_analytics_cli(self):
        self.db = MongoDB().db
        self.runner = CliRunner()
        self.analytics_cron = AnalyticsCron(cfg=None)
        self.analytics_cron.db = self.db

        # Insert test values #
        analytics_col = self.db.get_collection("analytics")
        users_col = self.db.get_collection("users")
        users_col.delete_many({})

        users_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "user_status": 4,
            }
        )
        users_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "user_status": 4,
            }
        )
        users_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "user_status": 4,
            }
        )

        self.assertEqual(users_col.count_documents({}), 3)
        analytics_col.delete_many({})

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

        self.assertEqual(analytics_col.count_documents({}), 3)

        reset_results = self.runner.invoke(
            app, ["reset-analytics", "--period", "weekly"]
        )
        self.assertEqual(reset_results.exit_code, 0)
        self.assertIn("Resetting analytics", reset_results.stdout)


class TestAnalyticsCLICronUpdate(unittest.TestCase):
    db = MongoDB().db
    runner = CliRunner()

    def test_update_analytics_cli(self):
        self.db = MongoDB().db
        self.runner = CliRunner()
        self.analytics_cron = AnalyticsCron(cfg=None)
        self.analytics_cron.db = self.db

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
        focus_timer_col.delete_many({})
        focus_timer_col.insert_one(
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
            }
        )
        focus_timer_col.insert_one(
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
            }
        )
        focus_timer_col.insert_one(
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
            }
        )

        self.assertEqual(focus_timer_col.count_documents({}), 3)
        analytics_col.delete_many({})
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_1",
                "daily": 120,
                "weekly": 600,
                "completed_sessions": 1,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_2",
                "daily": 200,
                "weekly": 800,
                "completed_sessions": 2,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_3",
                "daily": 300,
                "weekly": 1000,
                "completed_sessions": 5,
                "active": True,
            }
        )

        self.assertEqual(analytics_col.count_documents({}), 3)

        update_results = self.runner.invoke(app, ["update-analytics"])
        self.assertEqual(update_results.exit_code, 0)
        self.assertIn("Updating analytics", update_results.stdout)

        max_session_id = session_counter_col.find_one({})
        self.assertEqual(max_session_id["session_id"], 3)

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

        self.assertEqual(focus_timer_col.count_documents({}), 6)

        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_4",
                "daily": 120,
                "weekly": 600,
                "completed_sessions": 1,
                "active": True,
            }
        )
        analytics_col.insert_one(
            {
                "_id": ObjectId(),
                "user_id": "test_user_5",
                "daily": 200,
                "weekly": 800,
                "completed_sessions": 2,
                "active": True,
            }
        )

        self.assertEqual(analytics_col.count_documents({}), 5)

        update_results = self.runner.invoke(app, ["update-analytics"])
        self.assertEqual(update_results.exit_code, 0)
        self.assertIn("Updating analytics", update_results.stdout)

        max_session_id = session_counter_col.find_one({})
        assert max_session_id["session_id"] == 6
