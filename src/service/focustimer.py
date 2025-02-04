from datetime import datetime, timedelta
from src.config import Config
from src.api import SessionModel, SessionStatus, SessionType, ResponseStatus, SessionsResponse
from src.db import MongoDB
from fastapi import HTTPException


class FocusTimerService(object):
    """class to encapsulate the focus timer service."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = MongoDB().db

    def list_focus_sessions(self, user_id: str) -> SessionsResponse:
        """List all focus sessions for a user."""
        collection = self.db.get_collection("focus_sessions")
        query = {"user_id": user_id}
        focus_sessions_cursor = collection.find(query)
        focus_sessions = [
            SessionModel(**doc)
            for doc in focus_sessions_cursor
        ]
        return SessionsResponse(focus_sessions=focus_sessions, status=ResponseStatus.SUCCESS)

    def add_focus_session(self, session: SessionModel) -> SessionModel:
        """Add a new focus session."""
        # Step 1: Validate the session's time (no overlap and in the future)
        self._validate_session_time(session)

        # Step 2: Add the session to the database
        collection = self.db.get_collection("focus_sessions")
        session_data = session.dict()

        # Insert the session
        result = collection.insert_one(session_data)
        session.session_id = str(result.inserted_id)  # Set the session_id from the inserted document
        return session

    def delete_focus_session(self, session_id: str) -> dict:
        """Delete a focus session."""
        collection = self.db.get_collection("focus_sessions")
        query = {"session_id": session_id}
        result = collection.delete_one(query)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session deleted successfully"}

    def _validate_session_time(self, new_session: SessionModel):
        """Check if the new session overlaps with existing sessions or is in the past."""
        # Convert start_date and start_time to a single datetime object for comparison
        new_start_datetime = datetime.strptime(f"{new_session.start_date} {new_session.start_time}", "%Y-%m-%d %H:%M:%S")
        now = datetime.now()

        # Check if the new session starts in the past
        if new_start_datetime < now:
            raise HTTPException(status_code=400, detail="Session start time cannot be in the past.")

        # Calculate the end time of the new session
        new_end_datetime = new_start_datetime + timedelta(minutes=new_session.duration)

        # Check for overlap with existing sessions
        collection = self.db.get_collection("focus_sessions")
        existing_sessions_cursor = collection.find({"user_id": new_session.user_id})

        for existing_session in existing_sessions_cursor:
            existing_session = SessionModel(**existing_session)
            existing_start_datetime = datetime.strptime(f"{existing_session.start_date} {existing_session.start_time}", "%Y-%m-%d %H:%M:%S")
            existing_end_datetime = existing_start_datetime + timedelta(minutes=existing_session.duration)

            # Check if the new session overlaps with the existing session
            if (new_start_datetime < existing_end_datetime) and (new_end_datetime > existing_start_datetime):
                raise HTTPException(status_code=400, detail="The new session overlaps with an existing session.")
