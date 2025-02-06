#!/usr/bin/env python
# -*- encoding=utf8 -*-

import typer
from rich import print

from cron.cmd import reset_collection, update_collection

app = typer.Typer()


@app.command()
def reset_analytics(period: str = typer.Option(..., prompt=True)):
    print(f"[green] Resetting analytics for the {period}[/green]")
    reset_collection(period)


@app.command()
def update_analytics():
    print("[green] Updating analytics[/green]")
    update_collection()


if __name__ == "__main__":
    app()
