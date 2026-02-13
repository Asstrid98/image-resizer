# 🖼️ Proyecto: Image Resizer — Documento 1, Parte A

## Tu Misión DevOps

Vas a construir un servicio de redimensionado de imágenes y desplegarlo en OpenShift. Los usuarios suben una imagen, eligen el tamaño que quieren, y el sistema la procesa en segundo plano y les da el resultado.

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│    TU CONSTRUYES ESTO:                                         │
│                                                                │
│    Usuario                                                     │
│       │                                                        │
│       │  POST /resize                                          │
│       │  (imagen + tamaño deseado)                             │
│       ▼                                                        │
│    ┌─────────────────┐     ┌──────────┐     ┌──────────────┐   │
│    │   API Flask     │────▶│  Redis   │────▶│   Worker     │   │
│    │  (recibe img)   │     │  (cola)  │     │  (Celery)    │   │
│    └────────┬────────┘     └──────────┘     └──────┬───────┘   │
│             │                                      │           │
│             │    ┌──────────────┐                   │           │
│             └───▶│    MinIO     │◀──────────────────┘           │
│                  │ (almacén S3) │                               │
│                  └──────┬───────┘                               │
│                         │                                      │
│                         ▼                                      │
│    Usuario descarga su imagen redimensionada                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🆚 ¿Qué tiene esto de nuevo respecto al URL Shortener?

| Concepto | URL Shortener | Image Resizer |
|----------|---------------|---------------|
| Arquitectura | 1 servicio + BD | 4 servicios que se comunican |
| Procesamiento | Síncrono (inmediato) | Asíncrono (colas + workers) |
| Almacenamiento | Solo texto en PostgreSQL | Archivos binarios en MinIO/S3 |
| Workers | Ninguno | Celery procesando tareas |
| Cola de mensajes | Ninguna | Redis |
| Secrets | Plaintext en YAML | Sealed Secrets (encriptados) |

---

## 🎯 Lo que vas a practicar

| Componente | Skill | ¿Nuevo? |
|------------|-------|---------|
| API Python (Flask) | Desarrollo | Ya lo conoces |
| Celery Workers | Procesamiento asíncrono | 🆕 |
| Redis | Cola de mensajes | 🆕 |
| MinIO | Almacenamiento S3-compatible | 🆕 |
| PostgreSQL | Base de datos | Ya lo conoces |
| Dockerfile multi-stage | Containerización | Ya lo conoces |
| Deployments múltiples | Kubernetes | 🆕 Más complejo |
| Sealed Secrets | Seguridad | 🆕 |
| Helm Chart | Parametrización | Ya lo conoces |
| GitHub Actions | CI/CD | Ya lo conoces |

---

## 📋 Arquitectura Final

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OPENSHIFT SANDBOX                                │
│                                                                         │
│   Namespace: taylinn-dev                                                │
│   ┌─────────────────────────────────────────────────────────────┐       │
│   │                                                             │       │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │       │
│   │  │  Deployment  │  │  Deployment  │  │  Deployment  │      │       │
│   │  │  api-flask   │  │   worker     │  │  postgresql  │      │       │
│   │  │              │  │  (celery)    │  │              │      │       │
│   │  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │      │       │
│   │  │  │  Pod   │  │  │  │  Pod   │  │  │  │  Pod   │  │      │       │
│   │  │  │ :5000  │  │  │  │        │  │  │  │ :5432  │  │      │       │
│   │  │  └────────┘  │  │  └────────┘  │  │  └────────┘  │      │       │
│   │  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │       │
│   │         │                 │                                 │       │
│   │         │        ┌───────┴────────┐                         │       │
│   │         ▼        ▼                ▼                         │       │
│   │  ┌──────────────┐  ┌──────────────┐                         │       │
│   │  │  Deployment  │  │  Deployment  │                         │       │
│   │  │    Redis     │  │    MinIO     │                         │       │
│   │  │   (cola)     │  │  (almacén)   │                         │       │
│   │  │  ┌────────┐  │  │  ┌────────┐  │                         │       │
│   │  │  │  Pod   │  │  │  │  Pod   │  │                         │       │
│   │  │  │ :6379  │  │  │  │ :9000  │  │                         │       │
│   │  │  └────────┘  │  │  └────────┘  │                         │       │
│   │  └──────────────┘  └──────────────┘                         │       │
│   │                                                             │       │
│   │  ┌──────────────┐                                           │       │
│   │  │ Service      │                                           │       │
│   │  │  + Route     │                                           │       │
│   │  └──────┬───────┘                                           │       │
│   └─────────┼───────────────────────────────────────────────────┘       │
│             ▼                                                           │
└──── 🌐 https://image-resizer-taylinn-dev.apps.sandbox-xxx... ──────────┘
```

---

## 📁 Estructura Final del Proyecto

```
image-resizer/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── app/
│   ├── __init__.py
│   ├── app.py                  # API Flask
│   ├── models.py               # Modelos de BD
│   ├── config.py               # Configuración
│   ├── tasks.py                # Tareas Celery (resize)
│   ├── celery_app.py           # Configuración de Celery
│   └── storage.py              # Conexión con MinIO/S3
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_app.py
├── k8s/
│   ├── api-deployment.yaml
│   ├── worker-deployment.yaml
│   ├── redis.yaml
│   ├── minio.yaml
│   ├── postgresql.yaml
│   ├── service.yaml
│   ├── route.yaml
│   ├── configmap.yaml
│   └── secret.yaml
├── helm/
│   └── image-resizer/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-dev.yaml
│       └── templates/
│           ├── _helpers.tpl
│           ├── api-deployment.yaml
│           ├── worker-deployment.yaml
│           ├── redis.yaml
│           ├── minio.yaml
│           ├── postgresql.yaml
│           ├── service.yaml
│           ├── route.yaml
│           ├── configmap.yaml
│           └── secret.yaml
├── Dockerfile
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🗺️ Mapa de Fases

```
FASE 0        FASE 1       FASE 2       FASE 3       FASE 4
Setup         API          Tests        Async        MinIO
┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐
│ ENV │─────▶│Flask│─────▶│Pytest│─────▶│Redis│─────▶│ S3  │
│     │      │ App │      │     │      │Celry│      │store│
└─────┘      └─────┘      └─────┘      └─────┘      └─────┘
                                                        │
┌───────────────────────────────────────────────────────┘
│
▼
FASE 5       FASE 6       FASE 7       FASE 8       FASE 9
Docker       K8s          Sealed       Helm         CI/CD
┌─────┐      ┌─────┐      Secrets      ┌─────┐      ┌─────┐
│Image│─────▶│YAML │─────▶┌─────┐─────▶│Chart│─────▶│ 🚀  │
│     │      │     │      │ 🔒  │      │     │      │LIVE!│
└─────┘      └─────┘      └─────┘      └─────┘      └─────┘
```

---

# 🚀 FASES DEL PROYECTO

---

## Fase 0: Setup del Entorno

### 🎯 Objetivo
Configurar todo lo necesario. Si ya tienes Python, OpenShift CLI, Helm y los secrets de GitHub del proyecto anterior, solo verifica que siguen funcionando.

### 📝 Tareas

#### 0.1 Verifica tu entorno existente

```bash
python --version       # Python 3.11.x o 3.12.x
oc whoami              # tu-usuario (si da error, renueva el token)
helm version           # versión 3.x
git --version          # cualquier versión reciente
```

#### 0.1bis Crea y activa un entorno virtual (recomendado en macOS)

En macOS con Python instalado via Homebrew, `pip` puede estar bloqueado por PEP 668 si intentas instalar a nivel sistema. Para evitarlo, usa siempre un venv:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

A partir de aquí, cuando el documento diga `python -m pip ...`, hazlo dentro del venv (verás `(.venv)` al inicio del prompt).

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ⚠️  Si el token de OpenShift expiró:                      │
│                                                             │
│   1. Ve a la consola web de OpenShift                       │
│   2. Tu nombre → "Copy login command" → Display Token       │
│   3. Copia y pega el comando oc login en tu terminal        │
│   4. Actualiza el secret OPENSHIFT_TOKEN en GitHub          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 0.2 Crea el repositorio

1. Crea un nuevo repo en GitHub llamado `image-resizer`
2. Clónalo en tu máquina:
   ```bash
   git clone https://github.com/TU-USUARIO/image-resizer.git
   cd image-resizer
   ```
3. Crea la estructura de carpetas:
   ```bash
   mkdir -p app tests k8s helm/image-resizer/templates .github/workflows
   ```

#### 0.3 Configura los Secrets en GitHub

Ve a tu repositorio → Settings → Secrets and variables → Actions:

| Secret Name | Valor |
|-------------|-------|
| `OPENSHIFT_SERVER` | URL de tu servidor OpenShift |
| `OPENSHIFT_TOKEN` | Tu token de OpenShift |

### ✅ Checkpoint

Todos los comandos de 0.1 funcionan y tienes el repo clonado. Siguiente fase.

---

## Fase 1: API Flask Básica (Síncrona)

### 🎯 Objetivo
Crear una API que reciba una imagen y la devuelva redimensionada. Todo síncrono, sin colas ni workers todavía. Lo importante es que **funcione y puedas ver el resultado**.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 EN ESTA FASE: Todo es síncrono y en memoria            │
│                                                             │
│   Subes imagen → API la procesa → Te devuelve la imagen     │
│                                                             │
│   No hay Redis, no hay Celery, no hay MinIO todavía.        │
│   Paso a paso. Primero que funcione, luego lo mejoramos.    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📝 Tareas

#### 1.1 Crea `requirements.txt`

```txt
flask==3.0.0
flask-sqlalchemy==3.1.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
gunicorn==21.2.0
Pillow==10.2.0
pytest==7.4.3
pytest-flask==1.3.0
```

> 💡 **Pillow** es la librería de Python para manipular imágenes. Es la novedad aquí.

Instala las dependencias:
```bash
# Si no estás en un venv, actívalo primero (ver Fase 0.1bis)
python -m pip install -r requirements.txt
```

> ⚠️ Si `psycopg2-binary` da error en Windows, ignóralo. Solo se necesita para PostgreSQL en OpenShift. Local usamos SQLite.

#### 1.2 Crea `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/

# SQLite
*.db

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# OS
.DS_Store
Thumbs.db

# Uploads temporales
uploads/
results/
```

#### 1.3 Crea `app/config.py`

Este archivo lo conoces del URL Shortener. Tiene la configuración de la app.

**Tu tarea:** Crea `app/config.py` con una clase `Config` que tenga:
- `SQLALCHEMY_DATABASE_URI`: lee de la variable de entorno `DATABASE_URL`, por defecto SQLite
- `SQLALCHEMY_TRACK_MODIFICATIONS`: False
- `BASE_URL`: lee de variable de entorno, por defecto `http://localhost:5000`
- `MAX_CONTENT_LENGTH`: `10 * 1024 * 1024` (limita uploads a 10MB)
- `ALLOWED_EXTENSIONS`: un set con `{'png', 'jpg', 'jpeg', 'gif', 'webp'}`

<details>
<summary>💡 Pista</summary>

```python
import os

class Config:
    # Es igual que URL Shortener, pero con dos campos nuevos
    # MAX_CONTENT_LENGTH y ALLOWED_EXTENSIONS
    pass
```
</details>

<details>
<summary>🔑 Solución</summary>

```python
import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///image_resizer.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
```
</details>

#### 1.4 Crea `app/models.py`

**Tu tarea:** Crea el modelo `ImageJob` con estos campos:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer, primary key | ID único |
| `original_filename` | String(255), not null | Nombre del archivo original |
| `status` | String(20), default 'pending' | pending / processing / completed / failed |
| `width` | Integer, not null | Ancho deseado |
| `height` | Integer, not null | Alto deseado |
| `original_size` | Integer | Tamaño original en bytes |
| `resized_size` | Integer, nullable | Tamaño resultado en bytes |
| `created_at` | DateTime, default utcnow | Fecha de creación |
| `completed_at` | DateTime, nullable | Fecha de completado |
| `error_message` | String(500), nullable | Mensaje de error si falló |

También necesita un método `to_dict()` y `__tablename__ = 'image_jobs'`.

<details>
<summary>💡 Pista</summary>

Es muy similar al modelo `URL` del URL Shortener. La diferencia es que tiene más campos y un campo `status`.

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ImageJob(db.Model):
    __tablename__ = 'image_jobs'
    # Define los campos de la tabla de arriba...
    # Luego el método to_dict()
```
</details>

<details>
<summary>🔑 Solución</summary>

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class ImageJob(db.Model):
    __tablename__ = 'image_jobs'

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending')
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    original_size = db.Column(db.Integer)
    resized_size = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'status': self.status,
            'width': self.width,
            'height': self.height,
            'original_size': self.original_size,
            'resized_size': self.resized_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }
```
</details>

#### 1.5 Crea `app/app.py`

Tu API necesita estos endpoints:

| Método | Ruta | Qué hace |
|--------|------|----------|
| GET | `/health/live` | Devuelve `{"status": "alive"}` |
| GET | `/health/ready` | Comprueba la BD |
| POST | `/resize` | Recibe imagen + dimensiones, la redimensiona, la devuelve |
| GET | `/jobs` | Lista todos los jobs |
| GET | `/jobs/<id>` | Info de un job específico |

**El endpoint POST /resize debe:**

1. Recibir un archivo (imagen) vía `multipart/form-data`
2. Recibir `width` y `height` como campos del form
3. Validar que el archivo existe y tiene extensión permitida
4. Validar que width y height son números positivos (máximo 5000)
5. Redimensionar la imagen con Pillow
6. Guardar un registro en la BD con status `completed`
7. Devolver la imagen redimensionada como descarga

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 CONCEPTOS CLAVE PARA ESTA FASE                         │
│                                                             │
│   Recibir archivos en Flask:                                │
│     file = request.files.get('image')                       │
│     width = request.form.get('width', type=int)             │
│                                                             │
│   Redimensionar con Pillow:                                 │
│     from PIL import Image                                   │
│     import io                                               │
│     img = Image.open(io.BytesIO(file_bytes))                │
│     img = img.resize((width, height), Image.LANCZOS)        │
│     buffer = io.BytesIO()                                   │
│     img.save(buffer, format='PNG')                          │
│                                                             │
│   Devolver un archivo en Flask:                             │
│     from flask import send_file                             │
│     buffer.seek(0)                                          │
│     return send_file(buffer, mimetype='image/png')          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

<details>
<summary>💡 Pista 1: estructura general</summary>

```python
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

    # Health endpoints (ya sabes cómo son del URL Shortener)

    # POST /resize (lo nuevo)

    # GET /jobs y GET /jobs/<id> (parecido a /urls del URL Shortener)

    return app
```
</details>

<details>
<summary>💡 Pista 2: helper para validar extensión</summary>

```python
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
```
</details>

<details>
<summary>💡 Pista 3: el endpoint /resize paso a paso</summary>

```python
@app.route('/resize', methods=['POST'])
def resize_image():
    # 1. Validar que hay un archivo
    file = request.files.get('image')
    if not file or file.filename == '':
        return jsonify({'error': '...'}), 400

    # 2. Validar extensión

    # 3. Leer width y height del form

    # 4. Leer la imagen con file.read()

    # 5. Redimensionar con Pillow

    # 6. Guardar job en BD con status='completed'

    # 7. Devolver imagen con send_file
```
</details>

<details>
<summary>🔑 Solución</summary>

```python
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

        width = request.form.get('width', type=int)
        height = request.form.get('height', type=int)
        if not width or not height or width <= 0 or height <= 0:
            return jsonify({'error': 'Valid width and height are required'}), 400

        if width > 5000 or height > 5000:
            return jsonify({'error': 'Maximum dimension is 5000px'}), 400

        try:
            image_data = file.read()
            original_size = len(image_data)

            img = Image.open(io.BytesIO(image_data))
            img = img.resize((width, height), Image.LANCZOS)

            buffer = io.BytesIO()
            output_format = img.format if img.format else 'PNG'
            img.save(buffer, format=output_format)
            resized_size = buffer.tell()
            buffer.seek(0)

            job = ImageJob(
                original_filename=file.filename,
                status='completed',
                width=width,
                height=height,
                original_size=original_size,
                resized_size=resized_size,
                completed_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()

            mimetype = f'image/{output_format.lower()}'
            return send_file(
                buffer,
                mimetype=mimetype,
                as_attachment=True,
                download_name=f'resized_{file.filename}'
            )

        except Exception as e:
            job = ImageJob(
                original_filename=file.filename,
                status='failed',
                width=width,
                height=height,
                original_size=len(image_data) if 'image_data' in dir() else 0,
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
```
</details>

#### 1.6 Crea `app/__init__.py`

```python
from app.app import create_app, app
from app.models import db, ImageJob

__all__ = ['create_app', 'app', 'db', 'ImageJob']
```

### ✅ Checkpoint de Validación

1. **Arranca la app:**
   ```bash
   python -m app.app
   ```
   Debes ver: `* Running on http://127.0.0.1:5000`

2. **Prueba el health check:**
   ```bash
   curl http://localhost:5000/health/live
   # {"status": "alive"}
   ```

3. **Prueba el resize** (necesitas una imagen cualquiera):

   Si no tienes una imagen a mano, crea una con Python:
   ```bash
   python -c "from PIL import Image; Image.new('RGB', (800, 600), 'blue').save('test.jpg')"
   ```

   Luego:
   ```bash
   curl -i -H "Expect:" -X POST http://localhost:5000/resize \
     -F "image=@test.jpg" \
     -F "width=200" \
     -F "height=200" \
     --output resized.jpg
   ```
   Abre `resized.jpg`. Debe ser tu imagen a 200x200.

4. **Prueba los jobs:**
   ```bash
   curl http://localhost:5000/jobs
   # Debe mostrar el job con status "completed"
   ```

<details>
<summary>💡 Hint: curl con -F no funciona en mi terminal</summary>

**PowerShell alternativa:**
```powershell
$form = @{
    image = Get-Item -Path "test.jpg"
    width = "200"
    height = "200"
}
Invoke-RestMethod -Uri "http://localhost:5000/resize" -Method Post -Form $form -OutFile "resized.jpg"
```

**O usa Postman/Insomnia** con un POST a `http://localhost:5000/resize`, body tipo form-data.
</details>

### 🧩 Retos de la Fase 1

<details>
<summary>🎯 Reto 1.1: Añadir presets de tamaño</summary>

**Problema:** Los usuarios no siempre saben qué dimensiones quieren.

**Tu tarea:** Modifica `/resize` para que acepte un campo opcional `preset`:
- `thumbnail`: 150x150
- `medium`: 800x600
- `large`: 1920x1080

Si se envía `preset`, ignora `width` y `height`.

**Verificación:**
```bash
curl -X POST http://localhost:5000/resize \
  -F "image=@test.jpg" \
  -F "preset=thumbnail" \
  --output thumb.jpg
```
</details>

<details>
<summary>🎯 Reto 1.2: Mantener proporción (aspect ratio)</summary>

**Problema:** Si la imagen es 1600x900 y pides 200x200, se deforma.

**Tu tarea:** Añade un campo opcional `keep_aspect_ratio`. Si es `true`, no deforma la imagen.

**Pista:** `Image.thumbnail((width, height))` de Pillow hace exactamente esto.
</details>

---

## Fase 2: Tests

### 🎯 Objetivo
Crear tests para tu API. Ya sabes cómo funciona pytest del proyecto anterior.

### 📝 Tareas

#### 2.1 Crea `tests/__init__.py`
```python
# Empty file
```

#### 2.2 Crea `tests/conftest.py`

**Tu tarea:** Crea el conftest.py con:
- `TestConfig`: SQLite en memoria, `TESTING = True`, y las mismas `ALLOWED_EXTENSIONS`
- Fixture `app`: crea la app con config de test
- Fixture `client`: devuelve el test client
- Fixture `sample_image`: crea una imagen PNG de prueba en memoria

<details>
<summary>💡 Pista: el fixture sample_image</summary>

```python
@pytest.fixture
def sample_image():
    """Crea una imagen de prueba en memoria."""
    from PIL import Image
    img = Image.new('RGB', (800, 600), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer
```
</details>

<details>
<summary>🔑 Solución</summary>

```python
import pytest
import io
from PIL import Image
from app.app import create_app
from app.models import db


class TestConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    BASE_URL = 'http://localhost:5000'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_image():
    img = Image.new('RGB', (800, 600), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer
```
</details>

#### 2.3 Crea `tests/test_app.py`

**Tu tarea:** Escribe tests para al menos estos escenarios:

1. `test_health_live` - devuelve 200
2. `test_health_ready` - devuelve 200
3. `test_resize_success` - resize funciona con imagen válida
4. `test_resize_no_image` - error 400 sin imagen
5. `test_resize_invalid_extension` - error 400 con archivo .txt
6. `test_resize_missing_dimensions` - error 400 sin width/height
7. `test_resize_negative_dimensions` - error 400 con dimensiones negativas
8. `test_list_jobs` - listar jobs funciona
9. `test_get_job` - obtener un job específico funciona
10. `test_get_job_not_found` - 404 para job que no existe

<details>
<summary>💡 Pista: cómo enviar un archivo en un test de Flask</summary>

```python
def test_resize_success(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '200',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 200
```
</details>

<details>
<summary>🔑 Solución</summary>

```python
from io import BytesIO


def test_health_live(client):
    response = client.get('/health/live')
    assert response.status_code == 200
    assert response.json['status'] == 'alive'


def test_health_ready(client):
    response = client.get('/health/ready')
    assert response.status_code == 200
    assert response.json['status'] == 'ready'


def test_resize_success(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '200',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 200
    assert response.content_type.startswith('image/')


def test_resize_no_image(client):
    data = {'width': '200', 'height': '200'}
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400
    assert 'error' in response.json


def test_resize_invalid_extension(client):
    data = {
        'image': (BytesIO(b'not an image'), 'test.txt'),
        'width': '200',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_missing_dimensions(client, sample_image):
    data = {'image': (sample_image, 'test.png')}
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_negative_dimensions(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '-100',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_too_large(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '10000',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_list_jobs_empty(client):
    response = client.get('/jobs')
    assert response.status_code == 200
    assert response.json == []


def test_list_jobs_after_resize(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '100',
        'height': '100'
    }
    client.post('/resize', data=data, content_type='multipart/form-data')
    response = client.get('/jobs')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['status'] == 'completed'


def test_get_job(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '100',
        'height': '100'
    }
    client.post('/resize', data=data, content_type='multipart/form-data')
    response = client.get('/jobs/1')
    assert response.status_code == 200
    assert response.json['original_filename'] == 'test.png'
    assert response.json['width'] == 100


def test_get_job_not_found(client):
    response = client.get('/jobs/999')
    assert response.status_code == 404
```
</details>

### ✅ Checkpoint

```bash
pytest tests/ -v
# Todos deben pasar en verde ✅
```

---

## Fase 3: Procesamiento Asíncrono (Redis + Celery)

### 🎯 Objetivo
Convertir el procesamiento síncrono en asíncrono. La API recibe la imagen, la encola, y un worker la procesa por separado.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 ¿POR QUÉ ASÍNCRONO?                                    │
│                                                             │
│   Imagina que alguien sube una imagen de 10MB.              │
│   Si es síncrono, la API se queda bloqueada procesándola    │
│   y no puede atender a otros usuarios.                      │
│                                                             │
│   Con Celery + Redis:                                       │
│   1. La API recibe la imagen y dice "recibido, tu job es #5"│
│   2. Mete la tarea en Redis (cola)                          │
│   3. La API ya está libre para atender a más gente          │
│   4. El worker coge la tarea de Redis y la procesa          │
│   5. El usuario consulta /jobs/5 para ver si ya está lista  │
│                                                             │
│   Es como una pizzería:                                     │
│   - El camarero (API) recibe el pedido                      │
│   - Lo pasa a la cocina (Redis)                             │
│   - El cocinero (Worker) lo prepara                         │
│   - El camarero atiende más mesas mientras tanto            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📝 Conceptos Nuevos

```
┌───────────┐    encola    ┌───────────┐    procesa    ┌───────────┐
│   Flask   │ ──────────▶  │   Redis   │  ──────────▶  │  Celery   │
│   (API)   │              │  (broker) │               │ (worker)  │
└───────────┘              └───────────┘               └───────────┘
      │                                                       │
      │  Responde inmediatamente:                             │
      │  {"job_id": 5, "status": "pending"}                   │
      │                                                       │
      │                            Actualiza BD cuando acaba: │
      │                            status = "completed"       │
      └───────────────────────────────────────────────────────┘
```

### 📝 Tareas

#### 3.1 Instala Redis en tu máquina (para desarrollo local)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   WINDOWS                                                   │
│                                                             │
│   Opción 1 (recomendada): Memurai                           │
│   Redis para Windows. Descarga de:                          │
│   https://www.memurai.com/get-memurai                       │
│   Instala y arranca en puerto 6379 automáticamente.         │
│                                                             │
│   Opción 2: Docker Desktop                                  │
│   docker run -d -p 6379:6379 --name redis redis:7-alpine    │
│                                                             │
│   Opción 3: Sin Redis local                                 │
│   Los tests no necesitan Redis (se mockea Celery).          │
│   El flujo completo se prueba en OpenShift.                 │
│                                                             │
│   MAC                                                       │
│   brew install redis && brew services start redis           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Verificar: `redis-cli ping` → debe devolver `PONG`

#### 3.2 Actualiza `requirements.txt`

Añade al final:
```txt
celery==5.3.6
redis==5.0.1
```

Instala: `python -m pip install -r requirements.txt`

#### 3.3 Crea `app/celery_app.py`

**Tu tarea:** Configura Celery con:
- `REDIS_URL` de variable de entorno (default `redis://localhost:6379/0`)
- Serialización JSON
- `task_track_started = True` (para saber cuándo una tarea empezó)

<details>
<summary>💡 Pista</summary>

```python
from celery import Celery
import os

def make_celery():
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    celery = Celery('image_resizer', broker=redis_url, backend=redis_url)
    celery.conf.update(...)
    return celery
```
</details>

<details>
<summary>🔑 Solución</summary>

```python
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
```
</details>

#### 3.4 Crea `app/tasks.py`

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 ¿POR QUÉ BASE64?                                       │
│                                                             │
│   Celery envía las tareas por Redis como mensajes JSON.     │
│   JSON solo admite texto, no bytes binarios.                │
│   Convertimos la imagen a base64 (texto) para enviarla,     │
│   y la convertimos de vuelta a bytes en el worker.          │
│                                                             │
│   import base64                                             │
│   encoded = base64.b64encode(image_bytes).decode('utf-8')   │
│   decoded = base64.b64decode(encoded)                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Tu tarea:** Crea la tarea `resize_image_task` que:
1. Recibe: `job_id`, `image_data_b64`, `width`, `height`, `filename`
2. Actualiza el job en BD a status `processing`
3. Decodifica la imagen de base64
4. La redimensiona con Pillow
5. Guarda el resultado en disco (por ahora, en Fase 4 será MinIO)
6. Actualiza el job a `completed` (o `failed` si hay error)

<details>
<summary>💡 Pista: Celery necesita contexto de Flask para acceder a la BD</summary>

```python
@celery_app.task(bind=True)
def resize_image_task(self, job_id, image_data_b64, width, height, filename):
    from app.app import create_app
    from app.models import db, ImageJob
    app = create_app(Config)

    with app.app_context():
        job = ImageJob.query.get(job_id)
        # ... procesar ...
```
</details>

<details>
<summary>🔑 Solución</summary>

```python
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
```
</details>

> ⚠️ Nota importante (Celery y tareas registradas)
>
> Si el worker arranca pero los jobs se quedan en `pending`, mira los logs del worker. Si aparece:
>
> `Received unregistered task of type 'app.tasks.resize_image_task'`
>
> significa que el worker **no está importando** el módulo donde viven las tasks. En ese caso:
> - Arranca el worker con `-A app.tasks:celery_app` (ver checkpoint de esta fase), **o**
> - Asegúrate de que tu `celery_app.py` importa `app.tasks` / incluye `include=['app.tasks']`.

#### 3.5 Modifica `app/app.py` para usar Celery

Ahora `/resize` ya no procesa directamente. En su lugar:
1. Recibe la imagen → la valida
2. Crea un job en BD con status `pending`
3. Encola la tarea en Celery → `resize_image_task.delay(...)`
4. Devuelve 202 con el job_id

También necesitas un nuevo endpoint `GET /jobs/<id>/download`.

**Tu tarea:** Modifica `app/app.py` con estos cambios.

<details>
<summary>💡 Pista: cómo encolar</summary>

```python
import base64
from app.tasks import resize_image_task

# Dentro del endpoint /resize, después de crear el job:
image_data_b64 = base64.b64encode(image_data).decode('utf-8')
resize_image_task.delay(job.id, image_data_b64, width, height, file.filename)

return jsonify({'job_id': job.id, 'status': 'pending'}), 202
```
</details>

<details>
<summary>🔑 Solución</summary>

```python
from flask import Flask, request, jsonify, send_file
from app.models import db, ImageJob
from app.config import Config
from PIL import Image
import io
import os
import base64
import glob
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)


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

        width = request.form.get('width', type=int)
        height = request.form.get('height', type=int)
        if not width or not height or width <= 0 or height <= 0:
            return jsonify({'error': 'Valid width and height are required'}), 400

        if width > 5000 or height > 5000:
            return jsonify({'error': 'Maximum dimension is 5000px'}), 400

        image_data = file.read()
        original_size = len(image_data)

        job = ImageJob(
            original_filename=file.filename,
            status='pending',
            width=width,
            height=height,
            original_size=original_size
        )
        db.session.add(job)
        db.session.commit()

        image_data_b64 = base64.b64encode(image_data).decode('utf-8')

        from app.tasks import resize_image_task
        resize_image_task.delay(job.id, image_data_b64, width, height, file.filename)

        return jsonify({
            'job_id': job.id,
            'status': 'pending',
            'message': 'Image queued for processing'
        }), 202

    @app.route('/jobs/<int:job_id>/download', methods=['GET'])
    def download_result(job_id):
        job = ImageJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        if job.status != 'completed':
            return jsonify({'error': 'Job not completed yet', 'status': job.status}), 409

        pattern = os.path.join(RESULTS_DIR, f'resized_{job_id}.*')
        files = glob.glob(pattern)
        if not files:
            return jsonify({'error': 'Result file not found'}), 404

        return send_file(
            files[0],
            as_attachment=True,
            download_name=f'resized_{job.original_filename}'
        )

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
```
</details>

#### 3.6 Actualiza los tests

`/resize` ahora devuelve 202 en vez de 200. Hay que actualizar tests y mockear Celery para que los tests no necesiten Redis.

<details>
<summary>🔑 conftest.py actualizado</summary>

```python
import pytest
import io
from PIL import Image
from unittest.mock import patch
from app.app import create_app
from app.models import db


class TestConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    BASE_URL = 'http://localhost:5000'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_image():
    img = Image.new('RGB', (800, 600), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


@pytest.fixture(autouse=True)
def mock_celery():
    with patch('app.tasks.resize_image_task.delay') as mock_delay:
        mock_delay.return_value = None
        yield mock_delay
```
</details>

<details>
<summary>🔑 test_app.py actualizado</summary>

```python
from io import BytesIO


def test_health_live(client):
    response = client.get('/health/live')
    assert response.status_code == 200
    assert response.json['status'] == 'alive'


def test_health_ready(client):
    response = client.get('/health/ready')
    assert response.status_code == 200
    assert response.json['status'] == 'ready'


def test_resize_accepted(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '200',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 202
    assert 'job_id' in response.json
    assert response.json['status'] == 'pending'


def test_resize_no_image(client):
    data = {'width': '200', 'height': '200'}
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_invalid_extension(client):
    data = {
        'image': (BytesIO(b'fake'), 'test.txt'),
        'width': '200',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_missing_dimensions(client, sample_image):
    data = {'image': (sample_image, 'test.png')}
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_negative_dimensions(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '-100',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_resize_too_large(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '10000',
        'height': '200'
    }
    response = client.post('/resize',
                           data=data,
                           content_type='multipart/form-data')
    assert response.status_code == 400


def test_list_jobs_empty(client):
    response = client.get('/jobs')
    assert response.status_code == 200
    assert response.json == []


def test_list_jobs_after_resize(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '100',
        'height': '100'
    }
    client.post('/resize', data=data, content_type='multipart/form-data')
    response = client.get('/jobs')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['status'] == 'pending'


def test_get_job(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '100',
        'height': '100'
    }
    res = client.post('/resize', data=data, content_type='multipart/form-data')
    job_id = res.json['job_id']
    response = client.get(f'/jobs/{job_id}')
    assert response.status_code == 200
    assert response.json['original_filename'] == 'test.png'


def test_get_job_not_found(client):
    response = client.get('/jobs/999')
    assert response.status_code == 404


def test_download_not_completed(client, sample_image):
    data = {
        'image': (sample_image, 'test.png'),
        'width': '100',
        'height': '100'
    }
    res = client.post('/resize', data=data, content_type='multipart/form-data')
    job_id = res.json['job_id']
    response = client.get(f'/jobs/{job_id}/download')
    assert response.status_code == 409
```
</details>

### ✅ Checkpoint

```bash
# Tests pasan sin Redis:
pytest tests/ -v

# Flujo completo (necesitas Redis corriendo):
# Terminal 1:
python -m app.app

# Terminal 2:
celery -A app.tasks:celery_app worker --loglevel=info --pool=solo

# Terminal 3:
curl -X POST http://localhost:5000/resize \
  -F "image=@test.jpg" -F "width=200" -F "height=200"
# → {"job_id": 1, "status": "pending"}

# Espera unos segundos:
curl http://localhost:5000/jobs/1
# → {"status": "completed", ...}

curl http://localhost:5000/jobs/1/download --output resized.jpg
```

<details>
<summary>💡 Hint: El worker da error de import</summary>

Asegúrate de estar en la carpeta raíz del proyecto. En Windows, usa `--pool=solo`:
```bash
celery -A app.tasks:celery_app worker --loglevel=info --pool=solo
```
</details>

<details>
<summary>💡 Hint: No tengo Redis y no quiero instalarlo</summary>

No pasa nada. Los tests pasan sin Redis gracias al mock. El flujo completo se prueba en OpenShift donde Redis es un pod. Continúa a la siguiente fase.
</details>

---

## Fase 4: Almacenamiento con MinIO

### 🎯 Objetivo
Las imágenes se guardan en MinIO (compatible con S3) en vez del disco local. Cuando migres a AWS, solo cambias la URL y credenciales.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 ¿QUÉ ES MINIO?                                         │
│                                                             │
│   MinIO es un servidor de almacenamiento compatible con S3. │
│   Es como tener tu propio "AWS S3" local o en tu cluster.   │
│                                                             │
│   La API es idéntica a S3:                                   │
│   - Creas "buckets" (carpetas)                              │
│   - Subes y descargas "objetos" (archivos)                  │
│   - Usas la misma librería boto3 que con AWS                │
│                                                             │
│   Cuando migres a AWS, solo cambias:                        │
│   - endpoint_url (de MinIO a S3)                            │
│   - Las credenciales                                        │
│   - El código NO cambia                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📝 Tareas

#### 4.1 Actualiza `requirements.txt`

Añade al final:
```txt
boto3==1.34.14
```

Instala: `python -m pip install -r requirements.txt`

#### 4.2 Crea `app/storage.py`

**Tu tarea:** Crea funciones para interactuar con MinIO/S3:
- `get_storage_client()` → cliente boto3
- `ensure_bucket_exists(bucket_name)` → crea bucket si no existe
- `upload_image(key, image_data)` → sube un archivo
- `download_image(key)` → descarga un archivo
- `get_download_url(key)` → genera URL temporal (presigned URL)

Lee configuración de variables de entorno:
- `STORAGE_ENDPOINT`: default `http://localhost:9000`
- `STORAGE_ACCESS_KEY`: default `minioadmin`
- `STORAGE_SECRET_KEY`: default `minioadmin`
- `STORAGE_BUCKET`: default `image-resizer`

<details>
<summary>💡 Pista: cliente boto3 para MinIO</summary>

```python
import boto3
client = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    region_name='us-east-1'
)
```
</details>

<details>
<summary>🔑 Solución</summary>

```python
import boto3
import os
from botocore.exceptions import ClientError


def get_storage_client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv('STORAGE_ENDPOINT', 'http://localhost:9000'),
        aws_access_key_id=os.getenv('STORAGE_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('STORAGE_SECRET_KEY', 'minioadmin'),
        region_name='us-east-1'
    )


def ensure_bucket_exists(bucket_name=None):
    if bucket_name is None:
        bucket_name = os.getenv('STORAGE_BUCKET', 'image-resizer')
    client = get_storage_client()
    try:
        client.head_bucket(Bucket=bucket_name)
    except ClientError:
        client.create_bucket(Bucket=bucket_name)
    return bucket_name


def upload_image(key, image_data, bucket_name=None):
    if bucket_name is None:
        bucket_name = os.getenv('STORAGE_BUCKET', 'image-resizer')
    client = get_storage_client()
    client.put_object(Bucket=bucket_name, Key=key, Body=image_data)


def download_image(key, bucket_name=None):
    if bucket_name is None:
        bucket_name = os.getenv('STORAGE_BUCKET', 'image-resizer')
    client = get_storage_client()
    response = client.get_object(Bucket=bucket_name, Key=key)
    return response['Body'].read()


def get_download_url(key, bucket_name=None, expires_in=3600):
    if bucket_name is None:
        bucket_name = os.getenv('STORAGE_BUCKET', 'image-resizer')
    client = get_storage_client()
    return client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': key},
        ExpiresIn=expires_in
    )
```
</details>

#### 4.3 Actualiza `app/tasks.py` para usar MinIO

**Tu tarea:** Modifica la tarea para que:
1. Suba la imagen original a MinIO con key `originals/{job_id}_{filename}`
2. Suba la redimensionada con key `resized/{job_id}_{filename}`
3. Ya no guarde nada en disco local

<details>
<summary>💡 Pista</summary>

En vez de `img.save(result_path)`:
```python
from app.storage import upload_image, ensure_bucket_exists

ensure_bucket_exists()
upload_image(f'originals/{job_id}_{filename}', image_data)

buffer = io.BytesIO()
img.save(buffer, format=output_format)
upload_image(f'resized/{job_id}_{filename}', buffer.getvalue())
```
</details>

<details>
<summary>🔑 Solución</summary>

```python
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
```
</details>

#### 4.4 Actualiza `app/app.py` - endpoint de descarga

**Tu tarea:** Modifica `/jobs/<id>/download` para descargar desde MinIO.

<details>
<summary>🔑 Solución (solo el endpoint que cambia)</summary>

Reemplaza `download_result` por:

```python
    @app.route('/jobs/<int:job_id>/download', methods=['GET'])
    def download_result(job_id):
        job = ImageJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        if job.status != 'completed':
            return jsonify({'error': 'Job not completed yet', 'status': job.status}), 409

        try:
            from app.storage import download_image
            resized_key = f'resized/{job_id}_{job.original_filename}'
            image_data = download_image(resized_key)

            return send_file(
                io.BytesIO(image_data),
                mimetype='image/png',
                as_attachment=True,
                download_name=f'resized_{job.original_filename}'
            )
        except Exception as e:
            return jsonify({'error': f'Could not retrieve image: {str(e)}'}), 500
```

También elimina `RESULTS_DIR`, `glob` y `os.makedirs` del archivo. Ya no se usan.
</details>

### ✅ Checkpoint

```bash
# Tests siguen pasando (Celery está mockeado, no toca MinIO):
pytest tests/ -v

# Para probar MinIO local (opcional, necesitas Docker):
# docker run -d -p 9000:9000 -p 9001:9001 --name minio \
#   -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
#   minio/minio server /data --console-address ":9001"
#
# O espera a la Fase 6 donde MinIO corre en OpenShift.
```


---

**Fin de la Parte A.** Continúa en la **Parte B** con las Fases 5-9 (Docker, Kubernetes, Sealed Secrets, Helm y CI/CD).
