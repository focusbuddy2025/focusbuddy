#!/usr/bin/env python
# -*- encoding=utf8 -*-

import uvicorn

from src.config import Config

if __name__ == "__main__":
    cfg = Config()
    print(f"Starting server at {cfg.app_host}:{cfg.app_port}")
    uvicorn.run("rest:app", host=cfg.app_host, port=cfg.app_port, reload=True)
