#!/usr/bin/env python
# -*- encoding=utf8 -*-
import os

api_version = "/api/v1"


class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.db_host = os.getenv("DB_HOST", "localhost")
            self.db_port = int(os.getenv("DB_PORT", 27017))
            self.db_user_name = os.getenv("DB_USER_NAME", "admin")
            self.db_password = os.getenv("DB_PASSWORD", "admin")
            self.db = os.getenv("DB", "focusbuddy")

            self.app_host = os.getenv("APP_HOST", "localhost")
            self.app_port = int(os.getenv("APP_PORT", 8000))
            self.initialized = True

            self.secret_key = os.getenv("SECRET_KEY", "70dd17f8-b3cd-4b1a-a09a-7cdf68c59fdc")
