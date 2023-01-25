#!/bin/sh
gunicorn --worker-class gevent --workers 2 --bind 0.0.0.0:5000 wsgi:app --max-requests 1000 --timeout 5 --keep-alive 5 --log-level debug