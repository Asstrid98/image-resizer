from app.celery_app import celery_app
from app.config import Config
from app.storage import upload_image, ensure_bucket_exists
from PIL import Image
import io
import base64
from datetime import datetime


@celery_app.task(bind=True, max_retries=3)
def resize_image_task(self, job_id, image_data_b64, width, height, filename):
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

            ensure_bucket_exists()

            image_data = base64.b64decode(image_data_b64)

            original_key = f'originals/{job_id}_{filename}'
            upload_image(original_key, image_data)

            img = Image.open(io.BytesIO(image_data))
            img = img.resize((width, height), Image.LANCZOS)

            output_format = img.format if img.format else 'PNG'
            buffer = io.BytesIO()
            img.save(buffer, format=output_format)
            resized_data = buffer.getvalue()

            resized_key = f'resized/{job_id}_{filename}'
            upload_image(resized_key, resized_data)

            job.status = 'completed'
            job.resized_size = len(resized_data)
            job.completed_at = datetime.utcnow()
            db.session.commit()

            return {'job_id': job_id, 'status': 'completed'}

        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()
            return {'job_id': job_id, 'status': 'failed', 'error': str(e)}