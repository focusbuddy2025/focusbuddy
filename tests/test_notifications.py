#!/usr/bin/env python
# -*- encoding=utf8 -*-
import base64
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from src.api import SessionStatus, SessionType
from src.config import Config
from src.db import MongoDB
from src.service import NotificationService
from src.service.user import UserService

from tests.test_utils import get_test_app


class TestNotifications(unittest.TestCase):
    app = get_test_app()
    db = MongoDB().db
    user_service = UserService(cfg=Config())
    user_id = "focusbuddy_test"
    jwt_token = user_service._generate_jwt(
        "focusbuddy_test", "focusbuddy.test@gmail.com"
    )

    user_id_db = user_service._get_user_id_from_db("focusbuddy.test@gmail.com")

    def test_get_notification_status(self):
        self.db = MongoDB().db
        self.service = NotificationService(cfg=None)
        self.service.db = self.db

        response = self.service.get_notification(user_id=self.user_id_db)

        self.assertDictEqual(
            response,
            {
                "browser": False,
                "email_notification": False,
            },
        )

    def test_update_enable_browser_notification_status(self):
        self.db = MongoDB().db
        self.service = NotificationService(cfg=None)
        self.service.db = self.db

        response = self.service.update_notification(
            user_id=self.user_id_db, notification_type="browser", enabled=True
        )

        self.assertEqual(response, True)

        collection = self.db.get_collection("user")

        result = collection.find_one({"email": "focusbuddy.test@gmail.com"})
        self.assertDictEqual(
            result["notification"],
            {
                "browser": True,
                "email_notification": False,
            },
        )

    def test_update_enable_email_notification_status(self):
        self.db = MongoDB().db
        self.service = NotificationService(cfg=None)
        self.service.db = self.db

        response = self.service.update_notification(
            user_id=self.user_id_db,
            notification_type="email",
            enabled=True,
        )

        self.assertEqual(response, True)

        collection = self.db.get_collection("user")

        result = collection.find_one({"email": "focusbuddy.test@gmail.com"})
        self.assertDictEqual(
            result["notification"],
            {
                "browser": True,
                "email_notification": True,
            },
        )

    def test_update_enable_invalid_notification_status(self):
        self.db = MongoDB().db
        self.service = NotificationService(cfg=None)
        self.service.db = self.db

        with self.assertRaises(ValueError):
            self.service.update_notification(
                user_id=self.user_id_db,
                notification_type="slack",
                enabled=True,
            )

    def test_graph_generation_no_data(self):
        self.db = MongoDB().db
        self.service = NotificationService(cfg=None)
        self.service.db = self.db

        day_data = {}
        img_str, max_day = self.service.generate_stacked_bar_chart(day_data)
        self.assertEqual(img_str, "")
        self.assertEqual(max_day, "")

    def test_chart_generation_with_data(self):
        self.db = MongoDB().db
        self.service = NotificationService(cfg=None)
        self.service.db = self.db

        day_data = {
            "Monday": {0: 10, 1: 5, 2: 0, 3: 0},
            "Wednesday": {0: 2, 1: 8, 2: 1, 3: 0},
        }
        img_str, max_day = self.service.generate_stacked_bar_chart(day_data)

        self.assertIsInstance(img_str, str)
        self.assertGreater(len(img_str), 0)

        self.assertIn(max_day, day_data.keys())

    @patch("smtplib.SMTP")
    def test_send_email(self, mock_smtp):
        self.db = MongoDB().db
        self.cfg = Config()
        self.service = NotificationService(cfg=self.cfg)
        self.service.db = self.db

        to_email = "focusbuddy.test@gmail.com"
        max_day = "Monday"
        summary_text = "This is a summary of your weekly focus sessions."

        dummy_png = b"\x89PNG\r\n\x1a\n"
        chart_b64 = base64.b64encode(dummy_png).decode("utf-8")

        mock_server = MagicMock()

        mock_smtp.return_value.__enter__.return_value = mock_server

        self.service.send_email(to_email, chart_b64, max_day, summary_text)

        mock_server.starttls.assert_called_once()

        mock_server.login.assert_called_once_with(
            self.cfg.smtp_username, self.cfg.smtp_password
        )

        mock_server.sendmail.assert_called_once()
        sendmail_call_args = mock_server.sendmail.call_args[0]

        self.assertEqual(sendmail_call_args[0], self.cfg.from_email)
        self.assertEqual(sendmail_call_args[1], to_email)

        self.assertIn("Your Weekly Focus Sessions Summary", sendmail_call_args[2])
        self.assertIn(summary_text, sendmail_call_args[2])


class TestWeeklyAggregateSummary(unittest.TestCase):
    app = get_test_app()
    db = MongoDB().db
    user_service = UserService(cfg=Config())
    user_id = "focusbuddy_test"
    jwt_token = user_service._generate_jwt(
        "focusbuddy_test", "focusbuddy.test@gmail.com"
    )

    user_id_db = user_service._get_user_id_from_db("focusbuddy.test@gmail.com")

    def test_aggregate_weekly_summary(self):
        self.db = MongoDB().db
        self.service = NotificationService(cfg=None)
        self.service.db = self.db

        # enable email notification for the user #
        self.service.update_notification(
            user_id=self.user_id_db,
            notification_type="email",
            enabled=True,
        )

        # Insert test focus session #
        collection = self.db.get_collection("focus_timer")

        test_entry = {
            "user_id": self.user_id_db,
            "session_status": SessionStatus.COMPLETED,
            "start_date": (
                datetime.now(ZoneInfo("America/Toronto")) - timedelta(days=1)
            ).strftime("%m/%d/%Y"),
            "start_time": (
                datetime.now(ZoneInfo("America/Toronto")) - timedelta(days=1)
            ).strftime("%H-%M-%S"),
            "duration": 120,
            "break_duration": 30,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60,
        }

        collection.insert_one(test_entry)

        summaries = self.service.aggregate_weekly_summary()

        self.assertEqual(len(summaries), 1)
        summary = summaries[0]
        self.assertEqual(summary["email"], "focusbuddy.test@gmail.com")

        self.assertTrue(len(summary["summary_text"]) > 0)

        self.assertTrue(len(summary["chart_b64"]) > 0)

        decoded_img = base64.b64decode(summary["chart_b64"])
        self.assertTrue(decoded_img.startswith(b"\x89PNG\r\n\x1a\n"))

        expected_days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        self.assertIn(summary["max_day"], expected_days)
