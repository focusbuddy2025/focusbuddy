#!/usr/bin/env python
# -*- encoding=utf8 -*-

from fastapi import FastAPI, APIRouter

from src.api import ListBlockListResponse, BlockListType, SessionsResponse, SessionModel, ResponseStatus, SessionStatus, SessionType
from src.service import BlockListService, FocusTimerService
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
    

class FocusTimerAPI(object):
    """class to encapsulate the FocusTimer API endpoints."""

    def __init__(self, cfg: Config):
        self.router = APIRouter()
        self.focus_timer_service = FocusTimerService(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/focusSessions/{user_id}",
            endpoint=self.list_sessions,
            methods=["GET"],
            response_model=SessionsResponse,
            summary="List all focus sessions",
        )
        self.router.add_api_route(
            path="/focusSessions",
            endpoint=self.add_session,
            methods=["POST"],
            response_model=SessionModel,
            summary="Add a new focus session",
        )
        self.router.add_api_route(
            path="/focusSessions/{session_id}",
            endpoint=self.delete_focus_session,
            methods=["DELETE"],
            summary="Delete a focus session",
        )

    async def list_sessions(self, user_id: str):
        """List all focus sessions for a user."""
        return self.focus_timer_service.list_focus_sessions(user_id)

    async def add_session(self, session: SessionModel):
        """Add a new focus session."""
        return self.focus_timer_service.add_focus_session(session)

    async def delete_session(self, session_id: str):
        """Delete a focus session."""
        return self.focus_timer_service.delete_focus_session(session_id)


def create_app(cfg: Config):
    _app = FastAPI()
    blocklist_api = BlockListAPI(cfg)
    focus_timer_api = FocusTimerAPI(cfg)
    _app.include_router(blocklist_api.router, prefix=api_version)
    _app.include_router(focus_timer_api.router, prefix=api_version)
    return _app

app = create_app(Config())
