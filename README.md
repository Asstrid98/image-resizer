# 🖼️ Proyecto: Image Resizer — Documento 2, Parte A

## Fases 10-11: Terraform + AWS y External Secrets

---

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   📋 RESUMEN DEL DOCUMENTO 2                                │
│                                                             │
│   Documento 1: App completa en OpenShift (✅ hecho)          │
│                                                             │
│   Documento 2 (este):                                       │
│   Fase 10: Terraform + AWS (VPC, EKS, RDS, S3, ElastiCache)│
│   Fase 11: External Secrets (AWS Secrets Manager)           │
│   Fase 12: ArgoCD (GitOps)                                  │
│   Fase 13: DevSecOps (Trivy, Bandit, Checkov)               │
│                                                             │
│   💡 ¿QUÉ CAMBIA?                                           │
│                                                             │
│   OpenShift Sandbox           →  AWS EKS                    │
│   PostgreSQL en pod           →  RDS (managed)              │
│   Redis en pod                →  ElastiCache (managed)      │
│   MinIO en pod                →  S3 (managed)               │
│   ghcr.io                     →  ECR (managed)              │
│   Sealed Secrets              →  External Secrets + SM      │
│   GitHub Actions push deploy  →  ArgoCD GitOps              │
│                                                             │
│   Ya no necesitas gestionar bases de datos ni colas.        │
│   AWS lo hace por ti. Tú solo gestionas tu app.             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Requisitos Previos

Antes de empezar necesitas:

1. **Cuenta de AWS** con acceso a la consola y credenciales (Access Key + Secret Key)
   - Si no tienes una, créala en [aws.amazon.com](https://aws.amazon.com). El free tier cubre parte de lo que usaremos, pero **EKS cuesta ~$0.10/hora** (~$73/mes). Planifica cuánto tiempo lo tendrás encendido.

2. **AWS CLI instalado:**
   ```bash
   # Windows (descarga el MSI):
   # https://awscli.amazonaws.com/AWSCLIV2.msi

   # Verificar
   aws --version

   # Configurar
   aws configure
   # → AWS Access Key ID: tu-access-key
   # → AWS Secret Access Key: tu-secret-key
   # → Default region: eu-west-1     (o la que prefieras)
   # → Default output format: json
   ```

3. **Terraform instalado:**
   ```bash
   # Windows: descarga desde https://developer.hashicorp.com/terraform/install
   # Extrae terraform.exe y muévelo a una carpeta en tu PATH

   terraform --version
   ```

4. **kubectl instalado:**
   ```bash
   # Windows: descarga desde https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/
   kubectl version --client
   ```

5. **Helm** (ya lo tienes del Documento 1)

6. **eksctl** (necesario para instalar el AWS Load Balancer Controller con IRSA)
   ```bash
   # Instalar en Windows (Chocolatey):
   choco install -y eksctl

   # Verificar
   eksctl version
   ```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ⚠️  IMPORTANTE: COSTES DE AWS                              │
│                                                             │
│   EKS:           ~$0.10/hora ($73/mes)                      │
│   NAT Gateway:   ~$0.045/hora ($32/mes)                     │
│   RDS t3.micro:  ~$0.02/hora ($14/mes)                      │
│   ElastiCache:   ~$0.02/hora ($14/mes)                      │
│   Nodos EC2:     ~$0.10/hora ($72/mes) con 2 x t3.medium    │
│                                                             │
│   Total aproximado: ~$205/mes si lo dejas 24/7              │
│                                                             │
│   💡 TRUCO: Cuando NO estés practicando, haz                │
│   terraform destroy para parar todo. Luego                  │
│   terraform apply para levantarlo de nuevo.                 │
│   Así solo pagas las horas que usas.                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ¿Es indispensable pagar para hacer este proyecto?

Respuesta corta:
- Para **este Documento 2**, **sí**, necesitas AWS real (EKS/RDS/ElastiCache gestionados).
- En la práctica: o aprovechas créditos/free tier temporal si aplica, o tendrás que pagar las horas de laboratorio.

Puntos clave:
- EKS tiene coste por cluster/hora aunque no tengas tráfico.
- NAT Gateway tiene coste por hora y por GB procesado.
- Cuentas nuevas de AWS (desde el 15 de julio de 2025) pueden usar plan gratis temporal y hasta $200 en créditos, pero **no garantiza laboratorio gratis indefinido**.
- Lo más seguro es asumir que habrá coste y planificarlo desde el inicio.

### Presupuesto orientativo (ventana 3 días)

Estimación rápida con los números de esta guía:
- Coste base aproximado por hora encendido: `0.10 + 0.045 + 0.02 + 0.02 + 0.10 = 0.285 USD/h`
- Ventana de 72 horas (3 días): `0.285 x 72 = 20.52 USD`
- Recomendación realista para laboratorio: reserva entre **30 y 45 USD** por margen (almacenamiento, transferencias y reintentos).

### Recomendación para Taylinn (muy junior)

Como el Documento 1 ya cubrió la parte local/gratuita, en este Documento 2 recomendamos:
1. Preparar todo antes de encender infraestructura (código, comandos y checklist listos).
2. Ejecutar AWS en una **ventana corta de máximo 3 días** con recursos levantados.
3. Al terminar cada sesión, apagar con `terraform destroy` para no acumular coste.
4. Si algo falla, depurar rápido con los bloques de troubleshooting y volver a destruir.

Esto mantiene el objetivo didáctico sin esconder el coste real de AWS.
Documento 2 es un laboratorio AWS real: el objetivo es aprender operación cloud con coste controlado, no forzar coste cero.

### Plan sugerido (3 días)

1. Día 1: Fases 10.0 a 10.5 (network + EKS + acceso con kubectl).
2. Día 2: Fases 10.6 a 10.12 (RDS, Redis, S3, ECR y despliegue completo).
3. Día 3: Fase 11 (External Secrets), troubleshooting guiado y cierre con `terraform destroy`.

### Checklist antes de encender AWS

1. Credenciales AWS válidas: `aws sts get-caller-identity`.
2. Región definida y consistente en `terraform.tfvars`, `backend.tf` y comandos CLI.
3. Variables y secretos preparados (`db_password`, nombres de recursos, namespace).
4. Comandos de la fase copiados en un bloc para ejecutar sin improvisar.
5. Tiempo reservado para terminar y destruir infraestructura en la misma sesión.

### Glosario rápido (sin tecnicismos)

- **IaC (Infrastructure as Code):** definir infraestructura en archivos (en vez de clics en consola).
- **VPC:** tu red privada dentro de AWS.
- **Subnet:** una "subzona" dentro de esa red.
- **Internet Gateway:** salida/entrada a internet para subnets públicas.
- **NAT Gateway:** salida a internet para subnets privadas (sin exponerlas).
- **Security Group:** firewall de AWS (quién puede hablar con quién y por qué puerto).
- **IAM Role:** permisos temporales para servicios/pods.
- **IRSA:** forma de dar permisos AWS a un pod usando su ServiceAccount.
- **OIDC:** mecanismo de identidad que permite a Kubernetes "demostrar quién es" ante AWS.
- **Ingress:** puerta HTTP/HTTPS de entrada al cluster.
- **ExternalSecret:** recurso que copia secrets desde un gestor externo a Kubernetes.

### Cómo estudiar esta guía (modo junior)

En cada fase:
1. Lee primero el **Objetivo**.
2. Ejecuta solo la **Tarea** de esa subsección.
3. Pasa el **Checkpoint** antes de avanzar.
4. Si falla, ve al bloque **Troubleshooting** de esa fase (sin saltar pasos).
5. Apunta lo aprendido en 3 líneas: qué hiciste, qué falló, cómo lo arreglaste.
6. Si un comando falla, anota el error exacto y tu hipótesis antes de probar el siguiente cambio.

Si quieres, al final de cada fase puedes pedirle a otra persona que te haga 3 preguntas rápidas para reforzar conceptos.

---

## Fase 10: Terraform + AWS

### 🎯 Objetivo
Crear toda la infraestructura en AWS con Terraform: red, cluster de Kubernetes, base de datos, caché, almacenamiento y registro de imágenes Docker.

```
┌─────────────────────────────────────────────────────────────────────┐
│                           AWS CLOUD                                 │
│                                                                     │
│  ┌───────────────────── VPC (10.0.0.0/16) ───────────────────────┐  │
│  │                                                                │  │
│  │  ┌─── Public Subnets ───┐    ┌─── Private Subnets ──────────┐ │  │
│  │  │                      │    │                               │ │  │
│  │  │  ALB (Load Balancer) │    │  EKS Nodes                   │ │  │
│  │  │  NAT Gateway         │    │  ┌─────┐ ┌────────┐          │ │  │
│  │  │                      │    │  │ API │ │ Worker │          │ │  │
│  │  └──────────────────────┘    │  └──┬──┘ └───┬────┘          │ │  │
│  │                              │     │        │               │ │  │
│  │                              │     ▼        ▼               │ │  │
│  │                              │  ┌──────┐ ┌──────┐ ┌──────┐ │ │  │
│  │                              │  │ RDS  │ │Redis │ │  S3  │ │ │  │
│  │                              │  │Postgr│ │Cache │ │Bucket│ │ │  │
│  │                              │  └──────┘ └──────┘ └──────┘ │ │  │
│  │                              └──────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─── ECR ─────┐  ┌── S3 (tfstate) ──┐  ┌── Secrets Manager ──┐   │
│  │ Docker imgs  │  │ Terraform state  │  │ DB passwords, keys  │   │
│  └──────────────┘  └─────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 📝 Tareas

#### 10.0 Estructura del directorio Terraform

Crea esta estructura en tu repo:

```
terraform/
├── main.tf              # Provider y configuración general
├── variables.tf         # Variables de entrada
├── outputs.tf           # Valores de salida
├── vpc.tf               # Red (VPC, subnets, NAT, IGW)
├── eks.tf               # Cluster de Kubernetes
├── rds.tf               # Base de datos PostgreSQL
├── elasticache.tf       # Redis
├── s3.tf                # Bucket para imágenes
├── ecr.tf               # Registro de imágenes Docker
├── security-groups.tf   # Reglas de firewall
├── iam.tf               # Permisos
├── terraform.tfvars     # Valores de las variables (NO commitear)
└── backend.tf           # Configuración del state remoto
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 ¿POR QUÉ TANTOS ARCHIVOS?                              │
│                                                             │
│   En Terraform, puedes meter todo en un solo main.tf.       │
│   Pero en la vida real se separa por recurso para que       │
│   sea más fácil de leer y mantener. Igual que separas       │
│   los manifiestos de K8s por componente.                    │
│                                                             │
│   Terraform lee TODOS los .tf de la carpeta y los junta     │
│   automáticamente. El nombre del archivo no importa,        │
│   es solo organización para humanos.                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 10.1 State Remoto — `backend.tf`

Antes de crear nada, necesitas un sitio donde Terraform guarde su estado. Por defecto lo guarda en un archivo local (`terraform.tfstate`), pero eso tiene problemas: si lo pierdes, Terraform no sabe qué recursos existen; si trabajan dos personas, se pisan.

**Tu tarea:** Crea un bucket S3 y una tabla DynamoDB para el state. Esto se hace UNA VEZ manualmente porque Terraform necesita ese backend antes de poder usarlo.

```bash
# Crear el bucket para el state (el nombre debe ser único globalmente)
aws s3 mb s3://image-resizer-tfstate-TUNOMBRE --region eu-west-1

# Activar versionado (para poder recuperar states anteriores)
aws s3api put-bucket-versioning \
  --bucket image-resizer-tfstate-TUNOMBRE \
  --versioning-configuration Status=Enabled

# Crear tabla DynamoDB para locking (evita que dos personas apliquen a la vez)
aws dynamodb create-table \
  --table-name image-resizer-tflock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1
```

Ahora crea el archivo:

```hcl
# terraform/backend.tf
terraform {
  backend "s3" {
    bucket         = "image-resizer-tfstate-TUNOMBRE"
    key            = "image-resizer/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "image-resizer-tflock"
    encrypt        = true
  }
}
```

<details>
<summary>💡 Hint: ¿Qué pasa si me equivoco en el nombre del bucket?</summary>

Si te equivocas, puedes cambiar el nombre en `backend.tf` y ejecutar `terraform init -reconfigure`. Terraform moverá el state al nuevo bucket.
Si ya existe state en el backend anterior, usa `terraform init -migrate-state` para migrarlo correctamente.

Si aún no has hecho `terraform init`, simplemente corrige el nombre y listo.
</details>

#### 10.2 Provider y Variables — `main.tf` y `variables.tf`

**Tu tarea:** Configura el provider de AWS y define las variables que usaremos en todo el proyecto.

<details>
<summary>🔑 Solución: main.tf</summary>

```hcl
# terraform/main.tf
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "image-resizer"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```
</details>

<details>
<summary>🔑 Solución: variables.tf</summary>

```hcl
# terraform/variables.tf
variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Entorno (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "image-resizer"
}

variable "k8s_namespace" {
  description = "Namespace de Kubernetes donde desplegarás la app"
  type        = string
  default     = "default"
}

variable "vpc_cidr" {
  description = "CIDR block de la VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "db_username" {
  description = "Usuario de la base de datos"
  type        = string
  default     = "imageresizer"
}

variable "db_password" {
  description = "Contraseña de la base de datos"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Nombre de la base de datos"
  type        = string
  default     = "imageresizer"
}
```
</details>

<details>
<summary>🔑 Solución: terraform.tfvars</summary>

```hcl
# terraform/terraform.tfvars
# ⚠️ NO COMMITEAR ESTE ARCHIVO - añádelo a .gitignore
aws_region  = "eu-west-1"
environment = "dev"
db_password = "CambiameP0rAlgoSeguro!"
# k8s_namespace = "default"
```
</details>

**Actualiza `.gitignore`** para que no se commitee:
```
# Terraform
terraform/.terraform/
terraform/*.tfstate
terraform/*.tfstate.backup
terraform/terraform.tfvars
```

No ignores `terraform/.terraform.lock.hcl`; conviene versionarlo para fijar versiones de providers.

#### 10.3 VPC — `vpc.tf`

La VPC es la red privada donde vivirá todo. Necesitas:
- 2 subnets públicas (para el load balancer y NAT Gateway)
- 2 subnets privadas (para EKS, RDS y ElastiCache)
- Un Internet Gateway (para que las subnets públicas tengan internet)
- Un NAT Gateway (para que las subnets privadas tengan internet de salida)

**Tu tarea:** Crea la VPC con 2 AZs, 2 subnets públicas y 2 privadas.

<details>
<summary>💡 Pista: ¿Por qué 2 de cada?</summary>

AWS exige mínimo 2 Availability Zones para EKS y RDS. Es requisito, no opción.

```
eu-west-1a                    eu-west-1b
┌──────────────────┐          ┌──────────────────┐
│ public-1         │          │ public-2         │
│ 10.0.1.0/24      │          │ 10.0.2.0/24      │
├──────────────────┤          ├──────────────────┤
│ private-1        │          │ private-2        │
│ 10.0.11.0/24     │          │ 10.0.12.0/24     │
└──────────────────┘          └──────────────────┘
```
</details>

<details>
<summary>🔑 Solución: vpc.tf</summary>

```hcl
# terraform/vpc.tf

# --- Availability Zones ---
data "aws_availability_zones" "available" {
  state = "available"
}

# --- VPC ---
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# --- Internet Gateway ---
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# --- Subnets Públicas ---
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                                          = "${var.project_name}-public-${count.index + 1}"
    "kubernetes.io/role/elb"                       = "1"
    "kubernetes.io/cluster/${var.project_name}-eks" = "shared"
  }
}

# --- Subnets Privadas ---
resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 11}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name                                          = "${var.project_name}-private-${count.index + 1}"
    "kubernetes.io/role/internal-elb"              = "1"
    "kubernetes.io/cluster/${var.project_name}-eks" = "shared"
  }
}

# --- NAT Gateway (para que los nodos privados tengan internet) ---
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-nat-eip"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${var.project_name}-nat"
  }

  depends_on = [aws_internet_gateway.main]
}

# --- Route Tables ---
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-private-rt"
  }
}

# --- Asociar subnets a route tables ---
resource "aws_route_table_association" "public" {
  count = 2

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = 2

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
```
</details>

### ✅ Checkpoint 10.3

```bash
cd terraform/

# Inicializar Terraform (descarga el provider de AWS)
terraform init

# Ver qué va a crear
terraform plan

# Deberías ver ~12 recursos: VPC, IGW, 4 subnets, NAT, EIP, 2 route tables, 2 associations
```

<details>
<summary>💡 Hint: terraform init falla</summary>

- Verifica que tienes credenciales de AWS: `aws sts get-caller-identity`
- Si falla por el backend S3, asegúrate de que creaste el bucket y la tabla DynamoDB
- Si quieres trabajar sin backend remoto temporalmente, comenta el bloque `backend "s3"` en `backend.tf`
</details>

---

#### 10.4 Security Groups — `security-groups.tf`

**Tu tarea:** Crea los security groups (firewalls) para RDS y ElastiCache.
El cluster EKS ya crea su propio **cluster security group**; usaremos ese SG como origen permitido para DB y Redis.
Piensa en un security group como una lista de "permitidos": si no está permitido, se bloquea.
Este archivo referencia `aws_eks_cluster.main`, asi que valida con `terraform plan` despues de completar la Fase 10.5.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 SECURITY GROUPS = FIREWALLS DE AWS                      │
│                                                             │
│   Cada recurso tiene un SG que dice qué tráfico entra      │
│   y qué sale. La regla de oro: solo abrir lo necesario.     │
│                                                             │
│   EKS Cluster SG → puede hablar con RDS (5432) y Redis     │
│   RDS → solo acepta tráfico desde el SG del cluster EKS    │
│   ElastiCache → solo acepta tráfico desde SG del cluster   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

<details>
<summary>🔑 Solución: security-groups.tf</summary>

```hcl
# terraform/security-groups.tf

# Lo crea EKS al provisionar el cluster. Lo usamos como origen permitido
# para RDS y ElastiCache, asi evitamos SGs huerfanos no asociados a nodos.
locals {
  eks_cluster_security_group_id = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

# --- SG para RDS ---
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.main.id

  # Solo acepta tráfico desde el cluster security group de EKS
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [local.eks_cluster_security_group_id]
    description     = "PostgreSQL from EKS cluster security group"
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# --- SG para ElastiCache ---
resource "aws_security_group" "elasticache" {
  name_prefix = "${var.project_name}-redis-"
  description = "Security group for ElastiCache Redis"
  vpc_id      = aws_vpc.main.id

  # Solo acepta tráfico desde el cluster security group de EKS
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [local.eks_cluster_security_group_id]
    description     = "Redis from EKS cluster security group"
  }

  tags = {
    Name = "${var.project_name}-redis-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}
```
</details>

#### 10.5 EKS — `eks.tf` e `iam.tf`

El EKS es el Kubernetes de AWS. Necesita dos cosas: un cluster (control plane, el "cerebro" que coordina Kubernetes) y un node group (las máquinas donde corren tus pods).

**Tu tarea:** Crea el cluster EKS con un node group de 2 nodos t3.medium.

<details>
<summary>💡 Pista: IAM Roles para EKS</summary>

EKS necesita 2 roles de IAM:
1. **Cluster role:** Permite a EKS gestionar recursos de AWS
2. **Node role:** Permite a los nodos unirse al cluster, pull de ECR, etc.

Son muchas líneas, pero es un bloque estándar que casi no cambia entre proyectos. No te asustes: normalmente se copia y se ajusta lo mínimo.
</details>

<details>
<summary>🔑 Solución: iam.tf</summary>

```hcl
# terraform/iam.tf

# ========================================
# IAM Role para el Cluster EKS
# ========================================
resource "aws_iam_role" "eks_cluster" {
  name = "${var.project_name}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

# ========================================
# IAM Role para los Nodos EKS
# ========================================
resource "aws_iam_role" "eks_nodes" {
  name = "${var.project_name}-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "ecr_read_only" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

# ========================================
# IAM Role para pods que acceden a S3 (IRSA)
# ========================================
data "aws_iam_policy_document" "s3_access" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.images.arn,
      "${aws_s3_bucket.images.arn}/*"
    ]
  }
}

resource "aws_iam_policy" "s3_access" {
  name   = "${var.project_name}-s3-access"
  policy = data.aws_iam_policy_document.s3_access.json
}

# El IRSA (IAM Roles for Service Accounts) se configura después
# de crear el cluster, en la Fase 10.9
```
</details>

<details>
<summary>🔑 Solución: eks.tf</summary>

```hcl
# terraform/eks.tf

# --- Cluster EKS ---
resource "aws_eks_cluster" "main" {
  name     = "${var.project_name}-eks"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.31"

  vpc_config {
    subnet_ids = concat(
      aws_subnet.public[*].id,
      aws_subnet.private[*].id
    )
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
  ]

  tags = {
    Name = "${var.project_name}-eks"
  }
}

# --- Node Group ---
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.project_name}-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  instance_types = ["t3.medium"]

  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 1
  }

  update_config {
    max_unavailable = 1
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.ecr_read_only,
  ]

  tags = {
    Name = "${var.project_name}-node-group"
  }
}
```
</details>

### ✅ Checkpoint 10.5

```bash
# Ver el plan (ahora deberías ver VPC + EKS + IAM)
terraform plan

# Si todo se ve bien, aplica (EKS tarda 10-15 minutos)
terraform apply

# Cuando termine, configura kubectl:
EKS_CLUSTER_NAME="image-resizer-eks"  # Si cambiaste project_name, ajusta este valor
AWS_REGION="eu-west-1"                # Debe coincidir con aws_region en terraform.tfvars
aws eks update-kubeconfig --name "$EKS_CLUSTER_NAME" --region "$AWS_REGION"

# Verifica
kubectl get nodes
# Deberías ver 2 nodos en Ready
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ⏱️  EKS TARDA ~15 MINUTOS EN CREARSE                      │
│                                                             │
│   Es normal. AWS está provisionando el control plane y      │
│   los nodos. Aprovecha para ir leyendo las siguientes       │
│   fases mientras esperas.                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

<details>
<summary>💡 Hint: terraform apply falla por permisos</summary>

Tu usuario de AWS necesita permisos amplios para crear EKS. Si usas un usuario con permisos limitados, necesita como mínimo estas políticas:
- AmazonEKSClusterPolicy
- AmazonEKSServicePolicy
- IAMFullAccess (para crear los roles)
- AmazonVPCFullAccess
- AmazonEC2FullAccess

Lo más fácil para aprender es usar un usuario con `AdministratorAccess` y luego restringir cuando sepas qué necesitas.
</details>

<details>
<summary>💡 Hint: terraform apply falla con "Error creating EKS Cluster: UnsupportedAvailabilityZoneException"</summary>

No todas las Availability Zones soportan EKS. Puede pasar en algunas regiones. Solución:

```hcl
# En vpc.tf, filtra las AZs problemáticas:
data "aws_availability_zones" "available" {
  state = "available"
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}
```

Si sigue fallando, prueba otra región (por ejemplo `eu-west-2` o `us-east-1`). Cambia `aws_region` en `terraform.tfvars` y `backend.tf`.
</details>

<details>
<summary>💡 Hint: "Error creating EKS Cluster: ResourceInUseException" o nombres duplicados</summary>

Si hiciste un `terraform destroy` parcial o fallido, puede que queden recursos huérfanos en AWS. Ve a la consola de AWS, busca el recurso que da conflicto (por nombre) y bórralo manualmente. Luego reintenta `terraform apply`.

También puedes forzar que Terraform olvide el recurso:
```bash
terraform state rm aws_eks_cluster.main
```
</details>

<details>
<summary>💡 Hint: kubectl get nodes no muestra nodos</summary>

Causas posibles:
1. **kubeconfig no configurado:** Ejecuta `aws eks update-kubeconfig --name <tu-cluster> --region <tu-region>` de nuevo.
2. **El node group aún se está creando:** Puede tardar 5-10 minutos después del cluster. Mira el estado en la consola de AWS → EKS → Clusters → image-resizer-eks → Compute.
3. **Los nodos no pueden unirse al cluster:** Verifica que los nodos están en las subnets privadas y que el NAT Gateway está activo. Sin NAT, los nodos no pueden descargar las imágenes de los componentes de EKS.

```bash
# Ver estado del node group
aws eks describe-nodegroup --cluster-name <tu-cluster> --nodegroup-name <tu-nodegroup> --query "nodegroup.status"

# Si dice "CREATE_FAILED", lee el motivo:
aws eks describe-nodegroup --cluster-name <tu-cluster> --nodegroup-name <tu-nodegroup> --query "nodegroup.health"
```
</details>

<details>
<summary>💡 Hint: kubectl da "error: exec plugin is configured to use API version client.authentication.k8s.io/v1alpha1"</summary>

Tu versión de aws-cli es antigua. Actualízala:
```bash
# Windows: descarga el nuevo MSI desde https://awscli.amazonaws.com/AWSCLIV2.msi
# Verifica que tienes v2:
aws --version
# Debe ser aws-cli/2.x.x
```
</details>

---

#### 10.6 RDS PostgreSQL — `rds.tf`

Ya no necesitas un pod de PostgreSQL. AWS lo gestiona por ti.

**Tu tarea:** Crea una instancia RDS PostgreSQL.

<details>
<summary>🔑 Solución: rds.tf</summary>

```hcl
# terraform/rds.tf

# --- Subnet Group (RDS necesita saber en qué subnets puede vivir) ---
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

# --- RDS PostgreSQL ---
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-db"

  engine         = "postgres"
  engine_version = "16.4"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_type          = "gp3"

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  # Para dev: no multi-AZ, backup básico
  multi_az               = false
  backup_retention_period = 7
  skip_final_snapshot    = true

  tags = {
    Name = "${var.project_name}-db"
  }
}
```
</details>

#### 10.7 ElastiCache Redis — `elasticache.tf`

Lo mismo con Redis. AWS lo gestiona.

**Tu tarea:** Crea un cluster ElastiCache Redis.

<details>
<summary>🔑 Solución: elasticache.tf</summary>

```hcl
# terraform/elasticache.tf

# --- Subnet Group para ElastiCache ---
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-redis-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-redis-subnet-group"
  }
}

# --- ElastiCache Redis ---
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "${var.project_name}-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.elasticache.id]

  tags = {
    Name = "${var.project_name}-redis"
  }
}
```
</details>

#### 10.8 S3 y ECR — `s3.tf` y `ecr.tf`

S3 reemplaza a MinIO. ECR reemplaza a ghcr.io.

**Tu tarea:** Crea el bucket S3 para imágenes y el repositorio ECR para las imágenes Docker.

<details>
<summary>🔑 Solución: s3.tf</summary>

```hcl
# terraform/s3.tf

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "images" {
  # El nombre debe ser globalmente unico en AWS
  bucket = "${var.project_name}-images-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-images"
  }
}

resource "aws_s3_bucket_versioning" "images" {
  bucket = aws_s3_bucket.images.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Bloquear acceso público (las imágenes se acceden via presigned URLs)
resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```
</details>

<details>
<summary>🔑 Solución: ecr.tf</summary>

```hcl
# terraform/ecr.tf

resource "aws_ecr_repository" "main" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-ecr"
  }
}

# Política de limpieza: mantener solo las últimas 10 imágenes
resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}
```
</details>

#### 10.9 IRSA y Outputs — `iam.tf` (continuación) y `outputs.tf`

IRSA (IAM Roles for Service Accounts) permite que tus pods accedan a S3 sin hardcodear credenciales.

**Tu tarea:** Configura IRSA y crea los outputs.

<details>
<summary>💡 Pista: ¿Qué es IRSA?</summary>

En OpenShift, tus pods accedían a MinIO con usuario/contraseña (STORAGE_ACCESS_KEY/SECRET_KEY). En AWS, la forma correcta es que el pod tenga un IAM Role asociado a su ServiceAccount de Kubernetes. Así no necesitas ninguna credencial en el pod.

```
Pod → ServiceAccount → IAM Role → permiso para S3
```
</details>

<details>
<summary>🔑 Solución: Añadir a iam.tf</summary>

```hcl
# Añadir al final de terraform/iam.tf

# --- OIDC Provider para IRSA ---
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

# --- IAM Role para el ServiceAccount de la app ---
resource "aws_iam_role" "app_role" {
  name = "${var.project_name}-app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.eks.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:${var.k8s_namespace}:image-resizer-sa"
          "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "app_s3_access" {
  policy_arn = aws_iam_policy.s3_access.arn
  role       = aws_iam_role.app_role.name
}
```
</details>

<details>
<summary>🔑 Solución: outputs.tf</summary>

```hcl
# terraform/outputs.tf

output "eks_cluster_name" {
  description = "Nombre del cluster EKS"
  value       = aws_eks_cluster.main.name
}

output "aws_region" {
  description = "Region de AWS usada por Terraform"
  value       = var.aws_region
}

output "eks_cluster_endpoint" {
  description = "Endpoint del API server de EKS"
  value       = aws_eks_cluster.main.endpoint
}

output "rds_endpoint" {
  description = "Endpoint de RDS PostgreSQL"
  value       = aws_db_instance.main.endpoint
}

output "redis_endpoint" {
  description = "Endpoint de ElastiCache Redis"
  value       = "${aws_elasticache_cluster.main.cache_nodes[0].address}:${aws_elasticache_cluster.main.cache_nodes[0].port}"
}

output "s3_bucket_name" {
  description = "Nombre del bucket S3"
  value       = aws_s3_bucket.images.bucket
}

output "ecr_repository_url" {
  description = "URL del repositorio ECR"
  value       = aws_ecr_repository.main.repository_url
}

output "app_role_arn" {
  description = "ARN del IAM Role para los pods"
  value       = aws_iam_role.app_role.arn
}

output "database_url" {
  description = "Connection string de la base de datos"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/${var.db_name}"
  sensitive   = true
}
```
</details>

### ✅ Checkpoint 10.9 — Despliegue Completo de Infraestructura

```bash
# Plan final (deberías ver ~25-30 recursos)
terraform plan

# Aplica TODO (tardará ~15-20 minutos)
terraform apply

# Cuando termine, verifica:
terraform output

# Configura kubectl para el cluster EKS
AWS_REGION=$(terraform output -raw aws_region)
EKS_CLUSTER_NAME=$(terraform output -raw eks_cluster_name)
aws eks update-kubeconfig --name "$EKS_CLUSTER_NAME" --region "$AWS_REGION"

# Verifica que tienes acceso
kubectl get nodes
kubectl get namespaces
```

<details>
<summary>💡 Hint: terraform apply falla a mitad de camino</summary>

Si falla a mitad:
1. **No entres en pánico.** Terraform recuerda qué ya creó.
2. Lee el error. Normalmente es un problema de permisos o un nombre duplicado.
3. Arregla el error y vuelve a ejecutar `terraform apply`. Solo creará lo que falta.
4. Si quieres empezar de cero: `terraform destroy` y luego `terraform apply`.
</details>

<details>
<summary>💡 Hint: ¿Cómo veo lo que creé en la consola de AWS?</summary>

Ve a [console.aws.amazon.com](https://console.aws.amazon.com) y busca:
- **VPC** → tu VPC, subnets, NAT Gateway
- **EKS** → tu cluster y nodos
- **RDS** → tu instancia PostgreSQL
- **ElastiCache** → tu cluster Redis
- **S3** → tu bucket de imágenes
- **ECR** → tu repositorio Docker
</details>

### 🔧 Troubleshooting: Terraform + AWS (Fase 10.1 a 10.9)

Aquí están los problemas más comunes que te puedes encontrar al crear la infraestructura. No te asustes si te pasa alguno, son normales y todos tienen solución.

Diagnóstico express (haz esto primero, en este orden):

```bash
cd terraform/
aws sts get-caller-identity
terraform validate
terraform plan
terraform state list
```

Si uno de estos 5 pasos falla, arregla ese punto antes de seguir con errores más específicos.

<details>
<summary>🔥 terraform apply falla con "AccessDenied" o "UnauthorizedAccess"</summary>

**Síntoma:** Terraform dice que no tiene permisos para crear algún recurso.

**Causa:** Tu usuario de AWS no tiene los permisos necesarios.

**Solución:**
```bash
# Verifica quién eres
aws sts get-caller-identity

# Si ves un error, tus credenciales no están bien configuradas:
aws configure
```

Tu usuario necesita estas políticas como mínimo:
- `AmazonVPCFullAccess`
- `AmazonEKSClusterPolicy`
- `AmazonEC2FullAccess`
- `IAMFullAccess`
- `AmazonS3FullAccess`
- `AmazonElastiCacheFullAccess`
- `AmazonRDSFullAccess`
- `AmazonEC2ContainerRegistryFullAccess`

Lo más fácil para aprender: usa un usuario con `AdministratorAccess`. Cuando todo funcione, podrás restringir permisos.
</details>

<details>
<summary>🔥 terraform apply falla con "LimitExceeded" o "ResourceLimitExceeded"</summary>

**Síntoma:** AWS dice que has alcanzado el límite de algún recurso (VPCs, EIPs, etc.)

**Solución:**
```bash
# Ver tus límites de servicio actuales
aws service-quotas list-service-quotas --service-code vpc --query 'Quotas[?QuotaCode==`L-F678F1CE`]'
```

- **VPC limit:** Por defecto tienes 5 VPCs por región. Si ya tienes 5, borra una o cambia de región.
- **EIP limit:** Por defecto tienes 5 Elastic IPs. El NAT Gateway usa una.
- **EKS limit:** Por defecto puedes tener 100 clusters, raro que llegues aquí.

Para pedir más cuota: AWS Console → Service Quotas → Solicitar aumento.
</details>

<details>
<summary>🔥 terraform apply falla con "InvalidParameterValue" en EKS version</summary>

**Síntoma:** Error diciendo que la versión de EKS no es válida.

**Causa:** La versión que especificaste ya no está disponible o aún no existe en tu región.

**Solución:**
```bash
# Ver versiones disponibles de EKS
aws eks describe-addon-versions --query 'addons[0].addonVersions[0].compatibilities[*].clusterVersion' --output text

# O más directo:
aws eks describe-addon-versions --query 'addons[].addonVersions[].compatibilities[].clusterVersion' --output text
```

Cambia la versión en `eks.tf` por una de las que te muestre el comando.
</details>

<details>
<summary>🔥 terraform apply falla con "InvalidParameterCombination" en RDS</summary>

**Síntoma:** Error al crear la instancia RDS, algo sobre la combinación de parámetros.

**Causas comunes:**
1. La versión de PostgreSQL no está disponible para `db.t3.micro`
2. La combinación engine_version + instance_class no existe

**Solución:**
```bash
# Ver versiones disponibles de PostgreSQL para tu tipo de instancia
aws rds describe-orderable-db-instance-options \
  --engine postgres \
  --db-instance-class db.t3.micro \
  --query 'OrderableDBInstanceOptions[*].EngineVersion' \
  --output text \
  --region eu-west-1
```

Si `16.4` no está disponible, usa la versión más reciente que te muestre el comando.
</details>

<details>
<summary>🔥 terraform apply tarda mucho y parece colgado</summary>

**Síntoma:** Lleva 15+ minutos y no termina.

**Es normal para estos recursos:**
- EKS cluster: **10-15 minutos** (es el más lento)
- RDS: **5-10 minutos**
- NAT Gateway: **2-5 minutos**
- ElastiCache: **5-10 minutos**

Total de un `terraform apply` completo: **20-30 minutos** la primera vez.

No lo canceles. Si Ctrl+C, tendrás recursos a medias y tendrás que limpiar manualmente.
</details>

<details>
<summary>🔥 terraform apply falla a mitad de camino</summary>

**Síntoma:** Algunos recursos se crearon pero otros fallaron.

**Solución:** No entres en pánico. Terraform recuerda qué creó.

```bash
# Ver qué tiene Terraform en su state
terraform state list

# Arregla el error y vuelve a aplicar
terraform apply
# Solo intentará crear los que faltan

# Si todo está muy roto y quieres empezar de cero:
terraform destroy
# Espera a que termine
terraform apply
```
</details>

<details>
<summary>🔥 kubectl get nodes no funciona después de crear EKS</summary>

**Síntoma:** `kubectl` da error de conexión o autenticación.

**Soluciones:**
```bash
# 1. Actualizar kubeconfig
aws eks update-kubeconfig --name <tu-cluster> --region <tu-region>

# 2. Verificar que el contexto es correcto
kubectl config current-context
# Debe mostrar algo con "image-resizer-eks"

# 3. Si da "Unauthorized":
# Tu usuario de AWS debe ser el MISMO que creó el cluster
aws sts get-caller-identity
# El ARN que muestra debe coincidir con el que usó Terraform

# 4. Si usaste un perfil diferente:
aws eks update-kubeconfig --name <tu-cluster> --region <tu-region> --profile tu-perfil
```
</details>

<details>
<summary>🔥 Los nodos de EKS aparecen como "NotReady"</summary>

**Síntoma:** `kubectl get nodes` muestra nodos en NotReady.

**Causas comunes:**
1. Los nodos no tienen internet (NAT Gateway no funciona)
2. El security group no permite la comunicación necesaria

**Diagnóstico:**
```bash
# Ver detalles de los nodos
kubectl describe nodes

# Buscar en la sección "Conditions" el motivo
# Si dice "NetworkPluginNotReady": problema de red/CNI
# Si dice "KubeletNotReady": el nodo no puede comunicar con el API server
```

**Solución más común:** Verificar que la route table de las subnets privadas apunta al NAT Gateway:
```bash
# En AWS Console: VPC → Route Tables → la tabla privada
# Debe tener: 0.0.0.0/0 → nat-xxxxx
```
</details>

<details>
<summary>🔥 Error de bucket S3 "BucketAlreadyExists"</summary>

**Síntoma:** Terraform falla porque el nombre del bucket S3 ya existe.

**Causa:** Los nombres de bucket S3 son globales. Alguien (o tú en otro intento) ya tiene un bucket con ese nombre.

**Solución:** Cambia el nombre del bucket en `s3.tf`. Añade algo único:
```hcl
bucket = "${var.project_name}-images-${var.environment}-${data.aws_caller_identity.current.account_id}"
```

O simplemente pon tu nombre: `image-resizer-images-dev-tunombre`
</details>

---

Ahora que tienes la infra en AWS, necesitas adaptar tu Helm Chart. Los cambios principales:
- Ya NO despliegas PostgreSQL, Redis ni MinIO como pods (son servicios managed)
- La app usa S3 en vez de MinIO
- La app usa IRSA en vez de access keys para S3
- Se añade un ServiceAccount con anotación de IAM Role
- El Ingress reemplaza a la Route de OpenShift

**Tu tarea:** Crea un `values-aws.yaml` para el entorno AWS.

<details>
<summary>🔑 Solución: values-aws.yaml</summary>

```yaml
# helm/image-resizer/values-aws.yaml
# Valores para el entorno AWS (reemplaza values-dev.yaml de OpenShift)

image:
  # ECR repository URL - se sobreescribe en el pipeline
  repository: ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/image-resizer
  tag: "latest"
  pullPolicy: Always

api:
  replicaCount: 2
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "500m"

worker:
  replicaCount: 2
  concurrency: 4
  resources:
    requests:
      memory: "256Mi"
      cpu: "200m"
    limits:
      memory: "1Gi"
      cpu: "1000m"

# ¡DESACTIVADOS! Ya son servicios managed de AWS
redis:
  enabled: false

minio:
  enabled: false

postgresql:
  enabled: false

# Service Account con IRSA
serviceAccount:
  create: true
  name: image-resizer-sa
  annotations:
    eks.amazonaws.com/role-arn: "" # Se sobreescribe en el pipeline

service:
  type: ClusterIP
  port: 5000

# Ingress en vez de Route de OpenShift
ingress:
  enabled: true
  className: "alb"
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
  host: ""

route:
  enabled: false  # Solo para OpenShift

# External Secrets (se activa en Fase 11)
externalSecrets:
  enabled: false

# Evita que Helm sobrescriba el Secret creado manualmente en Fase 10
secret:
  enabled: false

config:
  baseUrl: ""
  storageBucket: ""  # Se sobreescribe con el nombre real del bucket S3
  storageRegion: "eu-west-1"
  redisUrl: ""       # Se sobreescribe con el endpoint de ElastiCache
  useAWS: true       # Flag para que la app sepa que usa S3 nativo

probes:
  liveness:
    initialDelaySeconds: 15
    periodSeconds: 10
  readiness:
    initialDelaySeconds: 10
    periodSeconds: 5
```
</details>

**Tu tarea:** Crea el template del ServiceAccount y el Ingress.

<details>
<summary>🔑 Solución: templates/serviceaccount.yaml</summary>

```yaml
{{- if .Values.serviceAccount.create }}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ .Values.serviceAccount.name | default (include "image-resizer.fullname" .) }}
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}
```
</details>

<details>
<summary>🔑 Solución: templates/ingress.yaml</summary>

```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "image-resizer.fullname" . }}
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "image-resizer.fullname" . }}
                port:
                  number: {{ .Values.service.port }}
{{- end }}
```
</details>

**Tu tarea:** Actualiza los templates de api-deployment y worker-deployment para usar el ServiceAccount.

<details>
<summary>💡 Pista: añadir serviceAccountName al deployment</summary>

En los templates de `api-deployment.yaml` y `worker-deployment.yaml`, dentro de `spec.template.spec`, añade:

```yaml
    spec:
      serviceAccountName: {{ .Values.serviceAccount.name | default (include "image-resizer.fullname" .) }}
      containers:
        ...
```
</details>

**Tu tarea:** Actualiza el ConfigMap para AWS (S3 endpoint cambia).

<details>
<summary>💡 Pista: ConfigMap para AWS</summary>

En AWS, el storage endpoint ya no es `http://minio:9000`. Se usa el SDK de AWS directamente (que sabe la URL de S3). Además, el Redis ya no es el pod local sino ElastiCache. Necesitas añadir las variables `AWS_REGION`, `STORAGE_USE_AWS` y hacer que `REDIS_URL` sea configurable:

```yaml
# En templates/configmap.yaml, modifica la sección data completa:
data:
  {{- if .Values.config.baseUrl }}
  BASE_URL: {{ .Values.config.baseUrl | quote }}
  {{- else if .Values.route.enabled }}
  BASE_URL: "https://{{ include "image-resizer.fullname" . }}-{{ .Release.Namespace }}.apps.sandbox.openshiftapps.com"
  {{- else }}
  BASE_URL: "http://localhost:5000"
  {{- end }}
  {{- if .Values.config.useAWS }}
  STORAGE_USE_AWS: "true"
  AWS_REGION: {{ .Values.config.storageRegion | quote }}
  {{- else }}
  STORAGE_ENDPOINT: "http://minio:9000"
  {{- end }}
  STORAGE_BUCKET: {{ .Values.config.storageBucket | quote }}
  REDIS_URL: {{ .Values.config.redisUrl | default "redis://redis:6379/0" | quote }}
```
</details>

### ✅ Checkpoint 10.10

```bash
# Verificar que el chart sigue siendo válido
helm lint helm/image-resizer/

# Ver qué generaría con los values de AWS
helm template my-release helm/image-resizer/ -f helm/image-resizer/values-aws.yaml

# Deberías ver:
# - ServiceAccount con anotación IRSA
# - Ingress en vez de Route
# - ConfigMap con STORAGE_USE_AWS
# - NO ver deployments de Redis, MinIO ni PostgreSQL
```

---

#### 10.11 Adaptar la App para AWS S3

La app necesita un cambio pequeño: cuando `STORAGE_USE_AWS=true`, usar el SDK de boto3 sin endpoint custom (boto3 sabe hablar con S3 directamente usando las credenciales de IRSA).

**Tu tarea:** Modifica `app/storage.py` para soportar S3 nativo.

<details>
<summary>🔑 Solución</summary>

```python
# app/storage.py
import boto3
import os
from botocore.exceptions import ClientError


def get_storage_client():
    use_aws = os.getenv('STORAGE_USE_AWS', 'false').lower() == 'true'

    if use_aws:
        # En AWS: boto3 usa las credenciales de IRSA automáticamente
        return boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'eu-west-1')
        )
    else:
        # En local/OpenShift: MinIO con credenciales explícitas
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
        use_aws = os.getenv('STORAGE_USE_AWS', 'false').lower() == 'true'
        if use_aws:
            # En AWS, el bucket ya existe (lo creó Terraform)
            raise
        else:
            # En MinIO, lo creamos
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

### ✅ Checkpoint 10.11 — Tests

```bash
# Los tests deben seguir pasando (usan mocks, no S3 real)
pytest tests/ -v

# Verifica que el cambio no rompe nada
```

---

#### 10.12 Desplegar en EKS

Ahora que tienes la infra y el chart adaptado, despliega la app en EKS.

**10.12.A Preparar variables e instalar AWS Load Balancer Controller**

```bash
# 1. Obtén outputs de Terraform
cd terraform/
terraform output

CLUSTER_NAME=$(terraform output -raw eks_cluster_name)
AWS_REGION=$(terraform output -raw aws_region)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

helm repo add eks https://aws.github.io/eks-charts
helm repo update

# Crear o reutilizar la policy IAM del controller (una vez por cuenta)
POLICY_ARN=$(aws iam list-policies --scope Local \
  --query "Policies[?PolicyName=='AWSLoadBalancerControllerIAMPolicy'].Arn | [0]" \
  --output text)

if [ "$POLICY_ARN" = "None" ]; then
  curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.1/docs/install/iam_policy.json
  aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json
  POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy"
fi

eksctl create iamserviceaccount \
  --cluster "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --attach-policy-arn "$POLICY_ARN" \
  --approve \
  --override-existing-serviceaccounts

helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName="$CLUSTER_NAME" \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --wait

kubectl -n kube-system rollout status deployment aws-load-balancer-controller
```

Señal de éxito 10.12.A:
- `rollout status ... successfully rolled out`.
- `kubectl -n kube-system get pods | grep aws-load-balancer-controller` muestra pods `Running`.

**10.12.B Build y push de imagen a ECR**

```bash
cd ..
ECR_URL=$(cd terraform && terraform output -raw ecr_repository_url)
ECR_REGISTRY=$(echo "$ECR_URL" | cut -d'/' -f1)

aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
docker build -t $ECR_URL:latest .
docker push $ECR_URL:latest
```

Si abriste una terminal nueva entre pasos, vuelve a definir `AWS_REGION` antes del login a ECR.

Señal de éxito 10.12.B:
- `docker push` termina sin `denied` ni `unauthorized`.
- En ECR (consola) ves al menos una imagen con tag `latest`.

**10.12.C Crear Secret de DATABASE_URL**

```bash
DB_URL=$(cd terraform && terraform output -raw database_url)
REDIS_URL="redis://$(cd terraform && terraform output -raw redis_endpoint)"

kubectl create secret generic image-resizer-secret \
  --from-literal=DATABASE_URL="$DB_URL" \
  --dry-run=client -o yaml | kubectl apply -f -
```

Señal de éxito 10.12.C:
- `kubectl get secret image-resizer-secret` devuelve `1` recurso.
- `kubectl get secret image-resizer-secret -o yaml` contiene `DATABASE_URL` en `data`.

**10.12.D Desplegar app con Helm**

```bash
S3_BUCKET=$(cd terraform && terraform output -raw s3_bucket_name)
ROLE_ARN=$(cd terraform && terraform output -raw app_role_arn)

helm upgrade --install image-resizer ./helm/image-resizer \
  -f ./helm/image-resizer/values-aws.yaml \
  --set image.repository=$ECR_URL \
  --set image.tag=latest \
  --set secret.enabled=false \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$ROLE_ARN \
  --set config.storageBucket=$S3_BUCKET \
  --set config.redisUrl=$REDIS_URL \
  --wait --timeout 300s

kubectl get pods
kubectl get ingress
```

Señal de éxito 10.12.D:
- `helm` termina con `STATUS: deployed`.
- API y worker en `Running`.
- `kubectl get ingress` muestra `ADDRESS` (hostname del ALB). Si tarda, espera 2-5 minutos.

<details>
<summary>💡 Hint: Los pods no arrancan</summary>

Errores comunes en AWS:
- **ImagePullBackOff:** El nodo no puede acceder a ECR. Verifica que el node role tiene `AmazonEC2ContainerRegistryReadOnly`.
- **CrashLoopBackOff:** La app no puede conectar a RDS. Verifica que el security group de RDS permite tráfico desde el SG del cluster EKS.
- **Pending:** No hay nodos con recursos suficientes. Escala el node group o usa instancias más grandes.

Diagnóstico:
```bash
kubectl describe pod <nombre-del-pod>
kubectl logs <nombre-del-pod>
```
</details>

<details>
<summary>💡 Hint: El AWS Load Balancer Controller no arranca</summary>

El controller necesita permisos IAM. Si usas IRSA (recomendado), crea un role con la policy de AWS:

```bash
# Descarga la policy
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.1/docs/install/iam_policy.json

# Crea la policy
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json

# Asocia con el service account (necesitas eksctl o hacerlo manualmente)
```

Si esto se complica, puedes temporalmente usar `kubectl port-forward` para acceder a la app y dejar el Ingress para después.
</details>

### ✅ Checkpoint Final de la Fase 10

```bash
# 1. Verifica que TODO funciona
kubectl get pods
# Todos los pods deben estar Running

# 2. Prueba la app
APP_URL=$(kubectl get ingress image-resizer -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
# O si usas port-forward:
# APP_URL="localhost:5000"

# Health check
curl http://$APP_URL/health/live

# Resize una imagen
curl -X POST http://$APP_URL/resize \
  -F "image=@test.jpg" \
  -F "width=200" \
  -F "height=200"

# 3. Verifica que la imagen se guardó en S3
aws s3 ls s3://$(cd terraform && terraform output -raw s3_bucket_name)/resized/
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   📊 QUÉ HAS CONSEGUIDO EN ESTA FASE                        │
│                                                             │
│   ✅ Infraestructura como Código (IaC) con Terraform         │
│   ✅ VPC con subnets públicas y privadas                     │
│   ✅ EKS cluster con nodos managed                          │
│   ✅ RDS PostgreSQL managed                                  │
│   ✅ ElastiCache Redis managed                               │
│   ✅ S3 para almacenamiento de imágenes                      │
│   ✅ ECR para imágenes Docker                                │
│   ✅ IRSA para acceso seguro a S3 desde pods                 │
│   ✅ State remoto en S3 + DynamoDB                           │
│                                                             │
│   💡 RECUERDA: terraform destroy cuando no lo uses           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 🧠 Qué debes saber explicar (Fase 10)

1. ¿Por qué usamos subnets privadas para nodos EKS y base de datos, y no todo en subnets públicas?
2. ¿Qué problema resuelven IRSA y el OIDC provider frente a usar access keys en variables de entorno?
3. ¿Qué se rompe si no ejecutas `terraform destroy` al cerrar la sesión de laboratorio?

### 🔧 Troubleshooting: Deploy en EKS (Fase 10.10 a 10.12)

Esta es la fase donde más cosas pueden fallar porque involucra la comunicación entre TODOS los componentes. Aquí tienes una guía de diagnóstico paso a paso.

Diagnóstico express (haz esto primero, en este orden):

```bash
kubectl get pods -A
kubectl get events --sort-by=.lastTimestamp | tail -n 30
kubectl describe pod <nombre-del-pod>
kubectl logs <nombre-del-pod>
kubectl get ingress
```

Si aquí ya encuentras el error, corrige eso antes de entrar a casos avanzados.

<details>
<summary>🔥 IRSA no funciona: la app no puede acceder a S3</summary>

**Síntoma:** Los pods arrancan pero al subir una imagen da error `AccessDenied` o `NoCredentialsError`.

**IRSA funciona así:** El pod asume un IAM Role a través de un token inyectado automáticamente. Si falla cualquier parte de la cadena, no hay credenciales.

**Diagnóstico paso a paso:**

```bash
# 1. Verificar que el ServiceAccount tiene la anotación correcta
kubectl get sa image-resizer-sa -o yaml
# Debe tener:
#   annotations:
#     eks.amazonaws.com/role-arn: arn:aws:iam::XXXXX:role/image-resizer-app-role

# 2. Verificar que el pod usa el ServiceAccount correcto
kubectl get pod <nombre-pod> -o jsonpath='{.spec.serviceAccountName}'
# Debe decir "image-resizer-sa"

# 3. Verificar que el token de IRSA está inyectado en el pod
kubectl exec <nombre-pod> -- ls /var/run/secrets/eks.amazonaws.com/serviceaccount/
# Debe mostrar "token"

# 4. Verificar que las variables de entorno están inyectadas
kubectl exec <nombre-pod> -- env | grep AWS
# Debe mostrar:
#   AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token
#   AWS_ROLE_ARN=arn:aws:iam::XXXXX:role/image-resizer-app-role

# 5. Si NO ves estas variables, el OIDC provider puede estar mal
aws eks describe-cluster --name <tu-cluster> --query "cluster.identity.oidc.issuer" --output text
# Compara con:
aws iam list-open-id-connect-providers
# El issuer del cluster debe coincidir con uno de los providers
```

**Causas más comunes:**
1. **El OIDC provider no se creó:** `terraform apply` de iam.tf falló silenciosamente. Re-ejecuta `terraform apply`.
2. **La anotación del ServiceAccount es incorrecta:** Revisa que el `--set serviceAccount.annotations...` del `helm upgrade` no tenga errores de escape. Los puntos en `eks.amazonaws.com` necesitan escaping con `\\.`.
3. **El Condition del Trust Policy es incorrecto:** El role espera exactamente `system:serviceaccount:${var.k8s_namespace}:image-resizer-sa`. Si cambiaste de namespace, actualiza `k8s_namespace` y vuelve a aplicar Terraform.
</details>

<details>
<summary>🔥 La app no puede conectar a RDS (CrashLoopBackOff)</summary>

**Síntoma:** El pod arranca y crashea inmediatamente. Los logs dicen algo como `could not connect to server` o `connection refused` a PostgreSQL.

**Diagnóstico:**

```bash
# 1. Ver los logs del pod
kubectl logs <nombre-pod>

# 2. Verificar que el DATABASE_URL es correcto
kubectl get secret image-resizer-secret -o jsonpath='{.data.DATABASE_URL}' | base64 -d
# Debe ser algo como: postgresql://imageresizer:password@image-resizer-db.xxxx.eu-west-1.rds.amazonaws.com:5432/imageresizer

# 3. Probar la conectividad desde un pod temporal
kubectl run debug --image=postgres:16 --rm -it --restart=Never -- bash
# Dentro del pod:
pg_isready -h image-resizer-db.xxxx.eu-west-1.rds.amazonaws.com -p 5432
# Si dice "accepting connections" → la red funciona
# Si dice "no response" → problema de security group
```

**Causas más comunes:**
1. **Security Group:** El SG de RDS no permite tráfico desde el cluster security group de EKS. Verifica en la consola de AWS:
   - Ve a RDS → tu instancia → Security Groups
   - El SG debe tener una regla inbound: `TCP 5432 desde sg-XXXX` donde `sg-XXXX` es el **cluster security group** de EKS
2. **El endpoint de RDS es incorrecto:** Comprueba `terraform output rds_endpoint` y que coincide con lo que hay en el Secret.
3. **La contraseña es incorrecta:** Si cambiaste `db_password` en `terraform.tfvars` después de crear la instancia, Terraform NO actualiza la contraseña automáticamente. Tendrás que cambiarla manualmente en la consola de AWS.
</details>

<details>
<summary>🔥 La app no puede conectar a Redis (ElastiCache)</summary>

**Síntoma:** La app funciona para peticiones simples pero falla al procesar imágenes (el worker usa Redis como broker de Celery).

**Diagnóstico:**

```bash
# 1. Verificar el REDIS_URL
kubectl get configmap <nombre>-config -o yaml | grep REDIS_URL
# Debe ser algo como: redis://image-resizer-redis.xxxx.cache.amazonaws.com:6379

# 2. Probar conectividad desde un pod temporal
kubectl run debug --image=redis:7 --rm -it --restart=Never -- bash
redis-cli -h image-resizer-redis.xxxx.cache.amazonaws.com -p 6379 ping
# Debe responder PONG
# Si no responde → problema de security group
```

**Causas más comunes:**
1. **Security Group:** Igual que RDS, el SG de ElastiCache debe permitir `TCP 6379` desde el **cluster security group** de EKS.
2. **El REDIS_URL no se pasó bien:** Si olvidaste `--set config.redisUrl=...` en el `helm upgrade`, el ConfigMap tendrá `redis://redis:6379/0` (que apunta al pod que ya no existe).
3. **ElastiCache está en otra subnet:** Verifica que ElastiCache está en las subnets privadas (las mismas que los nodos de EKS).
</details>

<details>
<summary>🔥 El Ingress no obtiene una dirección (ADDRESS vacío)</summary>

**Síntoma:** `kubectl get ingress` muestra la columna ADDRESS vacía durante más de 5 minutos.

**Diagnóstico:**

```bash
# 1. Verificar que el ALB Controller está corriendo
kubectl -n kube-system get pods | grep aws-load-balancer
# Debe haber 1-2 pods en Running

# 2. Ver los logs del controller
kubectl -n kube-system logs deployment/aws-load-balancer-controller

# 3. Verificar los eventos del Ingress
kubectl describe ingress image-resizer
# Busca en la sección Events si hay errores
```

**Causas más comunes:**
1. **El ALB Controller no tiene permisos IAM:** El controller necesita un IAM role propio con permisos para crear ALBs. La instalación básica que hicimos puede no tener estos permisos. Consulta el hint sobre ALB Controller más arriba.
2. **Las subnets públicas no tienen la etiqueta correcta:** Las subnets públicas deben tener el tag `kubernetes.io/role/elb = 1` para que el ALB Controller las encuentre. Ya lo incluimos en `vpc.tf`, pero verifica en la consola.
3. **No hay Internet Gateway:** El ALB necesita subnets públicas con ruta al Internet Gateway.

**Plan B si el Ingress no funciona:**
```bash
# Usa port-forward para acceder a la app mientras arreglas el Ingress
kubectl port-forward svc/image-resizer 5000:5000
# Accede en http://localhost:5000
```
</details>

<details>
<summary>🔥 Cómo diagnosticar CUALQUIER problema de conectividad entre componentes</summary>

**Técnica universal:** Lanza un pod de debug con todas las herramientas de red:

```bash
kubectl run debug --image=nicolaka/netshoot --rm -it --restart=Never -- bash
```

Desde ahí puedes:
```bash
# Probar DNS
nslookup image-resizer-db.xxxx.eu-west-1.rds.amazonaws.com

# Probar conectividad TCP
nc -zv image-resizer-db.xxxx.eu-west-1.rds.amazonaws.com 5432
# "succeeded" = puerto abierto, "timed out" = security group bloqueando

# Probar Redis
nc -zv image-resizer-redis.xxxx.cache.amazonaws.com 6379

# Probar que los nodos tienen internet (via NAT)
curl -s https://httpbin.org/ip

# Probar acceso a S3
curl -s https://s3.eu-west-1.amazonaws.com
```

**Regla general de security groups:**
Si `nc -zv` da `timed out`, el security group está bloqueando.
Si da `connection refused`, el servicio no está escuchando (problema del servicio, no de red).
</details>

<details>
<summary>🔥 terraform destroy falla y quedan recursos huérfanos</summary>

**Síntoma:** `terraform destroy` da error y quedan recursos en AWS que te siguen costando dinero.

**Solución por orden:**

```bash
# 1. Intenta de nuevo (a veces es un problema temporal)
terraform destroy

# 2. Si un recurso específico falla, destrúyelo manualmente:
# Ve a la consola de AWS, busca el recurso y bórralo a mano
# Luego dile a Terraform que se olvide de él:
terraform state rm aws_eks_node_group.main
terraform state rm aws_eks_cluster.main
# Y vuelve a intentar
terraform destroy

# 3. Si todo falla, borra los recursos manualmente en este orden:
# a) EKS Node Group (primero los nodos)
# b) EKS Cluster (luego el cluster)
# c) RDS (ojo: si tiene deletion protection, desactívala primero)
# d) ElastiCache
# e) NAT Gateway (puede tardar unos minutos)
# f) Elastic IP
# g) Subnets
# h) Internet Gateway
# i) Security Groups
# j) VPC (al final, cuando todo lo demás esté borrado)
```

**Tip:** Después de borrar manualmente, borra el state local para no confundir a Terraform:
```bash
rm -rf .terraform terraform.tfstate*
```
</details>

---

## Fase 11: External Secrets + AWS Secrets Manager

### 🎯 Objetivo
Reemplazar Sealed Secrets (que usamos en OpenShift) por External Secrets Operator + AWS Secrets Manager. En vez de encriptar secrets en el repo, los guardas en AWS y el operador los sincroniza automáticamente al cluster.
 
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   💡 SEALED SECRETS vs EXTERNAL SECRETS                      │
│                                                             │
│   Sealed Secrets (Doc 1):                                   │
│   Secret.yaml → kubeseal → SealedSecret.yaml → Git         │
│   El controlador en el cluster desencripta                  │
│                                                             │
│   External Secrets (Doc 2):                                 │
│   AWS Secrets Manager → ExternalSecret.yaml → Git           │
│   El operador lee de AWS y crea el Secret en K8s            │
│                                                             │
│   Ventaja: Los secrets NUNCA tocan Git, ni encriptados.     │
│   Los gestionas en AWS Secrets Manager (rotación, auditoría)│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📝 Tareas

#### 11.1 Crear secrets en AWS Secrets Manager

```bash
# Crear el secret con los datos de la app
aws secretsmanager create-secret \
  --name image-resizer/dev \
  --description "Image Resizer app secrets for dev environment" \
  --secret-string '{
    "DATABASE_URL": "postgresql://imageresizer:CambiameP0rAlgoSeguro!@TU-RDS-ENDPOINT:5432/imageresizer",
    "REDIS_URL": "redis://TU-REDIS-ENDPOINT:6379"
  }' \
  --region eu-west-1
```

Sustituye `TU-RDS-ENDPOINT` y `TU-REDIS-ENDPOINT` por los valores reales de `terraform output`.

#### 11.2 IAM Policy para leer secrets

**Tu tarea:** Añade a Terraform un IAM policy que permita a los pods leer de Secrets Manager.

<details>
<summary>🔑 Solución: Añadir a iam.tf</summary>

```hcl
# Añadir al final de terraform/iam.tf

# --- Policy para leer secrets ---
data "aws_iam_policy_document" "secrets_access" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]
    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.project_name}/*"
    ]
  }
}

resource "aws_iam_policy" "secrets_access" {
  name   = "${var.project_name}-secrets-access"
  policy = data.aws_iam_policy_document.secrets_access.json
}

resource "aws_iam_role_policy_attachment" "app_secrets_access" {
  policy_arn = aws_iam_policy.secrets_access.arn
  role       = aws_iam_role.app_role.name
}
```

```bash
# Aplicar el cambio
cd terraform/
terraform apply
```
</details>

#### 11.3 Instalar External Secrets Operator

```bash
# Añadir el repo de Helm
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Instalar el operador
helm upgrade --install external-secrets external-secrets/external-secrets \
  -n external-secrets \
  --create-namespace \
  --set installCRDs=true \
  --wait
```

#### 11.4 Crear el ClusterSecretStore

El ClusterSecretStore le dice al operador CÓMO conectarse a AWS Secrets Manager.

**Tu tarea:** Crea el manifiesto `helm/image-resizer/templates/cluster-secret-store.yaml`.

<details>
<summary>🔑 Solución</summary>

```yaml
{{- if .Values.externalSecrets.enabled }}
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: {{ .Values.config.storageRegion | default "eu-west-1" }}
      auth:
        jwt:
          serviceAccountRef:
            name: {{ .Values.serviceAccount.name | default (include "image-resizer.fullname" .) }}
            namespace: {{ .Release.Namespace }}
{{- end }}
```
</details>

#### 11.5 Condicionar el Secret de Helm

Hay un problema: el template `secret.yaml` de Helm puede pisar el Secret manual de Fase 10 o entrar en conflicto con el ExternalSecret de Fase 11. Necesitas condicionar el template para que NO se cree en esos casos.

**Tu tarea:** Modifica `helm/image-resizer/templates/secret.yaml`:

<details>
<summary>🔑 Solución</summary>

```yaml
{{- if and (.Values.secret.enabled | default true) (not .Values.externalSecrets.enabled) }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "image-resizer.fullname" . }}-secret
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
type: Opaque
stringData:
  DATABASE_URL: {{ .Values.config.databaseUrl | default (include "image-resizer.databaseUrl" .) | quote }}
  STORAGE_ACCESS_KEY: {{ .Values.minio.rootUser | quote }}
  STORAGE_SECRET_KEY: {{ .Values.minio.rootPassword | quote }}
{{- end }}
```

El `{{- if and (.Values.secret.enabled | default true) (not .Values.externalSecrets.enabled) }}` hace que:
- En OpenShift (`secret.enabled: true`, `externalSecrets.enabled: false`): se crea el Secret como antes
- En AWS Fase 10 (`secret.enabled: false`): NO se crea, se usa el Secret manual
- En AWS Fase 11 (`externalSecrets.enabled: true`): NO se crea, porque lo crea el ExternalSecret

Tabla rápida: qué Secret "manda" en cada fase

| Fase | Quién crea `image-resizer-secret` | Configuración clave |
|------|-----------------------------------|---------------------|
| Documento 1 / OpenShift | Helm (`templates/secret.yaml`) | `secret.enabled: true`, `externalSecrets.enabled: false` |
| Fase 10 en AWS | Tú manualmente con `kubectl create secret` | `secret.enabled: false`, `externalSecrets.enabled: false` |
| Fase 11 en AWS | External Secrets Operator | `secret.enabled: false`, `externalSecrets.enabled: true` |

Regla de oro: nunca dejes dos orígenes activos a la vez para el mismo Secret.
</details>

#### 11.6 Crear el ExternalSecret

El ExternalSecret dice QUÉ secret leer de AWS y cómo mapearlo a un Secret de Kubernetes.

**Tu tarea:** Crea el manifiesto `helm/image-resizer/templates/external-secret.yaml`.

<details>
<summary>🔑 Solución</summary>

```yaml
{{- if .Values.externalSecrets.enabled }}
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: {{ include "image-resizer.fullname" . }}-secret
  labels:
    {{- include "image-resizer.labels" . | nindent 4 }}
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: {{ include "image-resizer.fullname" . }}-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: {{ .Values.externalSecrets.secretName }}
{{- end }}
```
</details>

#### 11.7 Actualizar values-aws.yaml

Añade la configuración de External Secrets:

```yaml
# Añadir a helm/image-resizer/values-aws.yaml

secret:
  enabled: false

externalSecrets:
  enabled: true
  secretName: "image-resizer/dev"  # Nombre del secret en AWS SM
```

### ✅ Checkpoint de la Fase 11

```bash
# Redesplegar con Helm
helm upgrade --install image-resizer ./helm/image-resizer \
  -f ./helm/image-resizer/values-aws.yaml \
  --set image.repository=$ECR_URL \
  --set image.tag=latest \
  --set secret.enabled=false \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$ROLE_ARN \
  --set config.storageBucket=$S3_BUCKET \
  --wait --timeout 300s

# Verificar que el ExternalSecret sincronizó
kubectl get externalsecret
# STATUS debe ser "SecretSynced"

# Verificar que el Secret se creó
kubectl get secret image-resizer-secret -o yaml

# Verificar que los pods usan el secret
kubectl get pods
```

<details>
<summary>💡 Hint: ExternalSecret dice "SecretSyncedError"</summary>

Errores comunes:
1. **AccessDeniedException:** El IAM Role no tiene permiso para leer el secret. Verifica la policy en iam.tf.
2. **ResourceNotFoundException:** El nombre del secret en AWS no coincide con `secretName` en values.
3. **IRSA no funciona:** Verifica que el ServiceAccount tiene la anotación correcta: `kubectl describe sa image-resizer-sa`

Diagnóstico:
```bash
kubectl describe externalsecret image-resizer-secret
# Lee la sección "Events" para ver el error exacto
```
</details>

<details>
<summary>💡 Hint: El ClusterSecretStore dice "InvalidClusterStore"</summary>

**Síntoma:** `kubectl get clustersecretstore` muestra `Invalid` en la columna STATUS.

**Diagnóstico:**
```bash
kubectl describe clustersecretstore aws-secrets-manager
# Busca en Events el error exacto
```

**Causas comunes:**
1. **El External Secrets Operator no se instaló correctamente:**
   ```bash
   # Verificar que los pods del operator están corriendo
   kubectl -n external-secrets get pods
   # Debe haber 3 pods Running: external-secrets, cert-controller, webhook
   
   # Si alguno está en CrashLoopBackOff:
   kubectl -n external-secrets logs <pod-con-error>
   ```
2. **El ServiceAccount del ClusterSecretStore no tiene permisos:** El `serviceAccountRef` en el ClusterSecretStore debe apuntar a un SA con IRSA configurado para Secrets Manager. Si usas el mismo SA de la app (`image-resizer-sa`), verifica que la policy `secrets_access` está adjunta al role.
3. **Problemas de namespace:** Un `ClusterSecretStore` busca el ServiceAccount en un namespace específico. El namespace del `serviceAccountRef` debe coincidir con el namespace real del release.
</details>

<details>
<summary>💡 Hint: El Secret se crea pero está vacío o le faltan campos</summary>

**Síntoma:** `kubectl get secret image-resizer-secret -o yaml` muestra el secret pero no tiene los datos esperados (DATABASE_URL, REDIS_URL, etc.)

**Diagnóstico:**
```bash
# 1. Verificar el contenido del secret en AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id image-resizer/dev
# ¿El JSON tiene los campos correctos? ¿Los nombres coinciden EXACTAMENTE con lo que espera el ExternalSecret?

# 2. Verificar el mapping en el ExternalSecret
kubectl get externalsecret image-resizer-secret -o yaml
# Mira la sección spec.dataFrom[].extract.key
# Debe apuntar al secret correcto en AWS Secrets Manager

# 3. Ejemplo: si el secret en AWS es:
# {"DATABASE_URL": "...", "REDIS_URL": "..."}
# Con dataFrom.extract, esas keys se copian tal cual al Secret de Kubernetes
```

**Causa más común:** Typo en los nombres de las propiedades. JSON es case-sensitive.
</details>

<details>
<summary>💡 Hint: Hay un Secret duplicado y los pods usan el equivocado</summary>

**Síntoma:** Todo parece correcto pero la app sigue usando credenciales viejas o incorrectas.

Esto pasa si olvidaste el paso 11.5 (condicionar el secret.yaml de Helm). Helm crea un Secret y el ExternalSecret crea OTRO, o uno sobrescribe al otro.

```bash
# Verificar cuántos secrets hay
kubectl get secrets | grep image-resizer

# Si hay DOS con nombres parecidos, borra el que creó Helm
# y verifica que values-aws.yaml tiene externalSecrets.enabled: true

# Redesplegar
helm upgrade --install image-resizer ./helm/image-resizer \
  -f ./helm/image-resizer/values-aws.yaml \
  ...
```
</details>

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   📊 QUÉ HAS CONSEGUIDO EN ESTA FASE                        │
│                                                             │
│   ✅ Secrets gestionados en AWS Secrets Manager              │
│   ✅ External Secrets Operator sincronizando automáticamente │
│   ✅ NINGÚN secret en Git (ni encriptado)                    │
│   ✅ Rotación de secrets posible sin redesplegar              │
│                                                             │
│   La próxima vez que cambies un password en AWS Secrets     │
│   Manager, el operador lo actualizará en K8s en <1 hora.    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 🧠 Qué debes saber explicar (Fase 11)

1. ¿Qué diferencia práctica hay entre `secret.yaml` de Helm y `ExternalSecret`?
2. ¿Por qué `secret.enabled=false` y `externalSecrets.enabled=true` deben ir juntos en Fase 11?
3. Si `ExternalSecret` falla con `AccessDenied`, ¿qué revisarías primero: IAM policy, anotación IRSA o nombre del secret?

---

> **Continúa en Parte B:** Fases 12-13 (ArgoCD y DevSecOps)
