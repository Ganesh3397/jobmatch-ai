#!/bin/sh
# Runs on every deploy / restart (Render, Railway, any Docker host)
set -e
python manage.py migrate --noinput
python manage.py seed_demo --if-empty      # demo data only the FIRST time (never wipes real users)
exec gunicorn config.wsgi:application \
     --bind 0.0.0.0:${PORT:-8000} \
     --workers ${WEB_CONCURRENCY:-2} --threads 4 --timeout 120
