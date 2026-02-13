from celery import Celery
import os


def make_celery():
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    celery = Celery(
        'image_resizer',
        broker=redis_url,
        backend=redis_url
    )

    celery.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )

    return celery


celery_app = make_celery()