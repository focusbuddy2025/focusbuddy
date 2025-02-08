#!/usr/bin/env python
# -*- encoding=utf8 -*-

from crontab import CronTab

# Define schedule to run once a day
with CronTab(user="focusbuddy") as cron:
    job = cron.new(
        command="python3 -m cron.main reset-analytics --period daily /proc/1/fd/1 2>&1"
    )
    job.setall("0 0 * * *")
    cron.write()

# Define schedule to run once a week
with CronTab(user="focusbuddy") as cron:
    job = cron.new(
        command="python3 -m cron.main reset-analytics --period weekly /proc/1/fd/1 2>&1"
    )
    job.setall("0 0 * * SUN")
    cron.write()

# Define schedule to run every five mins
with CronTab(user="focusbuddy") as cron:
    job = cron.new(command="python3 -m cron.main update-analytics /proc/1/fd/1 2>&1")
    job.setall("*/5 * * * *")
    cron.write()
