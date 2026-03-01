#!/bin/bash
# Fall back to 3000 if $PORT is not set
PORT=${PORT:-3000}
uvicorn main:app --host 0.0.0.0 --port $PORT
