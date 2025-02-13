#!/usr/bin/env python
# -*- encoding=utf8 -*-

import sys
import debugpy

sys.path.append(".")

import uvicorn

from src.config import Config

if __name__ == "__main__":
    
    debugpy.listen(("0.0.0.0", 5678))  # Ensure it's listening
    print("Waiting for debugger to attach...")
    debugpy.wait_for_client()  # Optional: pauses execution until VS Code attaches

    cfg = Config()
    print(f"Starting server at {cfg.app_host}:{cfg.app_port}")
    uvicorn.run("rest:app", host=cfg.app_host, port=cfg.app_port, reload=True)
