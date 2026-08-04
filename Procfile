web: gunicorn config.wsgi:application
worker: celery -A config worker --loglevel=info --pool=solo
beat: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler