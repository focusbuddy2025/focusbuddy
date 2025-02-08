#!/usr/bin/env python
# -*- encoding=utf8 -*-
import unittest
from bson import ObjectId

from src.config import Config
from src.service.user import UserService
from tests.test_utils import get_test_app
from src.api import ResponseStatus, BlockListType
from src.db import MongoDB  # Import the MongoDB singleton
from src.service.blocklist import BlockListService


class TestBlockList(unittest.TestCase):
    app = get_test_app()
    db = MongoDB().db
    user_service = UserService(cfg=Config())
    user_id = "focusbuddy_test"
    jwt_token = user_service._generate_jwt("focusbuddy_test", "focusbuddy.test@gmail.com")

    def test_list_blocklist(self):
        response = self.app.get("/api/v1/blocklist", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200
        assert response.json() == {
            "blocklist": [],
            "status": ResponseStatus.SUCCESS,
        }

    def test_list_blocklist_non_empty(self):
        test_entry = {
            "user_id": self.user_id,
            "list_type": BlockListType.WORK,
            "domain": "example.com"
        }
        collection = self.db.get_collection("blocklist")
        collection.delete_many({})
        inserted_id = collection.insert_one(test_entry).inserted_id

        response = self.app.get("/api/v1/blocklist", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200
        assert response.json() == {
            "blocklist": [
                {"id": str(inserted_id), "domain": "example.com", "list_type": BlockListType.WORK}
            ],
            "status": ResponseStatus.SUCCESS,
        }

    def test_list_blocklist_multiple_entries(self):
        test_entries = [
            {"user_id": self.user_id, "list_type": BlockListType.WORK, "domain": "example1.com"},
            {"user_id": self.user_id, "list_type": BlockListType.WORK, "domain": "example2.com"},
        ]
        collection = self.db.get_collection("blocklist")
        collection.delete_many({})
        inserted_ids = [collection.insert_one(entry).inserted_id for entry in test_entries]
        response = self.app.get("/api/v1/blocklist", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200

        assert response.json() == {
            "blocklist": [
                {"id": str(inserted_ids[0]), "domain": "example1.com", "list_type": BlockListType.WORK},
                {"id": str(inserted_ids[1]), "domain": "example2.com", "list_type": BlockListType.WORK},
            ],
            "status": ResponseStatus.SUCCESS,
        }

    def test_list_blocklist_different_users(self):
        test_entries = [
            {"user_id": self.user_id, "list_type": BlockListType.WORK, "domain": "example1.com"},
            {"user_id": "user", "list_type": BlockListType.WORK, "domain": "example2.com"},
        ]
        collection = self.db.get_collection("blocklist")
        collection.delete_many({})
        [collection.insert_one(entry) for entry in test_entries]

        response = self.app.get("/api/v1/blocklist", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200
        assert response.json() == {
            "blocklist": [
                {"id": str(entry["_id"]), "domain": "example1.com", "list_type": BlockListType.WORK}
                for entry in collection.find({"user_id": self.user_id})
            ],
            "status": ResponseStatus.SUCCESS,
        }

    def test_list_blocklist_different_list_types(self):
        test_entries = [
            {"user_id": self.user_id, "list_type": BlockListType.WORK, "domain": "work.com"},
            {"user_id": self.user_id, "list_type": BlockListType.PERSONAL, "domain": "personal.com"},
        ]
        collection = self.db.get_collection("blocklist")
        collection.delete_many({})
        [collection.insert_one(entry) for entry in test_entries]
        response = self.app.get("/api/v1/blocklist", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200
        assert len(response.json()["blocklist"]) == 2

    """Test add_blocklist."""

    def setUp(self):
        """Setup mock database before each test."""
        self.db = MongoDB().db
        self.service = BlockListService(cfg=None)
        self.service.db = self.db

        # Clear the collection before each test to prevent interference
        self.db.get_collection("blocklist").delete_many({})

    def test_add_valid_website(self):
        """Ensure adding valid websites returns correct response."""
        response = self.service.add_blocklist(
            user_id="test_user",
            domain="https://example.com",
            list_type=BlockListType.WORK
        )
        assert response[0] != ""  # Should return a valid ObjectId
        assert response[1] is True  # Should return True

    def test_add_duplicate_website(self):
        """Ensure duplicate website additions return FAILED."""
        self.service.add_blocklist("test_user", "https://example.com", BlockListType.WORK)
        response = self.service.add_blocklist("test_user", "https://example.com", BlockListType.WORK)

        assert response[1] == False  # Should return False

        collection = self.db.get_collection("blocklist")
        count = collection.count_documents({"user_id": "test_user", "domain": "https://example.com"})
        assert count == 1  # Should not add duplicate

    def test_list_blocklist_after_adding_entries(self):
        """Ensure list_blocklist retrieves added entries."""
        # Insert data using add_blocklist
        self.service.add_blocklist(self.user_id, "https://example1.com", BlockListType.WORK)
        self.service.add_blocklist(self.user_id, "https://example2.com", BlockListType.WORK)

        # Call API to retrieve blocklist
        response = self.app.get("/api/v1/blocklist", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200

        # Expected response
        collection = self.db.get_collection("blocklist")
        expected_blocklist = [
            {"id": str(entry["_id"]), "domain": entry["domain"], "list_type": entry["list_type"]}
            for entry in collection.find({"user_id": self.user_id})
        ]
        # print(response.json())
        assert response.json() == {
            "blocklist": expected_blocklist,
            "status": ResponseStatus.SUCCESS,
        }

    def test_add_invalid_url(self):
        """Test adding an invalid URL returns FAILED."""
        response = self.app.post("/api/v1/blocklist", json={"domain": "invalid_url", "list_type": BlockListType.WORK}, headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 400

        # Ensure no entry was added
        count = self.db.get_collection("blocklist").count_documents({"user_id": self.user_id, "domain": "invalid_url"})
        assert count == 0

    def test_add_website_different_users(self):
        """Ensure the same website is allowed for different users."""
        self.service.add_blocklist("user1", "https://example.com", BlockListType.WORK)
        self.service.add_blocklist("user2", "https://example.com", BlockListType.WORK)

        count = self.db.get_collection("blocklist").count_documents({"domain": "https://example.com"})
        assert count == 2  # Should allow the same URL for different users

    def test_add_website_different_list_types(self):
        """Ensure the same website can exist under different blocklist types."""
        self.service.add_blocklist("test_user", "https://example.com", BlockListType.WORK)
        self.service.add_blocklist("test_user", "https://example.com", BlockListType.PERSONAL)

        count = self.db.get_collection("blocklist").count_documents({"user_id": "test_user", "domain": "https://example.com"})
        assert count == 2  # Should allow different list types

    """Test delete_blocklist."""

    def test_delete_valid_entry(self):
        """Test deleting an existing blocklist entry."""
        collection = self.db.get_collection("blocklist")

        # Insert a test entry
        test_entry = {
            "user_id": self.user_id,
            "domain": "example.com",
            "list_type": BlockListType.WORK
        }
        inserted_id = collection.insert_one(test_entry).inserted_id

        # Delete the entry
        response = self.app.delete(f"/api/v1/blocklist/{str(inserted_id)}", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 204
        # Verify the entry is actually removed
        assert collection.count_documents({"_id": inserted_id}) == 0

    def test_delete_non_existent_entry(self):
        """Test deleting a non-existent blocklist entry."""
        response = self.app.delete(f"/api/v1/blocklist/{str(ObjectId())}", headers={"x-auth-token": self.jwt_token}) # Random ObjectId
        assert response.status_code == 404

    def test_delete_invalid_object_id(self):
        """Test deleting an entry with an invalid ObjectId format."""
        response = self.app.delete("/api/v1/blocklist/invalid_id", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 400

    def test_delete_entry_belongs_to_another_user(self):
        """Test that a user cannot delete another user's blocklist entry."""
        collection = self.db.get_collection("blocklist")

        # Insert a test entry for "user_1"
        test_entry = {
            "user_id": "user_1",
            "domain": "example.com",
            "list_type": BlockListType.WORK
        }
        inserted_id = collection.insert_one(test_entry).inserted_id

        # "test_user" tries to delete it
        response = self.app.delete(f"/api/v1/blocklist/{str(inserted_id)}", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 404

        # Ensure the entry still exists
        assert collection.count_documents({"_id": inserted_id}) == 1
