#!/usr/bin/env python
# -*- encoding=utf8 -*-

from src.api import SessionStatus, SessionType
from src.config import Config
from src.db import MongoDB
from bson import ObjectId 


class FocusTimerService(object):
    """class to encapsulate the analytics service."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = MongoDB().db

    def add_focus_session(self, user_id: str, session_status: SessionStatus, start_date: str, start_time: str, duration: int, break_duration: int, session_type: SessionType, remaining_focus_time: int, remaining_break_time: int) -> (str, bool):
        """Add focus timer."""
        """TODO: If session conflict with upcoming sessions, return error."""
        collection = self.db.get_collection("focus_timer")

        query = {
            "user_id": user_id,
            "session_status": session_status,
            "start_date": start_date,
            "start_time": start_time,
            "duration": duration,
            "break_duration": break_duration,
            "session_type": session_type,
            "remaining_focus_time": remaining_focus_time,
            "remaining_break_time": remaining_break_time
        }
        update = {"$setOnInsert": query}
        result = collection.update_one(query, update, upsert=True)
        return str(result.upserted_id), True
    
    def modify_focus_session(self, user_id: str, session_id: str, **updates) -> bool:
        """Modify focus timer with optional fields."""
        collection = self.db.get_collection("focus_timer")

        if not updates:
            return False
        
        if "session_status" in updates:
            updates["session_status"] = updates["session_status"].value
        if "session_type" in updates:
            updates["session_type"] = updates["session_type"].value
        

        result = collection.update_one({"user_id": user_id, "_id": ObjectId(session_id)}, {"$set": updates})
        return result.modified_count > 0
    
    def delete_focus_session(self, user_id: str, session_id: str) -> bool:
        """Delete focus timer."""
        collection = self.db.get_collection("focus_timer")
        result = collection.delete_one({"user_id": user_id, "_id": ObjectId(session_id)})
        print(result)
        return result.deleted_count > 0


