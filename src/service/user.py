#!/usr/bin/env python
# -*- encoding=utf8 -*-

import datetime
from dataclasses import dataclass

import jwt
import requests
from bson import ObjectId

from src.api import UserStatus
from src.config import Config
from src.db import MongoDB


@dataclass
class User:
    jwt: str
    email: str
    picture: str


@dataclass
class DecodedUser:
    user_id: str
    email: str
    exp: float


class UserService(object):
    """class to handle user service"""

    _user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    jwt_algorithm = "HS256"

    def __init__(self, cfg: Config):
        self.db = MongoDB().db
        self.cfg = cfg

    def _get_user_from_google(self, token: str) -> (str, str):
        """Get user email from token."""
        user_info_response = requests.get(
            self._user_info_url, headers={"Authorization": f"Bearer {token}"}
        )
        user_info = user_info_response.json()
        if user_info.get("email") is None:
            return "", ""
        return user_info["email"], user_info["picture"]

    def _get_user_id_from_db(self, email: str) -> str:
        """Get user from db."""
        collection = self.db.get_collection("user")
        user = collection.find_one({"email": email})
        if user is None:
            res = collection.insert_one(
                {
                    "email": email,
                    "status": UserStatus.IDLE,
                    "notification": {"browser": False, "email_notification": False},
                }
            )
            return str(res.inserted_id)

        if "status" not in user:
            collection.update_one(
                {"_id": user["_id"]}, {"$set": {"status": UserStatus.IDLE}}
            )

        return str(user["_id"])

    def _generate_jwt(self, user_id: str, email: str) -> str:
        """Generate jwt token."""
        return jwt.encode(
            {
                "user_id": user_id,
                "email": email,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            },
            self.cfg.secret_key,
            algorithm=self.jwt_algorithm,
        )

    def get_user_app_token(self, token: str) -> User:
        """Get user app token from token."""
        email, picture = self._get_user_from_google(token)
        if email == "":
            return User("", "", "")
        user_id = self._get_user_id_from_db(email)
        return User(self._generate_jwt(user_id, email), email, picture)

    def decode_user(self, jwt_token: str) -> DecodedUser:
        """Get user info from token."""
        try:
            decoded = jwt.decode(
                jwt_token, key=self.cfg.secret_key, algorithms=["HS256"]
            )
            return DecodedUser(
                user_id=decoded["user_id"], email=decoded["email"], exp=decoded["exp"]
            )
        except jwt.ExpiredSignatureError:
            return DecodedUser(user_id="", email="", exp=0)
        except jwt.DecodeError:
            return DecodedUser(user_id="", email="", exp=0)
        except jwt.InvalidTokenError:
            return DecodedUser(user_id="", email="", exp=0)
        except Exception as e:
            print(e)
            return DecodedUser(user_id="", email="", exp=0)

    def update_user_status(self, user_id: str, status: str):
        """Update user status."""
        collection = self.db.get_collection("user")
        result = collection.update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"status": status}}
        )
        return result.modified_count > 0
