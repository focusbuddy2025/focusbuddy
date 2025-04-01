#!/usr/bin/env python
# -*- encoding=utf8 -*-
import unittest
from bson import ObjectId

from src.config import Config
from src.service.user import UserService
from tests.test_utils import get_test_app
from src.api import ResponseStatus, SessionStatus, SessionType
from src.db import MongoDB
from src.service.focustimer import FocusTimerService


class TestFocusTimer(unittest.TestCase):
    app = get_test_app()
    db = MongoDB().db
    user_service = UserService(cfg=Config())
    user_id = "focusbuddy_test"
    jwt_token = user_service._generate_jwt("focusbuddy_test", "focusbuddy.test@gmail.com")

    def test_get_all_focustimer(self):
        response = self.app.get("/api/v1/focustimer", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200
        assert response.json() == {
            "focus_sessions": [],
            "status": ResponseStatus.SUCCESS,
        }

    def test_get_all_focustimer_non_empty(self):
        collection = self.db.get_collection("focus_timer")
        collection.delete_many({})
        test_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2026",
            "start_time": "23:16:15",
            "duration": 1,
            "break_duration": 1,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60
        }
        inserted_id = collection.insert_one(test_entry).inserted_id
        response = self.app.get("/api/v1/focustimer", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200
        assert response.json() == {
            "focus_sessions": [
                {
                    "session_id": str(inserted_id),
                    "session_status": 0,
                    "start_date": "02/22/2026",
                    "start_time": "23:16:15",
                    "duration": 1,
                    "break_duration": 1,
                    "session_type": 0,
                    "remaining_focus_time": 60,
                    "remaining_break_time": 60
                }
            ],
            "status": ResponseStatus.SUCCESS,
        }

    def setUp(self):
        self.db = MongoDB().db
        self.service = FocusTimerService(cfg=None)
        self.service.db = self.db
        self.db.get_collection("focus_timer").delete_many({})

    def test_add_focus_timer(self):
        response = self.service.add_focus_session(
            user_id="test_user",
            session_status=SessionStatus.UPCOMING,
            start_date="02/22/2026",
            start_time="23:16:15",
            duration=1,
            break_duration=1,
            session_type=SessionType.WORK,
            remaining_focus_time=60,
            remaining_break_time=60
        )
        assert response[0] != ""
        assert response[1] is True

    def test_add_conflic_session(self):
        collection = self.db.get_collection("focus_timer")
        collection.delete_many({})
        test_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2026",
            "start_time": "23:16:15",
            "duration": 1,
            "break_duration": 1,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60
        }
        response = self.app.post("/api/v1/focustimer", json=test_entry, headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200

        test_entry2 = test_entry.copy()
        test_entry2["start_time"] = "23:15:15"
        response = self.app.post("/api/v1/focustimer", json=test_entry2, headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 409

    def test_update_focus_timer(self):
        collection = self.db.get_collection("focus_timer")
        test_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2025",
            "start_time": "23:00:00",
            "duration": 30,
            "break_duration": 5,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 1800,
            "remaining_break_time": 300
        }
        inserted_id = collection.insert_one(test_entry).inserted_id

        response = self.app.put(f"/api/v1/focustimer/{str(inserted_id)}", json={}, headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 400

        response = self.app.put(
            f"/api/v1/focustimer/{str(inserted_id)}",
            json={"session_type": SessionType.PERSONAL},
            headers={"x-auth-token": self.jwt_token}
        )
        assert response.status_code == 200
        assert response.json() == {
            "user_id": self.user_id,
            "id": str(inserted_id),
            "status": ResponseStatus.SUCCESS,
        }

        conflict_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2025",
            "start_time": "23:25:00",
            "duration": 30,
            "break_duration": 5,
            "session_type": SessionType.STUDY,
            "remaining_focus_time": 1800,
            "remaining_break_time": 300
        }
        conflict_id = collection.insert_one(conflict_entry).inserted_id

        response = self.app.put(
            f"/api/v1/focustimer/{str(conflict_id)}",
            json={"start_time": "23:10:00"},
            headers={"x-auth-token": self.jwt_token}
        )
        assert response.status_code == 409

        response = self.app.put(
            f"/api/v1/focustimer/{str(inserted_id)}",
            json={"start_time": "22:00:00"},
            headers={"x-auth-token": self.jwt_token}
        )
        assert response.status_code == 200
        assert response.json() == {
            "user_id": self.user_id,
            "id": str(inserted_id),
            "status": ResponseStatus.SUCCESS,
        }

    def test_delete_valid_entry(self):
        collection = self.db.get_collection("focus_timer")
        test_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2026",
            "start_time": "23:16:15",
            "duration": 1,
            "break_duration": 1,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60
        }
        inserted_id = collection.insert_one(test_entry).inserted_id
        response = self.app.delete(f"/api/v1/focustimer/{str(inserted_id)}", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 204
        assert collection.count_documents({"_id": inserted_id}) == 0

    def test_delete_non_existent_entry(self):
        response = self.app.delete(f"/api/v1/focustimer/{str(ObjectId())}", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 404

    @classmethod
    def tearDownClass(cls):
        """Close Mongo client after all tests."""
        MongoDB().close()
