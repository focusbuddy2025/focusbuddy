#!/usr/bin/env python
# -*- encoding=utf8 -*-

import requests
import datetime

import jwt
import uuid

from src.db import MongoDB
from src.config import Config


class UserService(object):
    """class to handle user service"""
    _user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self, cfg: Config):
        self.db = MongoDB().db
        self.cfg = cfg

    def _get_user_from_google(self, token: str) -> (str, str):
        """Get user email from token."""
        user_info_response = requests.get(self._user_info_url, headers={"Authorization": f"Bearer {token}"})
        user_info = user_info_response.json()
        if user_info.get("email") is None:
            return "", ""
        return user_info["email"], user_info["picture"]

    def _get_user_info(self, token: str) -> dict:
        """Get user secret key from token."""
        email, picture = self._get_user_from_google(token)
        if email == "":
            return {}
        collection = self.db.get_collection("user")
        user = collection.find_one({"email": email})
        if user is None:
            res = collection.insert_one({"email": email})
            return {"email": email, "id": str(res.inserted_id), "picture": picture}
        return {"email": email, "id": str(user["_id"]), "picture": picture}

    def get_user_app_token(self, token: str) -> (str, str, str):
        """Get user app token from token."""
        info = self._get_user_info(token)
        if info["email"] == "":
            return "", "", ""
        return jwt.encode({
            "user_id": info["id"],
            "email": info["email"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, self.cfg.secret_key, algorithm="HS256"), info["picture"], info["email"]

    def get_user(self, jwt_token: str) -> dict:
        """Get user info from token."""
        try:
            decoded = jwt.decode(jwt_token, key=self.cfg.secret_key, algorithms=["HS256"])
            return decoded
        except jwt.ExpiredSignatureError:
            return {}
        except jwt.DecodeError:
            return {}
        except jwt.InvalidTokenError:
            return {}
        except Exception as e:
            print(e)
            return {}
