release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: gunicorn landuse_project.wsgi --bind 0.0.0.0:$PORT --workers 3 --timeout 120
