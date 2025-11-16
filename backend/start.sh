#!/bin/bash
# start script to run Gunicorn
export PYTHONUNBUFFERED=1
# try to run app via gunicorn
exec gunicorn --bind 0.0.0.0:5000 --workers 3 --threads 3 app:app
