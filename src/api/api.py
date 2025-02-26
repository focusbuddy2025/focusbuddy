#!/usr/bin/env python
# -*- encoding=utf8 -*-

from enum import Enum, IntEnum
from typing import List, Optional

from pydantic import BaseModel, root_validator


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class BlockListType(IntEnum):
    WORK: int = 0
    STUDY: int = 1
    PERSONAL: int = 2
    OTHER: int = 3
    PERMANENT: int = 4


class UserStatus(IntEnum):
    WORK: int = 0
    STUDY: int = 1
    PERSONAL: int = 2
    OTHER: int = 3
    IDLE: int = 4


class SessionStatus(IntEnum):
    UPCOMING: int = 0
    ONGOING: int = 1
    PAUSED: int = 2
    COMPLETED: int = 3


class SessionType(IntEnum):
    WORK: int = 0
    STUDY: int = 1
    PERSONAL: int = 2
    OTHER: int = 3


class BlockListModel(BaseModel):
    domain: str
    list_type: BlockListType


class BlockListResponse(BaseModel):
    id: str
    domain: str
    list_type: BlockListType


class ListBlockListResponse(BaseModel):
    blocklist: List[BlockListResponse]
    status: ResponseStatus = ResponseStatus.SUCCESS


class EditBlockListResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    user_id: str
    domain: str
    list_type: BlockListType
    id: str


class AddBlockListRequest(BaseModel):
    domain: str
    list_type: BlockListType


class GetUserAppTokenResponse(BaseModel):
    jwt: str
    email: str
    picture: str


class GetUserAppTokenRequest(BaseModel):
    token: str


class UpdateUserStatusRequest(BaseModel):
    user_status: UserStatus


class UpdateUserStatusResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    user_id: str
    user_status: UserStatus


class AnalyticsListResponse(BaseModel):
    daily: float = 0
    weekly: float = 0
    completed_sessions: int = 0
    status: ResponseStatus = ResponseStatus.SUCCESS


class AnalyticsWeeklySummaryResponse(BaseModel):
    duration: float = 0
    user_id: str
    session_type: SessionType


class ListAnalyticsWeeklySummaryResponse(BaseModel):
    summary: List[AnalyticsWeeklySummaryResponse]
    status: ResponseStatus = ResponseStatus.SUCCESS


class FocusSessionModel(BaseModel):
    session_status: Optional[SessionStatus] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    duration: Optional[int] = None
    break_duration: Optional[int] = None
    session_type: Optional[SessionType] = None
    remaining_focus_time: Optional[int] = None
    remaining_break_time: Optional[int] = None


class GetFocusSessionResponse(BaseModel):
    session_id: Optional[str] = None
    session_status: Optional[SessionStatus] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    duration: Optional[int] = None
    break_duration: Optional[int] = None
    session_type: Optional[SessionType] = None
    remaining_focus_time: Optional[int] = None
    remaining_break_time: Optional[int] = None

    @root_validator(pre=True)
    def set_session_id(cls, values):
        # If _id exists, map it to session_id
        if "_id" in values:
            values["session_id"] = str(
                values["_id"]
            )  # MongoDB's _id is an ObjectId, so we convert it to string
            del values["_id"]  # Remove the original _id field
        return values


class EditFocusSessionResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    user_id: str
    id: str


class GetNextFocusSessionResponse(BaseModel):
    focus_session: Optional[GetFocusSessionResponse] = None
    status: ResponseStatus = ResponseStatus.SUCCESS


class GetAllFocusSessionResponse(BaseModel):
    focus_sessions: list[GetFocusSessionResponse]
    status: ResponseStatus = ResponseStatus.SUCCESS
