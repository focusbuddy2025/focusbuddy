#!/usr/bin/env python
# -*- encoding=utf8 -*-
import os

from fastapi.testclient import TestClient


def get_test_app():
    os.environ["ENV"] = "test"
    from src.rest import app
    return TestClient(app)
