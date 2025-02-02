#!/usr/bin/env python
# -*- encoding=utf8 -*-
import os
import unittest

from tests.test_utils import get_test_app
from src.api import ResponseStatus


class TestBlockList(unittest.TestCase):
    app = get_test_app()

    def test_list_blocklist(self):
        response = self.app.get("/api/v1/blocklist/test")
        assert response.status_code == 200
        print(response.json())
        assert response.json() == {
            "blocklist": [],
            "status": ResponseStatus.SUCCESS,
        }
