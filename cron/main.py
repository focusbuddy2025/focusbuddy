#!/usr/bin/env python
# -*- encoding=utf8 -*-

import typer
from rich import print
from src.config import Config

from cron.cmd import AnalyticsCron

app = typer.Typer()
analytics_cron = AnalyticsCron(cfg=Config)


@app.command()
def reset_analytics(period: str = typer.Option(..., prompt=True)):
    print(f"[green] Resetting analytics for the {period}[/green]")
    analytics_cron.reset_collection(period)


@app.command()
def update_analytics():
    print("[green] Updating analytics[/green]")
    analytics_cron.update_collection()


if __name__ == "__main__":
    app()
