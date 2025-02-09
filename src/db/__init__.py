#!/usr/bin/env python
# -*- encoding=utf8 -*-
import os

from pymongo import ASCENDING, MongoClient
from testcontainers.mongodb import MongoDbContainer

from src.config import Config


class MongoDB:
    """class to encapsulate the MongoDB connection."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cfg = Config()
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance.cfg = cfg
            if os.getenv("ENV") == "test":
                mongo = MongoDbContainer("mongo:latest")
                mongo.start()
                cls._instance.client = mongo.get_connection_client()
            else:
                cls._instance.client = MongoClient(
                    cls._instance.cfg.db_host,
                    cls._instance.cfg.db_port,
                    username=cls._instance.cfg.db_user_name,
                    password=cls._instance.cfg.db_password,
                    timeoutMS=2000,
                    socketTimeoutMS=2000,
                    connectTimeoutMS=3000,
                )
            cls._instance.db = cls._instance.client[cls._instance.cfg.db]
            cls._instance._init_index(
                "blocklist",
                [
                    ("user_id", ASCENDING),
                    ("domain", ASCENDING),
                    ("list_type", ASCENDING),
                ],
            )
            cls._instance._init_index(
                "analytics",
                [
                    ("user_id", ASCENDING),
                ],
            )
        return cls._instance

    def _init_index(self, collection_name, index):
        self.db[collection_name].create_index(index, unique=True)

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def close(self):
        self.client.close()
