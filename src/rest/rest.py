#!/usr/bin/env python
# -*- encoding=utf8 -*-
import re
from typing import Annotated
import datetime

from bson import ObjectId

from fastapi import APIRouter, HTTPException, status
from fastapi import FastAPI, Header, APIRouter, HTTPException, status, Response

from fastapi.responses import JSONResponse

from src.api import ListBlockListResponse, EditBlockListResponse, ResponseStatus, AddBlockListRequest, GetUserAppTokenResponse, GetUserAppTokenRequest
from src.config import api_version, Config
from src.rest.error import BLOCKLIST_NOT_FOUND, BLOCKLIST_IS_INVALID, BLOCKLIST_ID_INVALID, BLOCKLIST_ALREADY_EXISTS, INVALID_TOKEN
from src.service import BlockListService
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

    async def list_blocklist(self, x_auth_token: Annotated[str, Header()] = None):
        """List all blocklist."""
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        response = self.blocklist_service.list_blocklist(user_id)
        return ListBlockListResponse(blocklist=response, status=ResponseStatus.SUCCESS)

    async def add_blocklist(self, user_id: str, request: AddBlockListRequest):
        """Add an url to blocklist."""
        if not self.validate_domain(request.domain):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BLOCKLIST_IS_INVALID)

        new_id, ok = self.blocklist_service.add_blocklist(user_id, request.domain, request.list_type)
        if not ok:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=BLOCKLIST_ALREADY_EXISTS)
        return EditBlockListResponse(user_id=user_id, domain=request.domain, list_type=request.list_type, status=ResponseStatus.SUCCESS, id=new_id)

    async def delete_blocklist(self, user_id: str, blocklist_id: str):
        """Delete an url from blocklist."""
        if not ObjectId.is_valid(blocklist_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BLOCKLIST_ID_INVALID)

        ok = self.blocklist_service.delete_blocklist(user_id, blocklist_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BLOCKLIST_NOT_FOUND)
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
        user = self.user_service.get_user(token)
        if user == {}:
            return "", False
        expired = user.get("exp", "")
        if expired == "":
            return "", False
        now = datetime.datetime.timestamp(datetime.datetime.utcnow())
        if float(expired) < now:
            return "", False
        return user["user_id"], True


class UserAPI(object):
    """class to encapsulate the user API endpoints."""

    def __init__(self, cfg: Config):
        self.router = APIRouter()
        self.user_service = UserService(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/user/token",
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

        app_token, picture, email = self.user_service.get_user_app_token(token)
        if app_token == "":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        return GetUserAppTokenResponse(jwt=app_token, email=email, picture=picture)


def create_app(cfg: Config):
    _app = FastAPI()
    blocklist_api = BlockListAPI(cfg)
    _app.include_router(blocklist_api.router, prefix=api_version)
    user_api = UserAPI(cfg)
    _app.include_router(user_api.router, prefix=api_version)
    return _app


app = create_app(Config())
