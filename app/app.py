from flask import Flask, request, jsonify, send_file
from app.models import db, ImageJob
from app.config import Config
from PIL import Image
import io
from datetime import datetime

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route('/health/live', methods=['GET'])
    def liveness():
        return jsonify({'status': 'alive'}), 200

    @app.route('/health/ready', methods=['GET'])
    def readiness():
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'status': 'ready'}), 200
        except Exception as e:
            return jsonify({'status': 'not ready', 'error': str(e)}), 503

    @app.route('/resize', methods=['POST'])
    def resize_image():
        file = request.files.get('image')
        if not file or file.filename == '':
            return jsonify({'error': 'No image provided'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use: png, jpg, jpeg, gif, webp'}), 400

        # --- LÓGICA DE PRESETS Y ASPECT RATIO (RETO 1.1 Y 1.2) ---
        preset_name = request.form.get('preset')
        keep_ratio = request.form.get('keep_aspect_ratio', 'false').lower() == 'true'

        if preset_name:
            dimensions = app.config['SIZE_PRESETS'].get(preset_name)
            if not dimensions:
                return jsonify({'error': f'Invalid preset. Use: {list(app.config["SIZE_PRESETS"].keys())}'}), 400
            width, height = dimensions
        else:
            width = request.form.get('width', type=int)
            height = request.form.get('height', type=int)
            
            if not width or not height or width <= 0 or height <= 0:
                return jsonify({'error': 'Valid width and height (or a preset) are required'}), 400

        if width > 5000 or height > 5000:
            return jsonify({'error': 'Maximum dimension is 5000px'}), 400

        try:
            image_data = file.read()
            original_size = len(image_data)

            img = Image.open(io.BytesIO(image_data))
            img = img.convert('RGB') # Evita errores con PNGs transparentes al guardar en JPG

            # Aplicar redimensionado según el Reto 1.2
            if keep_ratio:
                img.thumbnail((width, height), Image.LANCZOS)
            else:
                img = img.resize((width, height), Image.LANCZOS)

            # Guardar resultado en buffer (Forzamos JPEG para máxima compatibilidad)
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            resized_size = buffer.tell()
            buffer.seek(0)

            # Guardar registro en la Base de Datos
            job = ImageJob(
                original_filename=file.filename,
                status='completed',
                width=img.width,   # Usamos el ancho final real
                height=img.height, # Usamos el alto final real
                original_size=original_size,
                resized_size=resized_size,
                completed_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()

            return send_file(
                buffer,
                mimetype='image/jpeg',
                as_attachment=True,
                download_name=f'resized_{file.filename}'
            )

        except Exception as e:
            db.session.rollback() # Limpia la sesión de DB si algo falla
            job = ImageJob(
                original_filename=file.filename,
                status='failed',
                width=0,
                height=0,
                original_size=len(image_data) if 'image_data' in locals() else 0,
                error_message=str(e),
                completed_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()
            return jsonify({'error': f'Failed to resize: {str(e)}'}), 500

    @app.route('/jobs', methods=['GET'])
    def list_jobs():
        jobs = ImageJob.query.order_by(ImageJob.created_at.desc()).limit(100).all()
        return jsonify([job.to_dict() for job in jobs]), 200

    @app.route('/jobs/<int:job_id>', methods=['GET'])
    def get_job(job_id):
        job = ImageJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        return jsonify(job.to_dict()), 200

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)