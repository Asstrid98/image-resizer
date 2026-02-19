# 🖼️ Proyecto: Image Resizer — Documento 2, Parte B

## Fases 12-13: ArgoCD (GitOps) y DevSecOps

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ⚠️  ESTA PARTE NO REQUIERE AWS NI TARJETA DE CRÉDITO      │
│                                                             │
│   Fase 12 (ArgoCD): usa un cluster local con kind (gratis) │
│   Fase 13 (DevSecOps): corre en GitHub Actions (gratis)    │
│                                                             │
│   Solo necesitas: Docker Desktop, Git, y tu repo en GitHub. │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Contexto: ¿Qué pasó con las Fases 10-11 (Parte A)?

La Parte A del Documento 2 cubría Terraform + AWS (infraestructura cloud real: EKS, RDS, ElastiCache, S3, External Secrets). Esas fases requieren una cuenta de AWS con tarjeta de crédito y tienen coste real (~$30-45 por un lab de 3 días).

**Si decidiste no hacer la Parte A, no pasa nada.** Esta Parte B es completamente independiente. Todo funciona con tu código del Documento 1 sin tocar nada de AWS.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 LO QUE CUBRÍAN LAS FASES 10-11 (resumen conceptual)    │
│                                                             │
│   Fase 10: Terraform crea toda la infra en AWS              │
│   - VPC, subnets, NAT Gateway (red)                         │
│   - EKS (Kubernetes managed)                                │
│   - RDS (PostgreSQL managed, sin pod)                       │
│   - ElastiCache (Redis managed, sin pod)                    │
│   - S3 (almacenamiento, reemplaza MinIO)                    │
│   - ECR (registro Docker, reemplaza ghcr.io)                │
│   - IRSA (permisos de pod a servicios AWS)                  │
│                                                             │
│   Fase 11: External Secrets Operator                        │
│   - Secrets en AWS Secrets Manager (no en Git)              │
│   - El operador los sincroniza a Kubernetes                 │
│                                                             │
│   💡 Esto lo podrás hacer en el futuro si tienes acceso a   │
│   un cloud provider (trabajo, créditos de formación, etc.)  │
│   La Parte A queda como referencia para cuando la necesites.│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Lo que vas a hacer en esta Parte B:**

| Fase | Qué | Dónde corre | Coste |
|------|-----|-------------|-------|
| 12 | ArgoCD (GitOps) | Cluster local con `kind` | Gratis |
| 13 | DevSecOps (Trivy, Bandit, Checkov) | GitHub Actions | Gratis |

Tu punto de partida es el código exacto que tienes del Documento 1 (OpenShift). No necesitas haber cambiado nada.

---

## Fase 12: ArgoCD — GitOps

### 🎯 Objetivo
Cambiar de "push-based deploy" (GitHub Actions hace `helm upgrade` directamente al cluster) a "pull-based deploy" (ArgoCD detecta cambios en Git y sincroniza automáticamente).

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 PUSH vs PULL DEPLOY                                     │
│                                                             │
│   PUSH (lo que tienes ahora):                               │
│   Git push → CI tests → CI build → CD hace helm upgrade     │
│   GitHub Actions EMPUJA los cambios al cluster              │
│                                                             │
│   PULL (lo que vas a hacer):                                │
│   Git push → CI tests → CI build → CI actualiza Git         │
│   ArgoCD DETECTA el cambio en Git y sincroniza              │
│                                                             │
│   ¿POR QUÉ ES MEJOR?                                        │
│                                                             │
│   - Git es la fuente de verdad. SIEMPRE.                    │
│   - Si alguien cambia algo manualmente en el cluster,       │
│     ArgoCD lo detecta y lo revierte.                        │
│   - No necesitas dar credenciales del cluster al CI.        │
│   - Puedes ver el estado de TODO en el dashboard de ArgoCD. │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 ¿POR QUÉ NO EN OPENSHIFT SANDBOX?                      │
│                                                             │
│   ArgoCD necesita permisos de cluster-admin para instalar   │
│   CRDs (Custom Resource Definitions) y vigilar todos los    │
│   namespaces. El Sandbox solo te da un namespace limitado.  │
│                                                             │
│   Solución: usamos kind, un cluster K8s local que corre     │
│   dentro de Docker. Es gratuito, ligero, y tienes control   │
│   total. Perfecto para aprender.                            │
│                                                             │
│   En un trabajo real, ArgoCD lo instala el equipo de        │
│   plataforma en el cluster compartido. Tú solo configuras   │
│   la Application que apunta a tu repo.                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📝 Requisitos

1. **Docker Desktop** funcionando (ya lo tienes del Documento 1)
2. **kind** instalado:
   ```bash
   # Windows con Chocolatey:
   choco install kind

   # O descarga directa:
   # https://kind.sigs.k8s.io/docs/user/quick-start/#installation

   kind --version
   ```
3. **kubectl** instalado (ya lo tienes)
4. **Helm** instalado (ya lo tienes)

### 📝 Tareas

#### 12.1 Crear un cluster local con kind

```bash
# Crear un cluster (tarda ~1 minuto)
kind create cluster --name argocd-lab

# Verificar que funciona
kubectl cluster-info
kubectl get nodes
# Deberías ver 1 nodo en Ready
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 kind = Kubernetes IN Docker                             │
│                                                             │
│   Crea un cluster Kubernetes completo dentro de un          │
│   contenedor Docker. Tienes control total: puedes crear     │
│   namespaces, instalar CRDs, ser cluster-admin.             │
│                                                             │
│   No consume casi recursos cuando no lo usas.               │
│   Para borrarlo: kind delete cluster --name argocd-lab      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

<details>
<summary>💡 Hint: kind create cluster falla</summary>

- **Docker no está corriendo:** Abre Docker Desktop y espera a que esté listo.
- **"Cannot connect to the Docker daemon":** En Windows, verifica que Docker Desktop está en modo Linux containers, no Windows containers.
- **Puerto ocupado:** Si otro servicio usa el puerto 6443, kind lo detecta y usa otro. No debería dar error, pero si lo da, para otros clusters: `kind delete cluster --name <nombre>`.
</details>

#### 12.2 Instalar ArgoCD en kind

```bash
# Crear namespace para ArgoCD
kubectl create namespace argocd

# Instalar ArgoCD (fijando versión para que el lab sea reproducible)
ARGOCD_VERSION=v2.11.7
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml

# Esperar a que todos los pods estén listos (~2 minutos)
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s
```

### ✅ Checkpoint 12.2

```bash
kubectl -n argocd get pods
# Deberías ver 5-7 pods, todos Running o Completed
# Los importantes: argocd-server, argocd-repo-server, argocd-application-controller
```

<details>
<summary>💡 Hint: Los pods están en Pending o CrashLoopBackOff</summary>

- **Pending:** kind puede no tener suficientes recursos. Verifica en Docker Desktop que tienes al menos 4GB de RAM asignados a Docker (Settings → Resources).
- **CrashLoopBackOff:** Espera un poco más, algunos pods reinician mientras esperan a que otros estén listos. Si tras 5 minutos sigue igual:
  ```bash
  kubectl -n argocd logs deployment/argocd-server
  ```
- **ImagePullBackOff:** Tu internet puede estar lento o hay un problema de DNS. Reinicia Docker Desktop e inténtalo de nuevo.
</details>

#### 12.3 Acceder al Dashboard de ArgoCD

```bash
# Obtener la contraseña del admin
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
# Apunta la contraseña que muestra (es un string aleatorio)
echo  # (para que el prompt no quede pegado a la contraseña)

# Abrir un túnel para acceder al dashboard (deja esta terminal abierta)
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Ahora abre tu navegador en **https://localhost:8080**

- **Usuario:** `admin`
- **Contraseña:** la que apuntaste arriba

<details>
<summary>💡 Hint: El navegador dice "conexión no segura"</summary>

Es normal: ArgoCD usa un certificado auto-firmado para HTTPS. No es un problema de seguridad real porque estás en localhost.

- **Chrome:** Escribe `thisisunsafe` directamente en la página (no hay campo de texto visible, solo escribe y ya).
- **Firefox:** Haz clic en "Avanzado" → "Aceptar el riesgo y continuar".
- **Edge:** Igual que Chrome, escribe `thisisunsafe`.
</details>

<details>
<summary>💡 Hint: base64 -d no funciona en Windows</summary>

En PowerShell no existe `base64 -d`. Usa esto en su lugar:

```powershell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```

O usa Git Bash (que ya deberías tener) donde el comando original funciona.
</details>

#### 12.4 Instalar la CLI de ArgoCD

```bash
# Windows: descarga desde https://github.com/argoproj/argo-cd/releases
# Busca argocd-windows-amd64.exe y renómbralo a argocd.exe
# Muévelo a una carpeta en tu PATH (por ejemplo C:\tools\)

# Verificar
argocd version --client

# Login (usa la misma contraseña del paso anterior)
argocd login localhost:8080 --username admin --password TU-PASSWORD --insecure
```

#### 12.5 Conectar tu Repositorio

```bash
# Si tu repo es PRIVADO, añádelo con credenciales:
argocd repo add https://github.com/TU-USUARIO/image-resizer.git \
  --username TU-USUARIO \
  --password TU-GITHUB-TOKEN

# Si tu repo es PÚBLICO, ArgoCD puede leerlo sin credenciales.
# Puedes saltar este paso.
```

<details>
<summary>💡 Hint: ¿Cómo creo un GitHub Token?</summary>

1. Ve a GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Dale permisos: `repo` (acceso completo al repo)
4. Copia el token (solo lo verás una vez)

Usa ese token como password en el comando de arriba.
</details>

#### 12.6 Cargar la imagen Docker en kind

kind no puede hacer pull de ghcr.io tan fácilmente como un cluster real. Para este lab, cargamos la imagen directamente en el cluster:

```bash
# 1. Si tu imagen es pública:
docker pull ghcr.io/TU-USUARIO/image-resizer:latest

# Si tu imagen es privada, haz login primero:
echo TU-GITHUB-TOKEN | docker login ghcr.io -u TU-USUARIO --password-stdin
docker pull ghcr.io/TU-USUARIO/image-resizer:latest

# 2. Cargar la imagen en kind
kind load docker-image ghcr.io/TU-USUARIO/image-resizer:latest --name argocd-lab
```

<details>
<summary>💡 Hint: ¿Qué hace kind load docker-image?</summary>

kind corre Kubernetes dentro de un contenedor Docker. Las imágenes que tienes en tu Docker local NO están automáticamente disponibles dentro de kind. Este comando las "copia" al contenedor de kind para que Kubernetes pueda usarlas sin hacer pull de internet.

Cada vez que rebuildes la imagen, tienes que volver a hacer `kind load`.
</details>

#### 12.7 Adaptar la imagen de PostgreSQL para kind

La imagen de PostgreSQL que usamos en el Documento 1 (`image-registry.openshift-image-registry.svc:5000/openshift/postgresql:15-el9`) es interna de OpenShift y no existe fuera de él. Necesitas parametrizarla.

**Tu tarea:** Haz que la imagen de PostgreSQL sea configurable via values.

<details>
<summary>🔑 Solución: Modificar templates/postgresql.yaml</summary>

En `helm/image-resizer/templates/postgresql.yaml`, busca la línea de `image:` dentro del container y cámbiala por:

```yaml
          image: {{ .Values.postgresql.image | default "image-registry.openshift-image-registry.svc:5000/openshift/postgresql:15-el9" }}
```

Esto hace que:
- En OpenShift (sin definir `postgresql.image`): usa la imagen interna de OpenShift como antes.
- En kind (definiendo `postgresql.image`): usa la que le digas.
</details>

<details>
<summary>🔑 Solución: Adaptar las variables de entorno</summary>

La imagen oficial de PostgreSQL usa variables diferentes a la de OpenShift:

| OpenShift (postgresql:15-el9) | Docker oficial (postgres:15) |
|------|------|
| `POSTGRESQL_USER` | `POSTGRES_USER` |
| `POSTGRESQL_PASSWORD` | `POSTGRES_PASSWORD` |
| `POSTGRESQL_DATABASE` | `POSTGRES_DB` |

Para hacerlo compatible, modifica el Secret en `templates/postgresql.yaml`:

```yaml
stringData:
  {{- if contains "postgres:" (.Values.postgresql.image | default "") }}
  POSTGRES_USER: {{ .Values.postgresql.user }}
  POSTGRES_PASSWORD: {{ .Values.postgresql.password }}
  POSTGRES_DB: {{ .Values.postgresql.database }}
  {{- else }}
  POSTGRESQL_USER: {{ .Values.postgresql.user }}
  POSTGRESQL_PASSWORD: {{ .Values.postgresql.password }}
  POSTGRESQL_DATABASE: {{ .Values.postgresql.database }}
  {{- end }}
```

Y el mountPath del volumen también cambia: OpenShift usa `/var/lib/pgsql/data`, la imagen oficial usa `/var/lib/postgresql/data`. Parametrízalo igual:

```yaml
          volumeMounts:
            - name: postgresql-data
              mountPath: {{ .Values.postgresql.dataDir | default "/var/lib/pgsql/data" }}
```
</details>

#### 12.8 Crear values-kind.yaml

**Tu tarea:** Crea un archivo de valores adaptado para kind.

<details>
<summary>🔑 Solución</summary>

```yaml
# helm/image-resizer/values-kind.yaml
# Valores para el cluster local de kind (ArgoCD lab)

image:
  repository: ghcr.io/TU-USUARIO/image-resizer
  tag: "latest"
  pullPolicy: IfNotPresent  # Usa la imagen cargada con kind load

api:
  replicaCount: 1
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"
    limits:
      memory: "256Mi"
      cpu: "250m"

worker:
  replicaCount: 1
  concurrency: 2
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"
    limits:
      memory: "256Mi"
      cpu: "250m"

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
  storage: 512Mi
  rootUser: minioadmin
  rootPassword: minioadmin
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"
    limits:
      memory: "256Mi"
      cpu: "250m"

postgresql:
  enabled: true
  image: postgres:15
  storage: 512Mi
  user: image-resizer
  password: password123
  database: image-resizer
  dataDir: /var/lib/postgresql/data

service:
  type: ClusterIP
  port: 5000

# Sin Route (no estamos en OpenShift) ni Ingress (no hace falta en local)
route:
  enabled: false

ingress:
  enabled: false

config:
  baseUrl: "http://localhost:5000"
  storageBucket: "image-resizer"

probes:
  liveness:
    initialDelaySeconds: 30
    periodSeconds: 15
  readiness:
    initialDelaySeconds: 20
    periodSeconds: 10
```
</details>

Haz commit y push:

```bash
git add helm/image-resizer/values-kind.yaml
git add helm/image-resizer/templates/postgresql.yaml
git commit -m "feat: add values-kind.yaml and parametrize postgresql image"
git push
```

#### 12.9 Crear la Application de ArgoCD

Hay dos formas: via CLI o via manifiesto YAML. Vamos con el manifiesto porque es más GitOps (¡la config de ArgoCD también vive en Git!).

**Tu tarea:** Crea `argocd/application.yaml`

<details>
<summary>🔑 Solución</summary>

```yaml
# argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: image-resizer
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://github.com/TU-USUARIO/image-resizer.git
    targetRevision: main
    path: helm/image-resizer

    helm:
      valueFiles:
        - values-kind.yaml

  destination:
    server: https://kubernetes.default.svc
    namespace: default

  syncPolicy:
    automated:
      prune: true       # Borra recursos que ya no están en Git
      selfHeal: true     # Revierte cambios manuales en el cluster
    syncOptions:
      - CreateNamespace=true
```
</details>

```bash
# Aplica la Application
kubectl apply -f argocd/application.yaml

# Verifica en la CLI
argocd app list
argocd app get image-resizer
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 syncPolicy.automated                                    │
│                                                             │
│   prune: true → Si borras un recurso de Git, ArgoCD        │
│   lo borra del cluster. Si es false, lo deja huérfano.     │
│                                                             │
│   selfHeal: true → Si alguien hace kubectl edit y cambia   │
│   algo manualmente, ArgoCD lo revierte a lo que dice Git.  │
│                                                             │
│   Esto es la esencia de GitOps: Git es la ÚNICA verdad.    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### ✅ Checkpoint 12.9

```bash
argocd app get image-resizer
# Health Status:     Healthy (o Progressing si aún está arrancando)
# Sync Status:       Synced

kubectl get pods
# Deberías ver: api, worker, redis, minio, postgresql
```

También puedes verlo en el dashboard de ArgoCD (https://localhost:8080). Deberías ver la app `image-resizer` con todos sus recursos en verde.

<details>
<summary>💡 Hint: ArgoCD dice "OutOfSync" pero no sincroniza</summary>

1. `argocd app get image-resizer` — lee el detalle del estado
2. Si dice "ComparisonError": el chart Helm tiene errores de template. Prueba:
   ```bash
   helm template test helm/image-resizer/ -f helm/image-resizer/values-kind.yaml
   ```
3. Si dice "SyncError": `kubectl -n argocd get events --sort-by=.lastTimestamp`
4. Fuerza la sincronización: `argocd app sync image-resizer`
</details>

<details>
<summary>💡 Hint: Los pods están en ImagePullBackOff</summary>

En kind esto es normal si no cargaste la imagen. Solución:

```bash
kind load docker-image ghcr.io/TU-USUARIO/image-resizer:latest --name argocd-lab
argocd app sync image-resizer
```

Si usas `imagePullPolicy: Always`, Kubernetes intentará siempre hacer pull aunque la imagen esté cargada. Verifica que `values-kind.yaml` tiene `pullPolicy: IfNotPresent`.
</details>

<details>
<summary>💡 Hint: PostgreSQL crashea con permisos (permission denied)</summary>

La imagen oficial `postgres:15` necesita que el directorio de datos sea escribible. En kind esto puede fallar si el PVC no tiene los permisos correctos.

Solución rápida: quita el volumen de PostgreSQL para el lab (los datos no persisten entre reinicios, pero para aprender ArgoCD no importa):

```yaml
# En values-kind.yaml, desactiva el storage
postgresql:
  storage: ""
```

O añade un `securityContext` al template de postgresql si quieres hacerlo bien.
</details>

#### 12.10 Probar el self-heal de ArgoCD

Esta es la parte divertida. Vamos a demostrar que ArgoCD revierte cambios manuales.

```bash
# 1. Verifica que la app está Synced
argocd app get image-resizer
# Sync Status: Synced

# 2. Haz un cambio manual en el cluster (esto simula que alguien toca algo)
kubectl scale deployment image-resizer-api --replicas=5
# Acabas de cambiar las réplicas de 1 a 5

# 3. Mira los pods (verás 5 réplicas del API arrancando)
kubectl get pods -w
# Espera 10-20 segundos...

# 4. ArgoCD detecta la diferencia y revierte
# Volverás a ver solo 1 réplica (lo que dice Git)
kubectl get pods
# Solo 1 pod de API — ArgoCD revirtió tu cambio manual
```

Puedes ver esto en tiempo real en el dashboard de ArgoCD: la app cambiará brevemente a "OutOfSync" y luego vuelve a "Synced" cuando ArgoCD la repare.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 ESTO ES GITOPS EN ACCIÓN                                │
│                                                             │
│   Acabas de ver que ArgoCD garantiza que el cluster         │
│   siempre refleja lo que dice Git. Si alguien toca algo     │
│   manualmente (a propósito o por error), ArgoCD lo arregla. │
│                                                             │
│   En un equipo grande, esto evita el "pero a mí me         │
│   funciona" y el "¿quién tocó esto en producción?".         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 12.11 Adaptar el Pipeline CI/CD para GitOps

Ahora que ArgoCD hace el deploy, el pipeline de CD cambia:
- **CI (sin cambios):** Tests → Build → Push imagen a ghcr.io
- **CD (NUEVO):** Actualizar el tag de la imagen en `values-kind.yaml` y hacer commit

ArgoCD detectará el cambio en el archivo de values y sincronizará automáticamente.

**Tu tarea:** Crea `.github/workflows/cd-gitops.yml`

<details>
<summary>🔑 Solución</summary>

```yaml
# .github/workflows/cd-gitops.yml
name: CD (GitOps)

on:
  workflow_run:
    workflows: [CI]
    types: [completed]
    branches: [main]

concurrency:
  group: cd-gitops-${{ github.event.workflow_run.head_branch }}
  cancel-in-progress: true

jobs:
  update-manifests:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}

    permissions:
      contents: write

    steps:
      - name: Checkout branch
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          ref: ${{ github.event.workflow_run.head_branch }}

      - name: Set image tag
        run: |
          echo "IMAGE_TAG=$(echo '${{ github.event.workflow_run.head_sha }}' | cut -c1-7)" >> $GITHUB_ENV

      - name: Update values-kind.yaml with new image tag
        uses: mikefarah/yq@v4.44.3
        with:
          cmd: yq -i '.image.tag = strenv(IMAGE_TAG)' helm/image-resizer/values-kind.yaml

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add helm/image-resizer/values-kind.yaml
          git diff --staged --quiet || git commit -m "chore: update image tag to ${{ env.IMAGE_TAG }} [skip ci]"
          git push
```
</details>

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 EL FLUJO COMPLETO AHORA ES:                             │
│                                                             │
│   1. Haces push a main                                      │
│   2. CI: tests → build → push imagen a ghcr.io              │
│   3. CD: actualiza el tag en values-kind.yaml → commit      │
│   4. ArgoCD detecta el commit → sincroniza el cluster       │
│   5. Los pods se actualizan con la nueva imagen              │
│                                                             │
│   Nadie tiene credenciales del cluster excepto ArgoCD.      │
│   GitHub Actions solo hace push a Git y a ghcr.io.          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

<details>
<summary>💡 Hint: El commit del CD crea un loop infinito</summary>

Si CI se dispara con el commit del CD, y el CD se dispara con CI, tienes un loop. Para evitarlo:

1. **Barrera principal:** Este workflow hace push con `GITHUB_TOKEN`. Por defecto, los commits creados con ese token no disparan nuevos workflows.

2. **Barrera adicional recomendada:** Mantén `[skip ci]` en el mensaje del commit. Si en el futuro cambias a PAT/App token, esto evita ejecuciones innecesarias.

3. **Defensa extra:** En `ci.yml`, ignora cambios en la carpeta helm:
   ```yaml
   on:
     push:
       branches: [main]
       paths-ignore:
         - 'helm/**'
   ```
</details>

#### 12.12 Eliminar el CD antiguo

Ahora puedes eliminar o desactivar el pipeline de CD antiguo (`.github/workflows/cd.yml`) que hacía `helm upgrade` directamente contra OpenShift. Ya no lo necesitas.

```bash
# Opción 1: Bórralo
rm .github/workflows/cd.yml

# Opción 2: Renómbralo para guardarlo como referencia
mv .github/workflows/cd.yml .github/workflows/cd-push-based.yml.bak

git add -A
git commit -m "feat: replace push-based CD with GitOps CD"
git push
```

### ✅ Checkpoint Final de la Fase 12

1. Haz un cambio pequeño en tu app (por ejemplo, añade un comentario en `app/app.py`)
2. Haz commit y push a `main`
3. Ve a GitHub Actions → observa que CI corre y luego CD actualiza el tag
4. Ve al dashboard de ArgoCD (https://localhost:8080) → observa que detecta el cambio
5. Haz pull y carga la nueva imagen: `docker pull ghcr.io/TU-USUARIO/image-resizer:NUEVO-TAG` y luego `kind load docker-image ghcr.io/TU-USUARIO/image-resizer:NUEVO-TAG --name argocd-lab`
6. Los pods se recrean con la nueva imagen

```bash
argocd app get image-resizer
# Health Status:     Healthy
# Sync Status:       Synced

kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 NOTA SOBRE kind Y PRODUCCIÓN                            │
│                                                             │
│   En este lab, el ciclo no es 100% automático porque kind   │
│   necesita kind load para cargar imágenes nuevas.           │
│                                                             │
│   En un cluster real (EKS, GKE, AKS, OpenShift con         │
│   permisos), ArgoCD haría pull de la imagen automáticamente │
│   y el ciclo sería completamente hands-off.                 │
│                                                             │
│   Lo que importa aquí es que aprendas el PATRÓN:            │
│   Git → CI → actualiza values → ArgoCD sincroniza.          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 🧠 Qué debes saber explicar (Fase 12)

1. ¿Qué diferencia hay entre push-based deploy y pull-based deploy (GitOps)?
2. ¿Qué hace `selfHeal: true` en ArgoCD y por qué es importante?
3. Si CI hace un commit que actualiza el tag de la imagen, ¿cómo evitas un loop infinito de CI → CD → CI?

### 🔧 Troubleshooting: ArgoCD en kind

<details>
<summary>🔥 ArgoCD no puede clonar el repo (ComparisonError)</summary>

**Síntoma:** La app muestra `ComparisonError` en el dashboard.

**Causas comunes:**
1. **Repo privado sin credenciales:** Registra el repo con `argocd repo add` (paso 12.5).
2. **URL del repo incorrecta:** Verifica que la URL en `application.yaml` coincide exactamente con la URL de GitHub (con `.git` al final).
3. **Token expirado:** Regenera el token en GitHub y actualiza en ArgoCD:
   ```bash
   argocd repo rm https://github.com/TU-USUARIO/image-resizer.git
   argocd repo add https://github.com/TU-USUARIO/image-resizer.git \
     --username TU-USUARIO --password NUEVO-TOKEN
   ```
</details>

<details>
<summary>🔥 Port-forward se desconecta cada poco tiempo</summary>

**Síntoma:** `kubectl port-forward` se corta y tienes que re-ejecutarlo.

**Solución:**
```bash
# En Git Bash o terminal Unix-like:
while true; do kubectl port-forward svc/argocd-server -n argocd 8080:443 2>/dev/null; sleep 2; done

# En PowerShell:
while ($true) { kubectl port-forward svc/argocd-server -n argocd 8080:443 2>$null; Start-Sleep -Seconds 2 }
```
</details>

<details>
<summary>🔥 kind no tiene suficientes recursos (Pending pods)</summary>

**Síntoma:** `kubectl describe pod <nombre>` dice "Insufficient cpu" o "Insufficient memory".

**Solución:**
1. Verifica que Docker Desktop tiene al menos 4GB de RAM (Settings → Resources).
2. Reduce los recursos en `values-kind.yaml`:
   ```yaml
   api:
     resources:
       requests:
         memory: "64Mi"
         cpu: "25m"
       limits:
         memory: "128Mi"
         cpu: "125m"
   ```
3. Si sigue sin funcionar, desactiva minio temporalmente (`minio.enabled: false`) y prueba la app sin storage.
</details>

---

## Fase 13: DevSecOps

### 🎯 Objetivo
Añadir escaneo de seguridad al pipeline de CI: vulnerabilidades en la imagen Docker (Trivy), análisis de código Python (Bandit), y validación de manifiestos de Kubernetes (Checkov).

Todo corre en GitHub Actions. No necesitas ningún cluster ni servicio de pago.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 ¿QUÉ ES DEVSECOPS?                                     │
│                                                             │
│   DevOps + Seguridad integrada desde el principio.          │
│   No como algo que se hace "al final" o "si hay tiempo".    │
│                                                             │
│   En tu pipeline:                                           │
│   ┌─────┐ ┌──────┐ ┌───────┐ ┌─────┐ ┌──────┐ ┌─────────┐ │
│   │Test │→│Bandit│→│Checkov│→│Build│→│Push/Tag│→│Trivy  │ │
│   │     │ │(SAST)│ │ (K8s) │ │     │ │       │ │(scan) │ │
│   └─────┘ └──────┘ └───────┘ └─────┘ └──────┘ └─────────┘ │
│                                                             │
│   En esta guía empezamos en modo fail-open (visibilidad):   │
│   reporta hallazgos sin bloquear deploys.                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📝 Tareas

#### 13.1 Bandit — Análisis de seguridad del código Python

Bandit busca patrones inseguros en código Python: SQL injection, uso de `eval()`, passwords hardcodeados, etc.

```bash
# Instalar y probar localmente
pip install bandit

# Escanear tu código
bandit -r app/ -ll -ii
# -ll: solo medium y high severity
# -ii: solo medium y high confidence
```

**Tu tarea:** Ejecuta Bandit localmente y revisa lo que reporta. Luego añádelo al pipeline de CI.

<details>
<summary>🔑 Solución: Añadir al job test en ci.yml</summary>

```yaml
      # Después del paso "Run linter", añade:
      - name: Run security scan (Bandit)
        run: |
          pip install bandit
          bandit -r app/ -ll -ii -f json -o bandit-report.json || true
          bandit -r app/ -ll -ii
```
</details>

<details>
<summary>💡 Hint: Bandit reporta falsos positivos</summary>

Si Bandit reporta algo que no es un problema real (por ejemplo, el uso de `assert` en tests), puedes excluirlo:

```bash
# Excluir checks específicos
bandit -r app/ -ll -ii --skip B101

# O añadir un comentario en el código
password = os.getenv('DB_PASSWORD')  # nosec B105
```

Crea un archivo `.bandit` en la raíz para configurarlo:
```ini
[bandit]
exclude_dirs = tests
skips = B101
```
</details>

### ✅ Checkpoint 13.1

```bash
bandit -r app/ -ll -ii
# Revisa el reporte. Si hay issues, evalúa si son reales o falsos positivos.
```

---

#### 13.2 Checkov — Validación de manifiestos Kubernetes

Checkov escanea tus manifiestos de Kubernetes buscando malas prácticas de seguridad: pods sin limits, containers corriendo como root, images sin tag fijo, secrets en texto plano, etc.

```bash
# Instalar y probar localmente
pip install checkov

# Escanear los Helm templates renderizados
helm template my-release helm/image-resizer/ -f helm/image-resizer/values-kind.yaml > /tmp/k8s-rendered.yaml
checkov -f /tmp/k8s-rendered.yaml --framework kubernetes

# También puedes escanear los manifiestos estáticos de k8s/
checkov -d k8s/ --framework kubernetes
# Si tu repo no tiene carpeta k8s/, omite este comando.
```

**Tu tarea:** Ejecuta Checkov localmente, revisa los findings, y luego añádelo al pipeline.

<details>
<summary>🔑 Solución: Añadir un nuevo job a ci.yml</summary>

```yaml
  security-scan:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Checkov
        run: pip install checkov

      - name: Scan Kubernetes manifests (static)
        run: |
          if [ -d k8s ]; then
            checkov -d k8s/ \
              --framework kubernetes \
              --soft-fail \
              --output cli
          else
            echo "No existe k8s/; se omite scan estático."
          fi

      - name: Install Helm (pinned version)
        run: |
          HELM_VERSION=v3.15.4
          curl -fsSL -o /tmp/helm.tgz https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz
          tar -xzf /tmp/helm.tgz -C /tmp
          sudo mv /tmp/linux-amd64/helm /usr/local/bin/helm
          helm version --short

      - name: Render and scan Helm templates
        run: |
          helm template my-release helm/image-resizer/ \
            -f helm/image-resizer/values-kind.yaml > /tmp/rendered.yaml
          checkov -f /tmp/rendered.yaml \
            --framework kubernetes \
            --soft-fail \
            --output cli
```
</details>

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 ¿QUÉ ES --soft-fail?                                   │
│                                                             │
│   Con --soft-fail, Checkov reporta los problemas pero       │
│   NO falla el pipeline. Es útil al principio para ver       │
│   qué reporta sin bloquear tus deploys.                     │
│                                                             │
│   Cuando ya hayas corregido los problemas importantes,      │
│   quita --soft-fail para que falle si hay issues nuevos.    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

<details>
<summary>💡 Hint: Checkov reporta MUCHOS problemas</summary>

Es normal. La primera vez, Checkov encontrará decenas de issues. No tienes que arreglarlos todos. Prioriza:

1. **CRITICAL:** Containers corriendo como root, secrets en texto plano → Arregla estos.
2. **HIGH:** Falta de readiness/liveness probes, sin resource limits → Ya los tienes del Doc 1.
3. **MEDIUM/LOW:** Cosas como falta de networkPolicies, PodDisruptionBudgets → Bonus para el futuro.

Para excluir checks que has evaluado y no aplican:
```bash
checkov -f /tmp/rendered.yaml --skip-check CKV_K8S_40,CKV_K8S_35
```
</details>

### ✅ Checkpoint 13.2

```bash
helm template my-release helm/image-resizer/ -f helm/image-resizer/values-kind.yaml > /tmp/k8s-rendered.yaml
checkov -f /tmp/k8s-rendered.yaml --framework kubernetes
# Revisa el output. Intenta arreglar al menos 2-3 findings reales.
```

---

#### 13.3 Trivy — Escaneo de vulnerabilidades en imágenes Docker

Trivy busca vulnerabilidades conocidas (CVEs) en las dependencias de tu imagen Docker: librerías del OS, paquetes Python, etc.

**Tu tarea:** Añade Trivy al pipeline después del build de la imagen.

<details>
<summary>🔑 Solución: Añadir al job build en ci.yml</summary>

```yaml
      # Después del paso "Build and push", añade:
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@0.30.0
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          format: 'table'
          exit-code: '0'        # No falla el pipeline (cambiar a '1' cuando estés listo)
          severity: 'CRITICAL,HIGH'
          ignore-unfixed: true  # Solo muestra vulnerabilidades con fix disponible
```
</details>

<details>
<summary>💡 Hint: Trivy reporta vulnerabilidades en la imagen base</summary>

Si Trivy reporta CVEs en la imagen base (`python:3.11-slim`), tienes opciones:

1. **Ignorar las que no tienen fix:** Con `ignore-unfixed: true` solo ves las que puedes arreglar.
2. **Actualizar la imagen base:** Cambia a una versión más reciente en tu Dockerfile.
3. **Crear un `.trivyignore`** para vulnerabilidades que has evaluado y aceptas:
   ```
   # .trivyignore
   CVE-2023-XXXXX
   CVE-2024-YYYYY
   ```
</details>

<details>
<summary>💡 Hint: También puedes correr Trivy localmente</summary>

```bash
# Instalar Trivy en Windows con Chocolatey:
choco install trivy

# Escanear una imagen local
trivy image ghcr.io/TU-USUARIO/image-resizer:latest

# Solo CRITICAL y HIGH
trivy image --severity CRITICAL,HIGH ghcr.io/TU-USUARIO/image-resizer:latest

# Escanear el filesystem (dependencias sin buildear)
trivy fs --scanners vuln .
```
</details>

### ✅ Checkpoint 13.3

Haz push de tus cambios al CI y verifica que Trivy corre después del build. En GitHub Actions, deberías ver la tabla de vulnerabilidades en el log del step "Run Trivy vulnerability scanner".

---

### ✅ Pipeline CI Final Completo

Aquí tienes el pipeline CI completo con todas las fases de seguridad integradas:

<details>
<summary>🔑 Solución: ci.yml completo</summary>

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
    paths-ignore:
      - 'helm/**'

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

      - name: Run security scan (Bandit)
        run: |
          pip install bandit
          bandit -r app/ -ll -ii

  security-scan:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Scan Kubernetes manifests (static)
        run: |
          pip install checkov
          if [ -d k8s ]; then
            checkov -d k8s/ --framework kubernetes --soft-fail --output cli
          else
            echo "No existe k8s/; se omite scan estático."
          fi

      - name: Install Helm (pinned version)
        run: |
          HELM_VERSION=v3.15.4
          curl -fsSL -o /tmp/helm.tgz https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz
          tar -xzf /tmp/helm.tgz -C /tmp
          sudo mv /tmp/linux-amd64/helm /usr/local/bin/helm
          helm version --short

      - name: Scan Helm templates
        run: |
          helm template my-release helm/image-resizer/ \
            -f helm/image-resizer/values-kind.yaml > /tmp/rendered.yaml
          checkov -f /tmp/rendered.yaml --framework kubernetes --soft-fail --output cli

  build:
    runs-on: ubuntu-latest
    needs: [test, security-scan]
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

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@0.30.0
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          format: 'table'
          exit-code: '0'
          severity: 'CRITICAL,HIGH'
          ignore-unfixed: true
```
</details>

### ✅ Checkpoint Final de la Fase 13

1. Haz un commit y push
2. Ve a la pestaña Actions en GitHub
3. Deberías ver 3 jobs corriendo:
   - **test:** pytest + flake8 + bandit
   - **security-scan:** checkov (K8s manifests)
   - **build:** Docker build + push + Trivy scan (solo si test y security-scan pasan)
4. Después del build, el CD GitOps actualizará el tag en values-kind.yaml

### 🧠 Qué debes saber explicar (Fase 13)

1. ¿Qué diferencia hay entre Bandit (SAST) y Trivy (imagen scan)? ¿Qué tipo de problemas encuentra cada uno?
2. ¿Por qué empezamos con `--soft-fail` en Checkov y `exit-code: '0'` en Trivy?
3. Si Trivy encuentra una vulnerabilidad CRITICAL en `python:3.11-slim` pero no tiene fix disponible, ¿qué harías?

### 🧯 Errores comunes por sección (12.x y 13.x)

| Sección | Error típico | Comprobación rápida | Solución directa |
|---|---|---|---|
| 12.1 | `kind create cluster` falla | `docker info` | Arranca Docker Desktop y verifica modo Linux containers |
| 12.2 | ArgoCD no instala o pods no arrancan | `kubectl -n argocd get pods` | Reintenta con versión fija de ArgoCD y espera readiness |
| 12.3 | No abre dashboard / password no visible | `kubectl -n argocd get secret argocd-initial-admin-secret` | Usa comando alternativo en PowerShell y relanza `port-forward` |
| 12.4 | `argocd login` falla con TLS/conn | `argocd version --client` | Mantén `--insecure` en local y confirma `port-forward` activo |
| 12.5 | `ComparisonError` por repo privado | `argocd repo list` | Reañade repo con token válido y URL exacta (`.git`) |
| 12.6 | `ImagePullBackOff` en API/worker | `kubectl get pods` | `docker pull` + `kind load docker-image` + `argocd app sync` |
| 12.7 | PostgreSQL en crash por env/paths | `kubectl logs deploy/image-resizer-postgresql` | Revisa mapeo de variables `POSTGRES_*` y `dataDir` |
| 12.8 | `values-kind.yaml` no aplica bien | `helm template ... -f values-kind.yaml` | Corrige placeholders `TU-USUARIO`, `tag` y `pullPolicy: IfNotPresent` |
| 12.9 | App `OutOfSync` o `ComparisonError` | `argocd app get image-resizer` | Verifica `repoURL`, `path`, `targetRevision` y `valueFiles` |
| 12.10 | Self-heal no revierte cambios | `argocd app get image-resizer` | Confirma `syncPolicy.automated.selfHeal: true` |
| 12.11 | CD GitOps no actualiza tag | Revisa logs de `cd-gitops.yml` | Verifica permisos `contents: write`, paso `yq` y branch checkout |
| 12.12 | CD viejo interfiere con GitOps | Lista workflows activos en Actions | Elimina o desactiva `.github/workflows/cd.yml` |
| 13.1 | Bandit rompe CI por falsos positivos | `bandit -r app/ -ll -ii` | Configura `.bandit` o `--skip` para reglas justificadas |
| 13.2 | Checkov falla por falta de `k8s/` o Helm | `ls k8s && helm version` | Omite scan estático si no hay `k8s/` e instala Helm fijo |
| 13.3 | Trivy falla por imagen/tag inexistente | Verifica imagen en GHCR y tags del build | Usa tag correcto y acción pineada (`aquasecurity/trivy-action@0.30.0`) |

Si quieres llevarlo a modo estricto después de estabilizar:

- Quita `--soft-fail` en Checkov
- Cambia Trivy a `exit-code: '1'`

---

## 🎉 ¡Documento 2 Parte B Completado!

Has añadido capacidades de nivel profesional a tu proyecto:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   📊 LO QUE HAS AÑADIDO EN ESTA PARTE                       │
│                                                             │
│   Documento 1              Documento 2 Parte B              │
│   ────────────             ──────────────────               │
│   Push-based CD            GitOps con ArgoCD                │
│   (GitHub Actions →        (Git → ArgoCD sincroniza)        │
│    helm upgrade directo)                                    │
│                                                             │
│   Sin seguridad            DevSecOps completo               │
│                            • Bandit (código Python)         │
│                            • Checkov (manifiestos K8s)      │
│                            • Trivy (imagen Docker)          │
│                                                             │
│   ¡Ahora tienes un pipeline de CI/CD profesional! 🚀        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   🧹 LIMPIEZA                                                │
│                                                             │
│   Cuando termines de practicar con kind:                    │
│                                                             │
│   # Borrar el cluster de kind (libera los recursos)         │
│   kind delete cluster --name argocd-lab                     │
│                                                             │
│   # Verificar que se borró                                  │
│   kind get clusters                                         │
│   # No debe mostrar nada                                    │
│                                                             │
│   # Docker Desktop sigue funcionando normal                 │
│   # No se borra nada de tu repo ni de ghcr.io               │
│                                                             │
│   💡 Para volver a practicar, repite desde el paso 12.1     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### ¿Qué sigue?

Con los Documentos 1 y 2 (Parte B) completados, tienes experiencia en:

- ✅ Desarrollo de APIs (Flask, Python)
- ✅ Procesamiento asíncrono (Celery, Redis)
- ✅ Bases de datos (PostgreSQL, SQLAlchemy)
- ✅ Almacenamiento de objetos (MinIO)
- ✅ Containerización (Docker, multi-stage builds)
- ✅ Orquestación (Kubernetes, Helm)
- ✅ CI/CD (GitHub Actions)
- ✅ GitOps (ArgoCD)
- ✅ Gestión de Secrets (Sealed Secrets)
- ✅ DevSecOps (Trivy, Bandit, Checkov)
