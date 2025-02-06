#!/usr/bin/env python
# -*- encoding=utf8 -*-

from datetime import datetime

from rich import print

from cron.db import MongoDB

db = MongoDB().db


# Get max session_id
def _get_max_session_id():
    if db.session_counter.count_documents({}) == 0:
        return 0
    else:
        max_session_id = db.session_counter.find_one({})

    return max_session_id["session_id"]


# Update max session_id
def _update_max_session_id(session_id):
    query_filter = {"session_id": _get_max_session_id()}
    update_operation = {"$set": {"session_id": session_id}}
    db.session_counter.update_one(query_filter, update_operation, upsert=True)


# Function to reset the user analytics
def reset_collection(period: str):
    active_users = db.users.find({})
    active_user_id = [user["user_id"] for user in active_users]

    for user_id in active_user_id:
        if period == "weekly":
            update_filter = {"user_id": user_id}
            update_operation = {"$set": {"weekly": 0}}
            update_response = db.analytics.update_one(update_filter, update_operation)
            print(update_response.modified_count)
        elif period == "daily":
            update_filter = {"user_id": user_id}
            update_operation = {"$set": {"daily": 0}}
            update_response = db.analytics.update_one(update_filter, update_operation)
            print(update_response.modified_count)


# Function to update the user analytics
def update_collection():
    max_session_id = _get_max_session_id()
    query_filter = {
        "$and": [
            {"session_status": 3},
            {"start_date": {"$eq": datetime.today().strftime("%Y-%m-%d")}},
            {"session_id": {"$gt": max_session_id}},
        ]
    }
    completed_sessions = db.focus_timer.find(query_filter)
    completed_sessions_summary = [
        {
            "user_id": session["user_id"],
            "duartion": session["duration"],
            "session_id": session["session_id"],
        }
        for session in completed_sessions
    ]
    for session_data in completed_sessions_summary:
        current_user_analytics = db.analytics.find_one(
            {"user_id": session_data["user_id"]}
        )
        if current_user_analytics is None:
            update_query_filter = {"user_id": session_data["user_id"]}
            update_operation_daily = {
                "$set": {
                    "user_id": session_data["user_id"],
                    "daily": session_data["duartion"],
                }
            }

            update_operation_weekly = {"$set": {"weekly": session_data["duartion"]}}
        else:
            update_query_filter = {"user_id": session_data["user_id"]}
            update_operation_daily = {
                "$set": {
                    "daily": current_user_analytics["daily"] + session_data["duartion"],
                }
            }

            update_operation_weekly = {
                "$set": {
                    "weekly": current_user_analytics["weekly"]
                    + session_data["duartion"]
                }
            }

        update_response_daily = db.analytics.update_one(
            update_query_filter, update_operation_daily, upsert=True
        )
        update_response_weekly = db.analytics.update_one(
            update_query_filter, update_operation_weekly, upsert=True
        )
        print(update_response_daily.modified_count)
        print(update_response_weekly.modified_count)
        _update_max_session_id(session_data["session_id"])
