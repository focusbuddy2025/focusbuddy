#!/usr/bin/env python
# -*- encoding=utf8 -*-
import re

from bson import ObjectId
from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from src.api import (
    AddBlockListRequest,
    AnalyticsListResponse,
    EditBlockListResponse,
    ListBlockListResponse,
    ResponseStatus,
)
from src.config import Config, api_version
from src.rest.error import (
    BLOCKLIST_ALREADY_EXISTS,
    BLOCKLIST_ID_INVALID,
    BLOCKLIST_IS_INVALID,
    BLOCKLIST_NOT_FOUND,
)
from src.service import AnalyticsListService, BlockListService


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
        self.router.add_api_route(
            path="/blocklist/{user_id}",
            endpoint=self.add_blocklist,
            methods=["POST"],
            response_model=EditBlockListResponse,
            summary="Add a blocklist url",
        )

        self.router.add_api_route(
            path="/blocklist/{user_id}/{blocklist_id}",
            endpoint=self.delete_blocklist,
            methods=["DELETE"],
            response_model=EditBlockListResponse,
            summary="Delete a blocklist url",
        )

    async def list_blocklist(self, user_id: str):
        """List all blocklist."""
        response = self.blocklist_service.list_blocklist(user_id)
        return ListBlockListResponse(blocklist=response, status=ResponseStatus.SUCCESS)

    async def add_blocklist(self, user_id: str, request: AddBlockListRequest):
        """Add an url to blocklist."""
        if not self.validate_domain(request.domain):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=BLOCKLIST_IS_INVALID
            )

        new_id, ok = self.blocklist_service.add_blocklist(
            user_id, request.domain, request.list_type
        )
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=BLOCKLIST_ALREADY_EXISTS
            )
        return EditBlockListResponse(
            user_id=user_id,
            domain=request.domain,
            list_type=request.list_type,
            status=ResponseStatus.SUCCESS,
            id=new_id,
        )

    async def delete_blocklist(self, user_id: str, blocklist_id: str):
        """Delete an url from blocklist."""
        if not ObjectId.is_valid(blocklist_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=BLOCKLIST_ID_INVALID
            )

        ok = self.blocklist_service.delete_blocklist(user_id, blocklist_id)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=BLOCKLIST_NOT_FOUND
            )
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={})

    @staticmethod
    def validate_domain(domain: str):
        """Validate the domain."""
        url_regex = re.compile(
            r"^(https?:\/\/)?"  # Optional http or https
            r"(([A-Za-z0-9-]+\.)+[A-Za-z]{2,6})"  # Domain (e.g., example.com)
            r"(:\d{1,5})?"  # Optional port (e.g., :8080)
            r"(\/[^\s]*)?$"  # Optional path (e.g., /path/to/page)
        )
        return url_regex.match(domain)


class AnalyticsListAPI(object):
    """class to encapsulate the analytics API endpoint."""

    def __init__(self, cfg: Config):
        self.router = APIRouter()
        self.analyticslist_service = AnalyticsListService(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/analytics/{user_id}",
            endpoint=self.list_analytics,
            methods=["GET"],
            response_model=AnalyticsListResponse,
            summary="List all analytics for user",
        )

    async def list_analytics(self, user_id: str):
        """List all analytics for user."""
        response = self.analyticslist_service.get_analytics(user_id)
        return response


def create_app(cfg: Config):
    _app = FastAPI()
    blocklist_api = BlockListAPI(cfg)
    analyticslist_api = AnalyticsListAPI(cfg)
    _app.include_router(blocklist_api.router, prefix=api_version)
    _app.include_router(analyticslist_api.router, prefix=api_version)
    return _app


app = create_app(Config())
