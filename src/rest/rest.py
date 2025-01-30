#!/usr/bin/env python
# -*- encoding=utf8 -*-

from fastapi import FastAPI, APIRouter

from src.api import ListBlockListResponse, BlockListType
from src.service import BlockListService
from src.config import api_version, Config


class BlockListAPI(object):
    """class to encapsulate the blocklist API endpoints."""

    def __init__(self, cfg: Config):
        self.router = APIRouter()
        self.blocklist_service = BlockListService(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/blocklist/{user_id}",
            endpoint=self.list_blocklist,
            methods=["GET"],
            response_model=ListBlockListResponse,
            summary="List all blocklist",
        )

    async def list_blocklist(self, user_id: str, list_type: BlockListType = BlockListType.WORK):
        """List all blocklist."""
        return self.blocklist_service.list_blocklist(user_id, list_type)


def create_app(cfg: Config):
    _app = FastAPI()
    blocklist_api = BlockListAPI(cfg)
    _app.include_router(blocklist_api.router, prefix=api_version)
    return _app

app = create_app(Config())
