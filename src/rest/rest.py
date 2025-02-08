#!/usr/bin/env python
# -*- encoding=utf8 -*-
import datetime
import re
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, FastAPI, HTTPException, Response, status, Header

from src.api import (
    AddBlockListRequest,
    AnalyticsListResponse,
    EditBlockListResponse,
    ListBlockListResponse,
    ResponseStatus,
    GetUserAppTokenResponse,
    GetUserAppTokenRequest,
)
from src.config import Config, api_version
from src.rest.error import (
    BLOCKLIST_ALREADY_EXISTS,
    BLOCKLIST_ID_INVALID,
    BLOCKLIST_IS_INVALID,
    BLOCKLIST_NOT_FOUND,
    INVALID_TOKEN,
)
from src.service import AnalyticsListService, BlockListService
from src.service.user import UserService


class BlockListAPI(object):
    """class to encapsulate the blocklist API endpoints."""

    def __init__(self, cfg: Config):
        self.router = APIRouter()
        self.blocklist_service = BlockListService(cfg)
        self.user_service = UserService(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/blocklist",
            endpoint=self.list_blocklist,
            methods=["GET"],
            response_model=ListBlockListResponse,
            summary="List all blocklist",
        )
        self.router.add_api_route(
            path="/blocklist",
            endpoint=self.add_blocklist,
            methods=["POST"],
            response_model=EditBlockListResponse,
            summary="Add a blocklist url",
        )
        self.router.add_api_route(
            path="/blocklist/{blocklist_id}",
            endpoint=self.delete_blocklist,
            methods=["DELETE"],
            response_model=EditBlockListResponse,
            summary="Delete a blocklist url",
        )

    async def list_blocklist(self, x_auth_token: Annotated[str, Header()] = None):
        """List all blocklist."""
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        response = self.blocklist_service.list_blocklist(user_id)
        return ListBlockListResponse(blocklist=response, status=ResponseStatus.SUCCESS)

    async def add_blocklist(self, request: AddBlockListRequest, x_auth_token: Annotated[str, Header()] = None):
        """Add an url to blocklist."""
        if not self.validate_domain(request.domain):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BLOCKLIST_IS_INVALID)
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        new_id, ok = self.blocklist_service.add_blocklist(user_id, request.domain, request.list_type)
        if not ok:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=BLOCKLIST_ALREADY_EXISTS)
        return EditBlockListResponse(user_id=user_id, domain=request.domain, list_type=request.list_type, status=ResponseStatus.SUCCESS, id=new_id)

    async def delete_blocklist(self, blocklist_id: str, x_auth_token: Annotated[str, Header()] = None):
        """Delete an url from blocklist."""
        if not ObjectId.is_valid(blocklist_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BLOCKLIST_ID_INVALID)
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        ok = self.blocklist_service.delete_blocklist(user_id, blocklist_id)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=BLOCKLIST_NOT_FOUND
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

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

    def validate_token(self, token: str) -> (str, bool):
        """Validate the token."""
        if token is None:
            return "", False
        user = self.user_service.decode_user(token)
        if user.user_id == "":
            return "", False
        now = datetime.datetime.timestamp(datetime.datetime.utcnow())
        if float(user.exp) < now:
            return "", False
        return user.user_id, True


class UserAPI(object):
    """class to encapsulate the user API endpoints."""

    def __init__(self, cfg: Config):
        self.router = APIRouter()
        self.user_service = UserService(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/user/login",
            endpoint=self.get_user_app_token,
            methods=["POST"],
            response_model=GetUserAppTokenResponse,
            summary="Get user app token",
        )

    async def get_user_app_token(self, request: GetUserAppTokenRequest):
        """Get user app token."""
        token = request.token
        if token is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_TOKEN)

        user = self.user_service.get_user_app_token(token)
        if user.jwt == "":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        return GetUserAppTokenResponse(jwt=user.jwt, email=user.email, picture=user.picture)


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
    user_api = UserAPI(cfg)
    _app.include_router(user_api.router, prefix=api_version)
    _app.include_router(analyticslist_api.router, prefix=api_version)
    return _app


app = create_app(Config())
