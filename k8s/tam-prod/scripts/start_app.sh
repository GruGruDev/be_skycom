#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

/usr/local/bin/gunicorn core.asgi:application -k uvicorn.workers.UvicornWorker --threads ${UVICORN_NUMBER_THREADS:-3} --workers ${UVICORN_NUMBER_WORKER:-3} --bind 0.0.0.0:8000 --chdir=/app
