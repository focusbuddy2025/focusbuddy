#!/usr/bin/env python
# -*- encoding=utf8 -*-

import logging
import sys
from datetime import datetime

from pymongo import errors

from cron.config import Config
from cron.db import MongoDB

logging.basicConfig(stream=sys.stdout, level=logging.WARN)


class AnalyticsCron(object):
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = MongoDB().db

    # Get max session_id
    def _get_max_session_id(self):
        if self.db.session_counter.count_documents({}) == 0:
            return 0
        else:
            max_session_id = self.db.session_counter.find_one({})

        return max_session_id["session_id"]

    # Update max session_id
    def _update_max_session_id(self, session_id):
        query_filter = {"session_id": self._get_max_session_id()}
        update_operation = {"$set": {"session_id": session_id}}
        self.db.session_counter.update_one(query_filter, update_operation, upsert=True)

    # Function to reset the user analytics
    def reset_collection(self, period: str):
        active_users = self.db.users.find({})
        active_user_id = [user["user_id"] for user in active_users]

        for user_id in active_user_id:
            if period == "weekly":
                update_filter = {"user_id": user_id}
                update_operation = {"$set": {"weekly": 0}}
                update_response = self.db.analytics.update_one(
                    update_filter, update_operation
                )
                if update_response.acknowledged:
                    logging.info(f"weekly analytics for {user_id} reset successfully")
                else:
                    logging.error(f"unable to update weekly analytics for {user_id}")
            elif period == "daily":
                update_filter = {"user_id": user_id}
                update_operation = {"$set": {"daily": 0}}
                update_response = self.db.analytics.update_one(
                    update_filter, update_operation
                )
                if update_response.acknowledged:
                    logging.info(f"daily analytics for {user_id} reset successfully")
                else:
                    logging.error(f"unable to update weekly analytics for {user_id}")

    # Function to update the user analytics
    def update_collection(self):
        max_session_id = self._get_max_session_id()
        query_filter = {
            "$and": [
                {"session_status": 3},
                {"start_date": {"$eq": datetime.today().strftime("%Y-%m-%d")}},
                {"session_id": {"$gt": max_session_id}},
            ]
        }
        completed_sessions = self.db.focus_timer.find(query_filter)
        completed_sessions_summary = [
            {
                "user_id": session["user_id"],
                "duartion": session["duration"],
                "session_id": session["session_id"],
            }
            for session in completed_sessions
        ]
        for session_data in completed_sessions_summary:
            current_user_analytics = self.db.analytics.find_one(
                {"user_id": session_data["user_id"]}
            )
            if current_user_analytics is None:
                update_query_filter = {"user_id": session_data["user_id"]}
                update_operation_daily = {
                    "$set": {
                        "user_id": session_data["user_id"],
                        "daily": int(session_data["duartion"]),
                        "completed_sessions": int(1),
                    }
                }

                update_operation_weekly = {"$set": {"weekly": session_data["duartion"]}}
            else:
                update_query_filter = {"user_id": session_data["user_id"]}
                update_operation_daily = {
                    "$set": {
                        "daily": int(current_user_analytics["daily"])
                        + int(session_data["duartion"]),
                        "completed_sessions": int(
                            current_user_analytics["completed_sessions"]
                        )
                        + int(1),
                    }
                }

                update_operation_weekly = {
                    "$set": {
                        "weekly": int(current_user_analytics["weekly"])
                        + int(session_data["duartion"])
                    }
                }

            update_response_daily = self.db.analytics.update_one(
                update_query_filter, update_operation_daily, upsert=True
            )
            update_response_weekly = self.db.analytics.update_one(
                update_query_filter, update_operation_weekly, upsert=True
            )
            if update_response_daily.acknowledged:
                logging.info(
                    f"daily analytics record updated successfully for {session_data['user_id']}"
                )
            else:
                logging.error("could not update daily user stats")
                raise errors.WriteError(
                    error="daily_update_failed",
                    details="could not update daily user stats",
                )

            if update_response_weekly.acknowledged:
                logging.info(
                    f"weekly analytics record updated successfully for {session_data['user_id']}"
                )
                self._update_max_session_id(session_data["session_id"])
            else:
                logging.error("could not update weekly user stats")
                raise errors.WriteError(
                    error="daily_update_failed",
                    details="could not update daily user stats",
                )
            test_val = self.db.analytics.find_one({"user_id": session_data["user_id"]})
            logging.debug(f"updated value {test_val}")

        return
