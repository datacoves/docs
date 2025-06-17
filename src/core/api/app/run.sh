#!/bin/bash

if [ "$1" == "worker" ]; then

    queue="$2"
    echo "Starting in Worker Mode (queue $queue)"
    # FIXME: Added --without-mingle --without-gossip bec of an issue on celery/redis
    # https://github.com/celery/celery/discussions/7276
    WORKER=1 exec su abc -c "celery -A datacoves worker -Q $queue -l INFO -E --without-mingle --without-gossip"

elif [ "$1" == "worker-reload" ]; then

    queue="$2"
    echo "Starting in Worker Reload Mode (queue $queue)"
    exec ./manage.py runcelery "$queue"

elif [ "$1" == "beat" ]; then

    echo "Starting in Beat Mode"
    WORKER=1 exec su abc -c "celery -A datacoves beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler"

elif [ "$1" == "flower" ]; then

    echo "Starting in Flower Mode"
    exec celery -A datacoves flower --basic_auth=${FLOWER_USERNAME}:${FLOWER_PASSWORD}

elif [ "$1" == "local" ]; then

    echo "Starting in Local Mode"
    exec tail -f /dev/null

elif [ "$1" == "dev" ]; then

    echo "Starting in Dev Mode with user 'abc'"
    su abc -c "/usr/src/app/manage.py runserver 0:8000"

else

    echo "Starting in Web Server Mode"
    # FIXME: Move migration script to a k8s job if replicas need to be greater than 1
    python manage.py collectstatic --noinput && \
    # exec uwsgi --yaml ../uwsgi.yaml
    exec daphne -b 0.0.0.0 -p 8000 datacoves.asgi:application

fi
