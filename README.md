# 🖼️ Proyecto: Image Resizer — Documento 1, Parte B (continuación)

## Fase 6 (continuación): Checkpoint y Despliegue Manual

### ✅ Checkpoint de la Fase 6

```bash
# Login a OpenShift
oc login --token=<tu-token> --server=<tu-server>

# Despliega los servicios de infraestructura primero
oc apply -f k8s/postgresql.yaml
oc apply -f k8s/redis.yaml
oc apply -f k8s/minio.yaml

# Espera a que estén running
oc get pods -w
# Espera hasta ver los 3 pods en Running

# Despliega la app (la imagen aún no existe, esto se arregla en Fase 9)
oc apply -f k8s/configmap.yaml
oc apply -f k8s/secret.yaml
oc apply -f k8s/api-deployment.yaml
oc apply -f k8s/worker-deployment.yaml
oc apply -f k8s/service.yaml
oc apply -f k8s/route.yaml

# Verifica
oc get pods
oc get routes
oc get services
```

<details>
<summary>💡 Hint: Los pods de api/worker dan ImagePullBackOff</summary>

Es normal. La imagen Docker aún no existe en ghcr.io. Se creará cuando configures GitHub Actions en la Fase 9. Los pods de infraestructura (PostgreSQL, Redis, MinIO) sí deben estar Running.
</details>

<details>
<summary>💡 Hint: MinIO no arranca en OpenShift</summary>

OpenShift ejecuta contenedores con un usuario random (no root). Si MinIO falla, prueba a añadir un SecurityContext:

```yaml
# Dentro del template.spec del deployment de MinIO:
securityContext:
  runAsUser: 1000
  fsGroup: 1000
```

Si sigue fallando, también puedes usar la imagen de Bitnami que es compatible con OpenShift:
```yaml
image: bitnami/minio:2024.1.16
env:
  - name: MINIO_ROOT_USER
    value: "minioadmin"
  - name: MINIO_ROOT_PASSWORD
    value: "minioadmin"
  - name: MINIO_DEFAULT_BUCKETS
    value: "image-resizer"
```
</details>

---

## Fase 7: Sealed Secrets

### 🎯 Objetivo
Los secrets que creaste en la Fase 6 tienen las contraseñas en texto plano en el YAML. Cualquiera que vea el repo puede leerlas. Sealed Secrets encripta los secrets para que puedas commitearlos de forma segura.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 EL PROBLEMA                                             │
│                                                             │
│   Tu secret.yaml tiene esto:                                │
│     DATABASE_URL: "postgresql://user:password123@..."        │
│                                                             │
│   Si lo commiteas a Git, cualquiera ve la contraseña.       │
│   Incluso si el repo es privado, es mala práctica.          │
│                                                             │
│   LA SOLUCIÓN: SEALED SECRETS                               │
│                                                             │
│   1. Tú escribes un Secret normal                           │
│   2. Lo encriptas con kubeseal → genera un SealedSecret     │
│   3. Commiteas el SealedSecret (encriptado, seguro)         │
│   4. El controlador en el cluster lo desencripta             │
│   5. Crea el Secret real automáticamente                    │
│                                                             │
│   Secret (plaintext) → kubeseal → SealedSecret (encriptado) │
│          NO commitear           SÍ commitear                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📝 Tareas

#### 7.1 Instala el controlador de Sealed Secrets en OpenShift

```bash
# Añadir el repo de Helm de Bitnami
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update

# Instalar el controlador
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system \
  --set fullnameOverride=sealed-secrets-controller
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ⚠️  OPENSHIFT SANDBOX: Si no tienes permisos para         │
│   instalar en kube-system, instala en tu namespace:         │
│                                                             │
│   helm install sealed-secrets sealed-secrets/sealed-secrets │
│     --namespace TU-NAMESPACE                                │
│                                                             │
│   Si tampoco funciona por permisos del Sandbox, no te       │
│   preocupes. Puedes continuar con secrets normales y        │
│   practicar Sealed Secrets cuando tengas un cluster real    │
│   o en el Documento 2 con AWS/EKS.                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 7.2 Instala kubeseal en tu máquina

**Windows:**
1. Descarga desde [github.com/bitnami-labs/sealed-secrets/releases](https://github.com/bitnami-labs/sealed-secrets/releases)
2. Busca `kubeseal-x.x.x-windows-amd64.tar.gz`
3. Extrae y mueve `kubeseal.exe` a una carpeta en tu PATH

**Mac:**
```bash
brew install kubeseal
```

**Verificar:**
```bash
kubeseal --version
```

#### 7.3 Encripta tus secrets

```bash
# Encriptar el secret de la app
kubeseal --format yaml < k8s/secret.yaml > k8s/sealed-secret.yaml

# Encriptar el secret de PostgreSQL
kubeseal --format yaml < k8s/postgresql-secret.yaml > k8s/sealed-postgresql-secret.yaml
```

El archivo `sealed-secret.yaml` resultante tiene los valores encriptados. **Este sí puedes commitearlo.**

#### 7.4 Actualiza `.gitignore`

Añade:
```
# Secrets sin encriptar (NUNCA commitear)
k8s/secret.yaml
k8s/postgresql-secret.yaml
```

#### 7.5 Aplica los Sealed Secrets

```bash
# Elimina los secrets antiguos
oc delete secret image-resizer-secret
oc delete secret postgresql-secret

# Aplica los sealed secrets
oc apply -f k8s/sealed-secret.yaml
oc apply -f k8s/sealed-postgresql-secret.yaml

# Verifica que se crearon los secrets reales
oc get secrets
# Debes ver image-resizer-secret y postgresql-secret
```

### ✅ Checkpoint

```bash
# Verificar que los secrets se desencriptaron correctamente
oc get secret image-resizer-secret -o jsonpath='{.data.DATABASE_URL}' | base64 -d
# Debe mostrar tu DATABASE_URL

# Los pods deben seguir funcionando
oc get pods
```

<details>
<summary>💡 Hint: kubeseal da error "cannot fetch certificate"</summary>

Necesita conectarse al controlador en el cluster. Asegúrate de que:
1. Estás logueado en OpenShift (`oc whoami`)
2. El controlador está instalado (`helm list` o `oc get pods -n kube-system`)

Si el Sandbox no te deja instalar el controlador, puedes usar el flag `--cert` con un certificado público o saltar esta fase.
</details>

<details>
<summary>💡 Hint: El Sandbox de OpenShift no me deja instalar Sealed Secrets</summary>

El Sandbox tiene permisos limitados. Opciones:

1. **Continúa sin Sealed Secrets por ahora.** Practica el concepto teóricamente y lo aplicas en el Documento 2 cuando tengas EKS en AWS con permisos completos.

2. **Usa esta alternativa ligera:** En vez de Sealed Secrets, simplemente no commitees los secrets y créalos manualmente con `oc create secret`. El pipeline de CD los referencia pero no los crea.

No te frustres con esto. La limitación es del Sandbox, no tuya.
</details>

---

## Fase 8: Helm Chart

### 🎯 Objetivo
Convertir todos los manifiestos de k8s/ en un Helm Chart parametrizable. Ya hiciste esto con el URL Shortener.

### 📝 Tareas

#### 8.1 Crea `helm/image-resizer/Chart.yaml`

```yaml
apiVersion: v2
name: image-resizer
description: An image resizing service with async processing
type: application
version: 1.0.0
appVersion: "1.0.0"
```

#### 8.2 Crea `helm/image-resizer/values.yaml`

**Tu tarea:** Crea el values.yaml con valores por defecto para todos los componentes. Ya lo hiciste para el URL Shortener, así que sabes la estructura.

Necesitas secciones para:
- `image` (repository, tag, pullPolicy)
- `api` (replicaCount, resources)
- `worker` (replicaCount, resources, concurrency)
- `redis` (enabled, resources)
- `minio` (enabled, storage, resources)
- `postgresql` (enabled, storage, user, password, database)
- `service` (type, port)
- `route` (enabled)
- `config` (baseUrl, storageBucket)
- `probes` (liveness, readiness settings)

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
    requests:
      memory: "64Mi"
      cpu: "50m"
    limits:
      memory: "256Mi"
      cpu: "500m"

worker:
  replicaCount: 1
  concurrency: 2
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "500m"

redis:
  enabled: true
  resources:
    requests:
      memory: "64Mi"
      cpu: "50m"
    limits:
      memory: "128Mi"
      cpu: "250m"

minio:
  enabled: true
  storage: 1Gi
  rootUser: minioadmin
  rootPassword: minioadmin
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "256Mi"
      cpu: "500m"

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

#### 8.3 Crea `helm/image-resizer/values-dev.yaml`

```yaml
api:
  replicaCount: 1
  resources:
    requests:
      memory: "64Mi"
      cpu: "50m"
    limits:
      memory: "128Mi"
      cpu: "250m"

worker:
  replicaCount: 1

minio:
  storage: 512Mi

postgresql:
  storage: 512Mi
```

#### 8.4 Crea `helm/image-resizer/templates/_helpers.tpl`

**Tu tarea:** Crea los helpers. Reutiliza lo que ya conoces del URL Shortener.

<details>
<summary>🔑 Solución</summary>

```yaml
{{- define "image-resizer.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "image-resizer.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "image-resizer.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "image-resizer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "image-resizer.selectorLabels" -}}
app.kubernetes.io/name: {{ include "image-resizer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "image-resizer.databaseUrl" -}}
postgresql://{{ .Values.postgresql.user }}:{{ .Values.postgresql.password }}@postgresql:5432/{{ .Values.postgresql.database }}
{{- end }}
```
</details>

#### 8.5 Crea los templates

Ahora necesitas convertir cada manifiesto de k8s/ en un template de Helm. Es el mismo proceso que con el URL Shortener: reemplazar valores hardcodeados por `{{ .Values.xxx }}`.

**Tu tarea:** Crea estos templates. Ya sabes cómo hacerlo del URL Shortener, así que te doy menos pistas aquí.

Templates necesarios:
- `templates/configmap.yaml`
- `templates/secret.yaml`
- `templates/api-deployment.yaml`
- `templates/worker-deployment.yaml`
- `templates/service.yaml`
- `templates/route.yaml`
- `templates/redis.yaml`
- `templates/minio.yaml`
- `templates/postgresql.yaml`

<details>
<summary>💡 Pista: template del worker</summary>

Lo más nuevo aquí es el worker. Es un deployment que usa la misma imagen pero con command diferente:

```yaml
containers:
  - name: worker
    image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
    command: ["celery"]
    args: ["-A", "app.celery_app:celery_app", "worker",
           "--loglevel=info",
           "--concurrency={{ .Values.worker.concurrency }}"]
```
</details>

<details>
<summary>🔑 Solución: api-deployment.yaml</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "image-resizer.fullname" . }}-api
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
    component: api
spec:
  replicas: {{ .Values.api.replicaCount }}
  selector:
    matchLabels:
      {{- include "image-resizer.selectorLabels" . | nindent 6 }}
      component: api
  template:
    metadata:
      labels:
        {{- include "image-resizer.selectorLabels" . | nindent 8 }}
        component: api
    spec:
      containers:
        - name: api
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 5000
          envFrom:
            - configMapRef:
                name: {{ include "image-resizer.fullname" . }}-config
            - secretRef:
                name: {{ include "image-resizer.fullname" . }}-secret
          resources:
            {{- toYaml .Values.api.resources | nindent 12 }}
          livenessProbe:
            httpGet:
              path: /health/live
              port: 5000
            initialDelaySeconds: {{ .Values.probes.liveness.initialDelaySeconds }}
            periodSeconds: {{ .Values.probes.liveness.periodSeconds }}
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 5000
            initialDelaySeconds: {{ .Values.probes.readiness.initialDelaySeconds }}
            periodSeconds: {{ .Values.probes.readiness.periodSeconds }}
```
</details>

<details>
<summary>🔑 Solución: worker-deployment.yaml</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "image-resizer.fullname" . }}-worker
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
    component: worker
spec:
  replicas: {{ .Values.worker.replicaCount }}
  selector:
    matchLabels:
      {{- include "image-resizer.selectorLabels" . | nindent 6 }}
      component: worker
  template:
    metadata:
      labels:
        {{- include "image-resizer.selectorLabels" . | nindent 8 }}
        component: worker
    spec:
      containers:
        - name: worker
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          command: ["celery"]
          args: ["-A", "app.celery_app:celery_app", "worker", "--loglevel=info", "--concurrency={{ .Values.worker.concurrency }}"]
          envFrom:
            - configMapRef:
                name: {{ include "image-resizer.fullname" . }}-config
            - secretRef:
                name: {{ include "image-resizer.fullname" . }}-secret
          resources:
            {{- toYaml .Values.worker.resources | nindent 12 }}
```
</details>

<details>
<summary>🔑 Solución: configmap.yaml</summary>

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "image-resizer.fullname" . }}-config
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
data:
  {{- if .Values.config.baseUrl }}
  BASE_URL: {{ .Values.config.baseUrl | quote }}
  {{- else if .Values.route.enabled }}
  BASE_URL: "https://{{ include "image-resizer.fullname" . }}-{{ .Release.Namespace }}.apps.sandbox.openshiftapps.com"
  {{- else }}
  BASE_URL: "http://localhost:5000"
  {{- end }}
  STORAGE_ENDPOINT: "http://minio:9000"
  STORAGE_BUCKET: {{ .Values.config.storageBucket | quote }}
  REDIS_URL: "redis://redis:6379/0"
```
</details>

<details>
<summary>🔑 Solución: secret.yaml</summary>

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "image-resizer.fullname" . }}-secret
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
type: Opaque
stringData:
  DATABASE_URL: {{ include "image-resizer.databaseUrl" . | quote }}
  STORAGE_ACCESS_KEY: {{ .Values.minio.rootUser | quote }}
  STORAGE_SECRET_KEY: {{ .Values.minio.rootPassword | quote }}
```
</details>

<details>
<summary>🔑 Solución: service.yaml y route.yaml</summary>

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "image-resizer.fullname" . }}
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: 5000
      protocol: TCP
      name: http
  selector:
    {{- include "image-resizer.selectorLabels" . | nindent 4 }}
    component: api
```

**route.yaml:**
```yaml
{{- if .Values.route.enabled }}
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: {{ include "image-resizer.fullname" . }}
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
spec:
  {{- if .Values.route.host }}
  host: {{ .Values.route.host }}
  {{- end }}
  to:
    kind: Service
    name: {{ include "image-resizer.fullname" . }}
    weight: 100
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
{{- end }}
```
</details>

<details>
<summary>🔑 Solución: redis.yaml</summary>

```yaml
{{- if .Values.redis.enabled }}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
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
            {{- toYaml .Values.redis.resources | nindent 12 }}
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
  labels:
    app: redis
spec:
  type: ClusterIP
  ports:
    - port: 6379
      targetPort: 6379
  selector:
    app: redis
{{- end }}
```
</details>

<details>
<summary>🔑 Solución: minio.yaml</summary>

```yaml
{{- if .Values.minio.enabled }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minio-pvc
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.minio.storage }}

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
    app: minio
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
              value: {{ .Values.minio.rootUser | quote }}
            - name: MINIO_ROOT_PASSWORD
              value: {{ .Values.minio.rootPassword | quote }}
          volumeMounts:
            - name: minio-data
              mountPath: /data
          resources:
            {{- toYaml .Values.minio.resources | nindent 12 }}
          livenessProbe:
            httpGet:
              path: /minio/health/live
              port: 9000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /minio/health/live
              port: 9000
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
  labels:
    app: minio
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
{{- end }}
```
</details>

<details>
<summary>🔑 Solución: postgresql.yaml</summary>

```yaml
{{- if .Values.postgresql.enabled }}
---
apiVersion: v1
kind: Secret
metadata:
  name: postgresql-secret
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
type: Opaque
stringData:
  POSTGRESQL_USER: {{ .Values.postgresql.user }}
  POSTGRESQL_PASSWORD: {{ .Values.postgresql.password }}
  POSTGRESQL_DATABASE: {{ .Values.postgresql.database }}

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgresql-pvc
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.postgresql.storage }}

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
    app: postgresql
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
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "{{ .Values.postgresql.user }}"]
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "{{ .Values.postgresql.user }}"]
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
  labels:
    app: postgresql
spec:
  type: ClusterIP
  ports:
    - port: 5432
      targetPort: 5432
  selector:
    app: postgresql
{{- end }}
```
</details>

### ✅ Checkpoint de la Fase 8

```bash
# Validar el chart
helm lint helm/image-resizer/

# Ver qué se generaría
helm template my-release helm/image-resizer/ -f helm/image-resizer/values-dev.yaml

# Si todo está limpio, limpia los recursos manuales e instala con Helm:
# PRIMERO borra lo que instalaste manualmente en Fase 6
oc delete deployment image-resizer-api image-resizer-worker redis minio postgresql
oc delete service image-resizer redis minio postgresql
oc delete route image-resizer
oc delete configmap image-resizer-config
oc delete secret image-resizer-secret postgresql-secret
oc delete pvc minio-pvc postgresql-pvc

# LUEGO instala con Helm
helm upgrade --install image-resizer helm/image-resizer/ \
  -f helm/image-resizer/values-dev.yaml \
  --wait --timeout 300s
```

---

## Fase 9: GitHub Actions CI/CD

### 🎯 Objetivo
Automatizar tests, build de imagen Docker y deploy a OpenShift. Igual que en el URL Shortener pero adaptado.

### 📝 Tareas

#### 9.1 Crea `.github/workflows/ci.yml`

**Tu tarea:** Crea el pipeline de CI. Ya conoces la estructura del URL Shortener. Las diferencias:
- Necesita servicio de Redis para los tests (aunque estamos mockeando, es buena práctica)
- Necesita servicio de PostgreSQL
- El linter puede ser el mismo

<details>
<summary>🔑 Solución</summary>

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
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/imageresizer_test
        run: pytest tests/ -v --tb=short

      - name: Run linter
        run: |
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
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=raw,value=latest

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          no-cache: true
```
</details>

#### 9.2 Crea `.github/workflows/cd.yml`

**Tu tarea:** Crea el pipeline de CD que despliega con Helm a OpenShift.

<details>
<summary>🔑 Solución</summary>

```yaml
name: CD

on:
  workflow_run:
    workflows: [CI]
    types: [completed]
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install OpenShift CLI
        uses: redhat-actions/oc-installer@v1
        with:
          oc_version: 'latest'

      - name: Install Helm
        uses: azure/setup-helm@v3
        with:
          version: '3.13.0'

      - name: Login to OpenShift
        run: |
          oc login --token=${{ secrets.OPENSHIFT_TOKEN }} --server=${{ secrets.OPENSHIFT_SERVER }}

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
            --wait \
            --timeout 300s

      - name: Verify deployment
        run: |
          ROUTE_URL=$(oc get route image-resizer -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
          if [ -n "$ROUTE_URL" ]; then
            echo "🚀 Application URL: https://$ROUTE_URL"
            sleep 15
            curl -sf https://$ROUTE_URL/health/live || echo "⚠️ Health check failed, but deployment may still be starting"
          else
            echo "⚠️ No route found. Check the deployment manually."
          fi
          echo "✅ Deploy step completed"
```
</details>

### ✅ Checkpoint Final

1. Haz commit y push a `main`
2. Ve a la pestaña Actions en GitHub
3. Deberías ver CI ejecutándose (tests + build)
4. Luego CD (deploy a OpenShift)
5. Verifica en OpenShift:
   ```bash
   oc get pods
   # Debes ver: api, worker, redis, minio, postgresql - todos Running

   oc get routes
   # Debes ver la URL de la app
   ```

6. ¡Prueba la app desplegada!
   ```bash
   ROUTE=$(oc get route image-resizer -o jsonpath='{.spec.host}')

   # Health check
   curl https://$ROUTE/health/live

   # Resize una imagen
   curl -X POST https://$ROUTE/resize \
     -F "image=@test.jpg" \
     -F "width=200" \
     -F "height=200"
   # → {"job_id": 1, "status": "pending"}

   # Espera unos segundos y consulta el job
   curl https://$ROUTE/jobs/1
   # → {"status": "completed", ...}

   # Descarga el resultado
   curl https://$ROUTE/jobs/1/download --output resized.jpg
   ```

<details>
<summary>💡 Hint: El pipeline de CD falla</summary>

Errores comunes:
- **Token expirado:** Renueva el token de OpenShift y actualiza el secret en GitHub
- **Helm install falla:** Revisa si hay recursos del Fase 6 que no borraste. Limpia con `oc delete` y reintenta
- **Pods no arrancan:** `oc logs deployment/image-resizer-api` para ver el error
</details>

<details>
<summary>💡 Hint: El worker no procesa las tareas</summary>

Verifica:
1. `oc logs deployment/image-resizer-worker` - busca errores
2. `oc get pods` - el pod del worker debe estar Running
3. Verifica que Redis está Running: `oc logs deployment/redis`
4. Verifica que el ConfigMap tiene `REDIS_URL` correcta: `oc get configmap image-resizer-config -o yaml`
</details>

---

## 🎉 ¡Documento 1 Completado!

Has construido y desplegado un servicio completo con:

- ✅ API Flask para recibir imágenes
- ✅ Procesamiento asíncrono con Celery + Redis
- ✅ Almacenamiento de archivos en MinIO (S3-compatible)
- ✅ Base de datos PostgreSQL
- ✅ Containerización con Docker
- ✅ 5 deployments en Kubernetes/OpenShift
- ✅ Sealed Secrets (o concepto aprendido)
- ✅ Helm Chart parametrizable
- ✅ CI/CD automatizado con GitHub Actions
- ✅ Tests automatizados

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   📊 COMPARACIÓN CON EL URL SHORTENER                       │
│                                                             │
│   URL Shortener          Image Resizer                      │
│   ─────────────          ─────────────                      │
│   1 app service          2 servicios (API + Worker)         │
│   1 base de datos        1 BD + 1 Redis + 1 MinIO           │
│   Síncrono               Asíncrono (colas)                  │
│   Solo texto             Archivos binarios                  │
│   Secrets plaintext      Sealed Secrets                     │
│   2 deployments          5 deployments                      │
│                                                             │
│   ¡Has dado un salto grande! 🚀                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Siguiente paso: Documento 2

En el Documento 2 aprenderás:
- **Terraform + AWS:** Crear toda la infraestructura en AWS (VPC, EKS, S3, ElastiCache, RDS)
- **External Secrets:** AWS Secrets Manager + External Secrets Operator
- **ArgoCD:** GitOps, pasar de push-based a pull-based deploys
- **DevSecOps:** Trivy, Bandit, Checkov en el pipeline

¡Pide el Documento 2 cuando estés lista! 🎯
