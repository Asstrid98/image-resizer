from app.celery_app import celery_app
from app.config import Config
from PIL import Image
import io
import base64
import os
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)


@celery_app.task(bind=True, max_retries=3)
def resize_image_task(self, job_id, image_data_b64, width, height, filename):
    """Redimensiona una imagen en segundo plano."""
    from app.app import create_app
    from app.models import db, ImageJob

    app = create_app(Config)

    with app.app_context():
        job = ImageJob.query.get(job_id)
        if not job:
            return {'error': 'Job not found'}

        try:
            job.status = 'processing'
            db.session.commit()

            image_data = base64.b64decode(image_data_b64)

            img = Image.open(io.BytesIO(image_data))
            img = img.resize((width, height), Image.LANCZOS)

            output_format = img.format if img.format else 'PNG'
            extension = output_format.lower()
            result_filename = f'resized_{job_id}.{extension}'
            result_path = os.path.join(RESULTS_DIR, result_filename)

            img.save(result_path, format=output_format)
            resized_size = os.path.getsize(result_path)

            job.status = 'completed'
            job.resized_size = resized_size
            job.completed_at = datetime.utcnow()
            db.session.commit()

            return {'job_id': job_id, 'status': 'completed'}

        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()
            return {'job_id': job_id, 'status': 'failed', 'error': str(e)}