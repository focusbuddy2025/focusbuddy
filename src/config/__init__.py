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
        if not hasattr(self, "initialized"):
            self.db_host = os.getenv("DB_HOST", "localhost")
            self.db_port = int(os.getenv("DB_PORT", 27017))
            self.db_user_name = os.getenv("DB_USER_NAME", "admin")
            self.db_password = os.getenv("DB_PASSWORD", "admin")
            self.db = os.getenv("DB", "focusbuddy")
            self.db_uri = os.getenv("DB_URI", "")

            self.app_host = os.getenv("APP_HOST", "localhost")
            self.app_port = int(os.getenv("APP_PORT", 8000))
            self.initialized = True

            self.secret_key = os.getenv(
                "SECRET_KEY", "70dd17f8-b3cd-4b1a-a09a-7cdf68c59fdc"
            )

            self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
            self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            self.smtp_username = os.environ.get(
                "SMTP_USERNAME", "ece651.group10@gmail.com"
            )
            self.smtp_password = os.environ.get("SMTP_PASSWORD", "cjdjlqijxkajcpgi")
            self.from_email = os.environ.get("FROM_EMAIL", "ece651.group10@gmail.com")

            self.broker_url = os.environ.get(
                "CELERY_BROKER_URL", "redis://redis:6379/0"
            )
            self.backend_url = os.environ.get(
                "CELERY_RESULT_BACKEND", "redis://redis:6379/0"
            )
