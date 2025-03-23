#!/usr/bin/env python
# -*- encoding=utf8 -*-
import unittest

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
