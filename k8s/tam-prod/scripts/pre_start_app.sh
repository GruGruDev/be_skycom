#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# python /app/manage.py collectstatic --noinput
python /app/manage.py makemigrations
python /app/manage.py migrate
