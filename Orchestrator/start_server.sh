gunicorn --bind 0.0.0.0:8000 wsgi:app -w 2
