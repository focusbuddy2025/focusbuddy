import base64
import io
import math
import smtplib
from collections import defaultdict
from datetime import datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

import matplotlib.pyplot as plt
from bson import ObjectId

from src.config import Config
from src.db import MongoDB


class NotificationService(object):
    """class to handle notification management"""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = MongoDB().db

    def get_notification(self, user_id: str):
        """List the user notification settings"""
        collection = self.db.get_collection("user")
        query_filter = {"_id": ObjectId(user_id)}
        user_data = collection.find_one(query_filter)
        result = user_data["notification"]
        return result

    def update_notification(self, user_id: str, notification_type: str, enabled: bool):
        """Update user notification status"""
        collection = self.db.get_collection("user")
        query_filter = {"_id": ObjectId(user_id)}
        print(user_id, notification_type, enabled)
        if notification_type == "browser":
            update_operation = {"$set": {"notification.browser": enabled}}
        elif notification_type == "email":
            update_operation = {"$set": {"notification.email_notification": enabled}}
        else:
            raise ValueError(f"Unrecognized notification type: {notification_type}")

        result = collection.update_one(query_filter, update_operation)
        return result.modified_count > 0

    def generate_stacked_bar_chart(self, day_data: dict) -> (str, str):
        """
        Generates a stacked bar chart from the provided data.
        day_data is a dict mapping day names to another dict of session types and durations.
        Returns a base64-encoded PNG and the day with the highest total duration.
        """
        if len(day_data) == 0:
            return "", ""
        # Define the expected order and labels
        week_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        session_labels = {0: "WORK", 1: "STUDY", 2: "PERSONAL", 3: "OTHER"}
        session_types = [0, 1, 2, 3]

        days = week_order

        # Prepare the data for each session type per day
        values = {stype: [] for stype in session_types}
        total_per_day = []
        for day in days:
            day_totals = day_data.get(day, {0: 0, 1: 0, 2: 0, 3: 0})
            day_sum = 0
            for stype in session_types:
                duration = day_totals.get(stype, 0)
                values[stype].append(duration)
                day_sum += duration
            total_per_day.append(day_sum)

        if all(total == 0 for total in total_per_day):
            max_day = days[0]
        else:
            max_day = days[total_per_day.index(max(total_per_day))]

        # Create the stacked bar chart
        fig, ax = plt.subplots(figsize=(8, 4))
        bar_width = 0.6
        indices = range(len(days))

        bottom = [0] * len(days)
        for stype in session_types:
            ax.bar(
                indices,
                values[stype],
                bar_width,
                bottom=bottom,
                label=session_labels[stype],
            )

            bottom = [b + v for b, v in zip(bottom, values[stype])]

        ax.set_xticks(indices)
        ax.set_xticklabels(days)
        ax.set_ylabel("Total Duration (minutes)")
        ax.set_title("Weekly Focus Sessions Summary")
        ax.legend()

        max_total = max(total_per_day) if total_per_day else 0
        ax.set_ylim([0, max_total * 1.2 if max_total > 0 else 1])

        # Save the figure to a buffer
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        return img_str, max_day

    def send_email(
        self, to_email: str, chart_b64: str, max_day: str, summary_text: str
    ):
        """
        Sends an email with the provided summary and stacked bar chart image embedded.
        SMTP settings are read from environment variables.
        """
        msg = MIMEMultipart("related")
        msg["Subject"] = "Your Weekly Focus Sessions Summary"
        msg["From"] = self.cfg.from_email
        msg["To"] = to_email

        # Create HTML body with an embedded image reference
        html = f"""
        <html>
        <body>
            <h2>Your Weekly Focus Sessions Summary</h2>
            <pre>{summary_text}</pre>
            <img src="cid:chart" alt="Stacked Bar Chart"/>
        </body>
        </html>
        """
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(html, "html"))

        # Attach the stacked bar chart image
        img_data = base64.b64decode(chart_b64)
        image = MIMEImage(img_data, name="chart.png")
        image.add_header("Content-ID", "<chart>")
        msg.attach(image)

        # Send email using SMTP with TLS
        with smtplib.SMTP(self.cfg.smtp_server, self.cfg.smtp_port) as server:
            server.starttls()
            server.login(self.cfg.smtp_username, self.cfg.smtp_password)
            server.sendmail(self.cfg.from_email, to_email, msg.as_string())

    def aggregate_weekly_summary(self):
        """
        Queries the database for users with email notifications enabled,
        aggregates their completed focus sessions over the past week into a summary,
        and returns a list of dictionaries containing the email, the base64-encoded
        stacked bar chart, the day with the highest focus, and summary text.
        """
        user_collection = self.db.get_collection("user")
        focus_collection = self.db.get_collection("focus_timer")
        today = datetime.now(ZoneInfo("America/Toronto"))
        last_week = today - timedelta(days=7)
        summaries = []

        # Find users with email notifications enabled.
        users = list(user_collection.find({"notification.email_notification": True}))
        for user in users:
            user_id = str(user["_id"])
            email = user["email"]

            # Query completed sessions for this user
            sessions = list(
                focus_collection.find({"user_id": user_id, "session_status": 3})
            )

            # Filter sessions within the past week
            sessions_in_week = []
            for s in sessions:
                try:
                    session_date = datetime.strptime(
                        s["start_date"], "%m/%d/%Y"
                    ).replace(tzinfo=ZoneInfo("America/Toronto"))
                    if last_week <= session_date <= today:
                        sessions_in_week.append(s)
                except Exception as e:
                    print(f"Error parsing date for session {s['_id']}: {e}")
                    continue

            if not sessions_in_week:
                continue

            # day_data maps day_name -> { session_type -> total duration }
            day_data = defaultdict(lambda: {0: 0, 1: 0, 2: 0, 3: 0})
            for s in sessions_in_week:
                try:
                    session_date = datetime.strptime(s["start_date"], "%m/%d/%Y")
                    day_name = session_date.strftime("%A")
                    stype = s.get("session_type", 3)
                    day_data[day_name][stype] += s.get("duration", 0) - (
                        math.floor(s.get("remaining_focus_time", 0) / 60)
                    )
                except Exception as e:
                    print(f"Error processing session {s['_id']}: {e}")
                    continue

            summary_lines = []
            for day, type_data in day_data.items():
                total = sum(type_data.values())
                summary_lines.append(
                    f"{day}: {total} minute(s)  [WORK: {type_data.get(0, 0)}, STUDY: {type_data.get(1, 0)}, PERSONAL: {type_data.get(2, 0)}, OTHER: {type_data.get(3, 0)}]"
                )
            summary_text = "\n".join(summary_lines)

            # Generate the stacked bar chart and determine the day with the highest focus.
            chart_b64, max_day = self.generate_stacked_bar_chart(day_data)

            summaries.append(
                {
                    "email": email,
                    "chart_b64": chart_b64,
                    "max_day": max_day,
                    "summary_text": summary_text,
                }
            )
        return summaries

    def weekly_summary_job(self):
        """
        This job aggregates weekly summaries and sends emails to users.
        """
        print("Running weekly summary job...")
        summaries = self.aggregate_weekly_summary()
        for summary in summaries:
            try:
                self.send_email(
                    summary["email"],
                    summary["chart_b64"],
                    summary["max_day"],
                    summary["summary_text"],
                )
                print(f"Email sent to {summary['email']}")
            except Exception as e:
                print(f"Failed to send email to {summary['email']}: {e}")
