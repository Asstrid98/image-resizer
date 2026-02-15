# 🖼️ Proyecto: Image Resizer — Documento 1, Parte B

## Fases 5-9: Docker, Kubernetes, Sealed Secrets, Helm y CI/CD

---

## Fase 5: Dockerización

### 🎯 Objetivo
Crear el Dockerfile. La misma imagen sirve para la API y para el worker (solo cambia el comando de inicio).

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 UNA IMAGEN, DOS USOS                                   │
│                                                             │
│   API:    gunicorn --bind 0.0.0.0:5000 app.app:app          │
│   Worker: celery -A app.celery_app:celery_app worker ...     │
│                                                             │
│   En Kubernetes, el deployment de la API y el del worker    │
│   usan la MISMA imagen pero con diferente command.          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📝 Tareas

#### 5.1 Crea el `Dockerfile`

**Tu tarea:** Crea un Dockerfile multi-stage. Ya hiciste uno para el URL Shortener. Las diferencias:
- Necesita `libjpeg-dev` y `zlib1g-dev` para Pillow (procesamiento de imágenes)
- En runtime necesita `libjpeg62-turbo` y `zlib1g`
- Comando por defecto: gunicorn (API)

<details>
<summary>💡 Pista: dependencias del builder</summary>

```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
```
</details>

<details>
<summary>💡 Pista: dependencias del runtime</summary>

```dockerfile
RUN apt-get update && apt-get install -y \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*
```
</details>

<details>
<summary>🔑 Solución</summary>

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc libpq-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libpq5 libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY app/ ./app/
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health/live')" || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app.app:app"]
```
</details>

#### 5.2 Crea `.dockerignore`

```
__pycache__
*.pyc
*.pyo
.Python
env/
venv/
.venv/
.git
.gitignore
.dockerignore
Dockerfile
*.md
tests/
.pytest_cache/
.coverage
k8s/
helm/
.github/
*.db
results/
```

### ✅ Checkpoint

```bash
ls Dockerfile .dockerignore  # Ambos archivos existen
pytest tests/ -v              # Tests siguen pasando
```

---

## Fase 6: Manifiestos de Kubernetes

### 🎯 Objetivo
Crear los manifiestos para desplegar TODO en OpenShift: API, Worker, Redis, MinIO y PostgreSQL.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 MÁS DEPLOYMENTS QUE EL URL SHORTENER                   │
│                                                             │
│   URL Shortener: 2 deployments (app + postgres)             │
│   Image Resizer: 5 deployments (api + worker + redis +      │
│                                  minio + postgres)          │
│                                                             │
│   No te agobies. Son repetitivos. Una vez hagas uno,        │
│   los demás siguen el mismo patrón.                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📝 Tareas

#### 6.1 `k8s/configmap.yaml` — ConfigMap con `BASE_URL`, `STORAGE_ENDPOINT`, `STORAGE_BUCKET`, `REDIS_URL`

#### 6.2 `k8s/secret.yaml` — Secret con `DATABASE_URL`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`

#### 6.3 `k8s/redis.yaml` — Deployment + Service (redis:7-alpine, puerto 6379)

#### 6.4 `k8s/minio.yaml` — PVC + Deployment + Service (minio, puertos 9000/9001)

#### 6.5 `k8s/postgresql.yaml` — Secret + PVC + Deployment + Service (postgresql:15-el9)

#### 6.6 `k8s/api-deployment.yaml` — Deployment API Flask (puerto 5000, probes en /health/*)

#### 6.7 `k8s/worker-deployment.yaml` — Deployment Worker (misma imagen, command celery)

#### 6.8 `k8s/service.yaml` + `k8s/route.yaml` — Service + Route para exponer la API

Todos estos manifiestos son idénticos a lo que ya tienes en el proyecto de pruebas (el zip que te dimos). Los tienes completos en las soluciones de la Parte A del URL Shortener y adaptados aquí. Si necesitas los YAML completos, abre las soluciones:

<details>
<summary>🔑 Solución: configmap.yaml</summary>

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: image-resizer-config
  labels:
    app: image-resizer
data:
  BASE_URL: "https://image-resizer-TUNAMESPACE.apps.sandbox-xxx.openshiftapps.com"
  STORAGE_ENDPOINT: "http://minio:9000"
  STORAGE_BUCKET: "image-resizer"
  REDIS_URL: "redis://redis:6379/0"
```
</details>

<details>
<summary>🔑 Solución: secret.yaml</summary>

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: image-resizer-secret
  labels:
    app: image-resizer
type: Opaque
stringData:
  DATABASE_URL: "postgresql://imageresizer:password123@postgresql:5432/imageresizer"
  STORAGE_ACCESS_KEY: "minioadmin"
  STORAGE_SECRET_KEY: "minioadmin"
```
</details>

<details>
<summary>🔑 Solución: redis.yaml</summary>

```yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  labels:
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "128Mi"
              cpu: "250m"
          livenessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  type: ClusterIP
  ports:
    - port: 6379
      targetPort: 6379
  selector:
    app: redis
```
</details>

<details>
<summary>🔑 Solución: minio.yaml</summary>

```yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minio-pvc
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
        - name: minio
          image: minio/minio:RELEASE.2024-01-16T16-07-38Z
          command: ["minio", "server", "/data", "--console-address", ":9001"]
          ports:
            - containerPort: 9000
            - containerPort: 9001
          env:
            - name: MINIO_ROOT_USER
              value: "minioadmin"
            - name: MINIO_ROOT_PASSWORD
              value: "minioadmin"
          volumeMounts:
            - name: minio-data
              mountPath: /data
          resources:
            requests: { memory: "128Mi", cpu: "100m" }
            limits: { memory: "256Mi", cpu: "500m" }
          livenessProbe:
            httpGet: { path: /minio/health/live, port: 9000 }
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet: { path: /minio/health/live, port: 9000 }
            initialDelaySeconds: 10
            periodSeconds: 5
      volumes:
        - name: minio-data
          persistentVolumeClaim:
            claimName: minio-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: minio
spec:
  type: ClusterIP
  ports:
    - port: 9000
      targetPort: 9000
      name: api
    - port: 9001
      targetPort: 9001
      name: console
  selector:
    app: minio
```
</details>

<details>
<summary>🔑 Solución: postgresql.yaml</summary>

```yaml
---
apiVersion: v1
kind: Secret
metadata:
  name: postgresql-secret
type: Opaque
stringData:
  POSTGRESQL_USER: imageresizer
  POSTGRESQL_PASSWORD: password123
  POSTGRESQL_DATABASE: imageresizer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgresql-pvc
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
        - name: postgresql
          image: image-registry.openshift-image-registry.svc:5000/openshift/postgresql:15-el9
          ports:
            - containerPort: 5432
          envFrom:
            - secretRef:
                name: postgresql-secret
          volumeMounts:
            - name: postgresql-data
              mountPath: /var/lib/pgsql/data
          resources:
            requests: { memory: "128Mi", cpu: "100m" }
            limits: { memory: "256Mi", cpu: "500m" }
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "imageresizer"]
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "imageresizer"]
            initialDelaySeconds: 5
            periodSeconds: 5
      volumes:
        - name: postgresql-data
          persistentVolumeClaim:
            claimName: postgresql-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
spec:
  type: ClusterIP
  ports:
    - port: 5432
      targetPort: 5432
  selector:
    app: postgresql
```
</details>

<details>
<summary>🔑 Solución: api-deployment.yaml</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-resizer-api
  labels:
    app: image-resizer
    component: api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: image-resizer
      component: api
  template:
    metadata:
      labels:
        app: image-resizer
        component: api
    spec:
      containers:
        - name: api
          image: ghcr.io/TU-USUARIO/image-resizer:latest
          ports:
            - containerPort: 5000
          envFrom:
            - configMapRef:
                name: image-resizer-config
            - secretRef:
                name: image-resizer-secret
          resources:
            requests: { memory: "64Mi", cpu: "50m" }
            limits: { memory: "256Mi", cpu: "500m" }
          livenessProbe:
            httpGet: { path: /health/live, port: 5000 }
            initialDelaySeconds: 15
            periodSeconds: 10
          readinessProbe:
            httpGet: { path: /health/ready, port: 5000 }
            initialDelaySeconds: 10
            periodSeconds: 5
```
</details>

<details>
<summary>🔑 Solución: worker-deployment.yaml</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-resizer-worker
  labels:
    app: image-resizer
    component: worker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: image-resizer
      component: worker
  template:
    metadata:
      labels:
        app: image-resizer
        component: worker
    spec:
      containers:
        - name: worker
          image: ghcr.io/TU-USUARIO/image-resizer:latest
          command: ["celery"]
          args: ["-A", "app.celery_app:celery_app", "worker", "--loglevel=info", "--concurrency=2"]
          envFrom:
            - configMapRef:
                name: image-resizer-config
            - secretRef:
                name: image-resizer-secret
          resources:
            requests: { memory: "128Mi", cpu: "100m" }
            limits: { memory: "512Mi", cpu: "500m" }
```
</details>

<details>
<summary>🔑 Solución: service.yaml + route.yaml</summary>

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: image-resizer
spec:
  type: ClusterIP
  ports:
    - port: 5000
      targetPort: 5000
      name: http
  selector:
    app: image-resizer
    component: api
```

**route.yaml:**
```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: image-resizer
spec:
  to:
    kind: Service
    name: image-resizer
    weight: 100
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
```
</details>

### ✅ Checkpoint de la Fase 6

```bash
oc login --token=<tu-token> --server=<tu-server>
oc apply -f k8s/postgresql.yaml
oc apply -f k8s/redis.yaml
oc apply -f k8s/minio.yaml
oc get pods -w   # Espera hasta Running

oc apply -f k8s/configmap.yaml
oc apply -f k8s/secret.yaml
oc apply -f k8s/api-deployment.yaml
oc apply -f k8s/worker-deployment.yaml
oc apply -f k8s/service.yaml
oc apply -f k8s/route.yaml
```

<details>
<summary>💡 Hint: Los pods de api/worker dan ImagePullBackOff</summary>

Normal — la imagen Docker aún no existe en ghcr.io. Se crea en Fase 9 con GitHub Actions. Los pods de infra (PostgreSQL, Redis, MinIO) sí deben estar Running.
</details>

<details>
<summary>💡 Hint: MinIO no arranca en OpenShift</summary>

OpenShift ejecuta contenedores con usuario random. Prueba la imagen de Bitnami:
```yaml
image: bitnami/minio:2024.1.16
```
</details>

---

## Fase 7: Sealed Secrets

### 🎯 Objetivo
Encriptar secrets para commitearlos de forma segura.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Secret (plaintext) → kubeseal → SealedSecret (encriptado) │
│          NO commitear           SÍ commitear                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📝 Tareas

#### 7.1 Instala el controlador en OpenShift

```bash
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system \
  --set fullnameOverride=sealed-secrets-controller
```

> ⚠️ Si el Sandbox no te deja, instala en tu namespace o salta esta fase. Practicarás Sealed Secrets en el Documento 2 con AWS/EKS.

#### 7.2 Instala kubeseal

**Windows:** Descarga desde [GitHub releases](https://github.com/bitnami-labs/sealed-secrets/releases) y pon en PATH.
**Mac:** `brew install kubeseal`

#### 7.3 Encripta y aplica

```bash
kubeseal --format yaml < k8s/secret.yaml > k8s/sealed-secret.yaml

# Añade a .gitignore:
echo "k8s/secret.yaml" >> .gitignore

# Aplica
oc delete secret image-resizer-secret 2>/dev/null
oc apply -f k8s/sealed-secret.yaml
```

### ✅ Checkpoint

```bash
oc get secret image-resizer-secret  # Debe existir (creado por el controlador)
```

---

## Fase 8: Helm Chart

### 🎯 Objetivo
Convertir todos los manifiestos en un Helm Chart parametrizable.

### 📝 Tareas

#### 8.1 `helm/image-resizer/Chart.yaml`

```yaml
apiVersion: v2
name: image-resizer
description: An image resizing service with async processing
type: application
version: 1.0.0
appVersion: "1.0.0"
```

#### 8.2 `helm/image-resizer/values.yaml`

**Tu tarea:** Crea el values con secciones: `image`, `api`, `worker`, `redis`, `minio`, `postgresql`, `service`, `route`, `config`, `probes`. Los valores son los mismos que hardcodeaste en k8s/.

<details>
<summary>🔑 Solución</summary>

```yaml
image:
  repository: ghcr.io/TU-USUARIO/image-resizer
  tag: "latest"
  pullPolicy: Always

api:
  replicaCount: 1
  resources:
    requests: { memory: "64Mi", cpu: "50m" }
    limits: { memory: "256Mi", cpu: "500m" }

worker:
  replicaCount: 1
  concurrency: 2
  resources:
    requests: { memory: "128Mi", cpu: "100m" }
    limits: { memory: "512Mi", cpu: "500m" }

redis:
  enabled: true
  resources:
    requests: { memory: "64Mi", cpu: "50m" }
    limits: { memory: "128Mi", cpu: "250m" }

minio:
  enabled: true
  storage: 1Gi
  rootUser: minioadmin
  rootPassword: minioadmin
  resources:
    requests: { memory: "128Mi", cpu: "100m" }
    limits: { memory: "256Mi", cpu: "500m" }

postgresql:
  enabled: true
  storage: 1Gi
  user: imageresizer
  password: password123
  database: imageresizer

service:
  type: ClusterIP
  port: 5000

route:
  enabled: true
  host: ""

config:
  baseUrl: ""
  storageBucket: "image-resizer"

probes:
  liveness:
    initialDelaySeconds: 15
    periodSeconds: 10
  readiness:
    initialDelaySeconds: 10
    periodSeconds: 5
```
</details>

#### 8.3 `helm/image-resizer/values-dev.yaml`

```yaml
api:
  replicaCount: 1
  resources:
    requests: { memory: "64Mi", cpu: "50m" }
    limits: { memory: "128Mi", cpu: "250m" }
worker:
  replicaCount: 1
minio:
  storage: 512Mi
postgresql:
  storage: 512Mi
```

#### 8.4 `_helpers.tpl` y templates

**Tu tarea:** Crea `_helpers.tpl` y convierte cada manifiesto de k8s/ en un template (reemplazar valores por `{{ .Values.xxx }}`). El proceso es el mismo que en URL Shortener.

Los templates los tienes completos en el zip del proyecto de pruebas. La diferencia clave respecto al URL Shortener es el **worker-deployment.yaml**:

```yaml
# Lo nuevo: misma imagen, diferente command
command: ["celery"]
args: ["-A", "app.celery_app:celery_app", "worker",
       "--loglevel=info",
       "--concurrency={{ .Values.worker.concurrency }}"]
```

### ✅ Checkpoint

```bash
helm lint helm/image-resizer/
helm template my-release helm/image-resizer/ -f helm/image-resizer/values-dev.yaml

# Limpia recursos manuales e instala con Helm:
helm upgrade --install image-resizer helm/image-resizer/ \
  -f helm/image-resizer/values-dev.yaml \
  --wait --timeout 300s
```

---

## Fase 9: GitHub Actions CI/CD

### 🎯 Objetivo
Automatizar tests, build de imagen Docker y deploy a OpenShift.

### 📝 Tareas

#### 9.1 `.github/workflows/ci.yml` — Tests + Build + Push imagen

#### 9.2 `.github/workflows/cd.yml` — Deploy con Helm a OpenShift

Ya conoces estos pipelines del URL Shortener. Las diferencias:
- CI incluye servicio de PostgreSQL para tests
- CD usa `github.event.workflow_run.head_sha` para el tag (lección aprendida del URL Shortener)

Los archivos completos están en el zip del proyecto de pruebas. Si quieres escribirlos tú, las soluciones están aquí:

<details>
<summary>🔑 Solución: ci.yml</summary>

```yaml
name: CI
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: imageresizer_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/imageresizer_test
      - run: |
          pip install flake8
          flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=raw,value=latest
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          no-cache: true
```
</details>

<details>
<summary>🔑 Solución: cd.yml</summary>

```yaml
name: CD
on:
  workflow_run:
    workflows: [CI]
    types: [completed]
    branches: [main]

env:
  REGISTRY: ghcr.io

jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    steps:
      - uses: actions/checkout@v4
      - uses: redhat-actions/oc-installer@v1
        with: { oc_version: 'latest' }
      - uses: azure/setup-helm@v3
        with: { version: '3.13.0' }
      - run: oc login --token=${{ secrets.OPENSHIFT_TOKEN }} --server=${{ secrets.OPENSHIFT_SERVER }}
      - name: Set image tag
        run: |
          echo "IMAGE_TAG=$(echo '${{ github.event.workflow_run.head_sha }}' | cut -c1-7)" >> $GITHUB_ENV
          echo "IMAGE_REPO=$(echo '${{ github.repository }}' | tr '[:upper:]' '[:lower:]')" >> $GITHUB_ENV
      - name: Deploy with Helm
        run: |
          helm upgrade --install image-resizer ./helm/image-resizer \
            -f ./helm/image-resizer/values-dev.yaml \
            --set image.repository=${{ env.REGISTRY }}/${{ env.IMAGE_REPO }} \
            --set image.tag=${{ env.IMAGE_TAG }} \
            --wait --timeout 300s
      - name: Verify
        run: |
          ROUTE_URL=$(oc get route image-resizer -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
          if [ -n "$ROUTE_URL" ]; then
            echo "URL: https://$ROUTE_URL"
            sleep 15
            curl -sf https://$ROUTE_URL/health/live || echo "Health check pending"
          fi
```
</details>

### ✅ Checkpoint Final

1. Commit y push a `main`
2. CI ejecuta tests + build
3. CD despliega a OpenShift
4. Verifica:
   ```bash
   oc get pods       # 5 pods Running
   oc get routes     # URL de la app

   ROUTE=$(oc get route image-resizer -o jsonpath='{.spec.host}')
   curl https://$ROUTE/health/live
   curl -X POST https://$ROUTE/resize -F "image=@test.jpg" -F "width=200" -F "height=200"
   curl https://$ROUTE/jobs/1
   curl https://$ROUTE/jobs/1/download --output resized.jpg
   ```

---

## 🎉 ¡Documento 1 Completado!

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   📊 URL Shortener vs Image Resizer                         │
│                                                             │
│   1 servicio        →  2 servicios (API + Worker)           │
│   1 BD              →  1 BD + Redis + MinIO                 │
│   Síncrono          →  Asíncrono (colas)                    │
│   Solo texto        →  Archivos binarios                    │
│   Secrets plaintext →  Sealed Secrets                       │
│   2 deployments     →  5 deployments                        │
│                                                             │
│   ¡Salto grande! 🚀                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Siguiente: Documento 2

- **Terraform + AWS:** VPC, EKS, S3, ElastiCache, RDS
- **External Secrets:** AWS Secrets Manager
- **ArgoCD:** GitOps (push → pull)
- **DevSecOps:** Trivy, Bandit, Checkov
