#/bin/sh
uvicorn odds.api.server:app --host 0.0.0.0 --port 8000
