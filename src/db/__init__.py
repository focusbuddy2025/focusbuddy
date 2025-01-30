#!/usr/bin/env python
# -*- encoding=utf8 -*-

from pymongo import MongoClient

from src.config import Config


class MongoDB:
    """class to encapsulate the MongoDB connection."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cfg = Config()
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance.cfg = cfg
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
        return cls._instance

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def close(self):
        self.client.close()
