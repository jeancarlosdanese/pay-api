#!/bin/bash

python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --reload --workers 1 --host 0.0.0.0 --port 8000 --log-level=debug
