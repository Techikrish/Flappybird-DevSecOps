# FlappyBird — DevSecOps & GitOps Project

**A production-style FlappyBird microservices project** with end-to-end DevSecOps and GitOps:

- CI: **GitHub Actions** (SonarCloud, Trivy image scan, OWASP deps)
- CD: **Argo CD** + **Helm charts**
- Infra: **Terraform** (VPC, EKS, RDS)
- App: **Frontend (React)** + **Backend (Flask + SQLAlchemy)** + **RDS PostgreSQL**
- Observability: **Prometheus + Grafana** (packaged in Helm; Grafana and FrontEnd Service exposed by LoadBalancer)
- Security: least privilege security groups, Kubernetes Secret for DB password

# Quick high-level flow

1. Provision infra using Terraform → **EKS + RDS + VPC**
2. Provide DB password to Terraform (prompt or env): `TF_VAR_db_password`
3. Terraform outputs `rds_endpoint`
4. Create Kubernetes namespace `flappy` and a Kubernetes Secret with DB password (from step 2)
5. Edit Helm `values.yaml` (image repository names, RDS endpoint)
6. Push changes → GitHub Actions builds images, runs SonarCloud/Trivy tests, and updates Helm values (or you can commit them manually)
7. Apply Argo CD App in cluster (it will deploy Helm charts which include Prometheus+Grafana). Grafana has `service.type: LoadBalancer` and will get a public LoadBalancer DNS.
8. Access app + Grafana. Seed data or create DB if needed.

    ![digaram.png](digaram.png)

# Step-by-step execution (detailed)

### 4.1 Clone the repository

```bash
git clone https://github.com/Techikrish/Flappybird-DevSecOps
cd Flappybird-DevSecOps

```

---

### 4.2 Provision infra using Terraform

**Option A — provide DB password interactively (Terraform prompt)**:

```bash
cd infra/terrafrom 
export DB_PASSWORD="YourSecurePassword123!"
terraform apply \
  -var="db_password=$DB_PASSWORD" \
  -var="aws_region=us-east-1" \
  -var="project_name=flappybird"

```

- Terraform will create VPC, subnets, EKS, node group, security groups, RDS instance.
- After apply completes, **copy the RDS endpoint** from Terraform output (or check `terraform output rds_endpoint`).

### Create Kubernetes namespace & secret for DB password

Once complete, configure kubectl:

`aws eks --region us-east-1 update-kubeconfig --name <your-cluster-name>
kubectl get nodes`

**Create namespace `flappy`**

```bash
kubectl create namespace flappy

```

**Create secret with DB password** (use the same password you supplied to Terraform):

```bash
kubectl create secret generic flappybird-backend-db \
  --from-literal=DB_PASS="$DB_PASSWORD" \
  --namespace flappybird

```

### Edit Helm values (required manual edits)

Open `helm/flappybird/values.yaml` and update:

### 1) Update Docker repository names (image repo):

```yaml
image:
  repository: docker.io/techikrish/flappybird-frontend   # <-- your Docker Hub re
 

```

```yaml

image:
  repository: docker.io/techikrish/flappybird-backend    # <-- your Docker Hub repo
  

```

### 2) Add RDS endpoint into backend values

```yaml
 helm/flappybird/values.yaml
db:
  host: rds endpoint    # fill with Terraform rds_endpoint
  name: flappydb
  user: flappy
  # password will be read from Kubernetes secret flappy-db-secret

```

**Important:** DB_HOST must be hostname only — **do not** append `:5432`. The code adds the port separately.

---

## Update sonar-properties file

### **Create Your SonarCloud Account**

1. Go to [**https://sonarcloud.io/**](https://sonarcloud.io/)
2. Click **Log in**
3. Choose:
    - **GitHub** (recommended)

Once you sign in → you will land on the SonarCloud dashboard.

---

### **🔹  Create a New Organization (FREE Tier Supported)**

---

### **Option Manual Organization Creation**

1. Go to **My Account → Organizations**
2. Click **“Create Organization manually”**
3. Fill:
    - **Organization Name**
    - **Unique Organization Key**
    - Choose **Free plan (public projects)**

---

### **🔹 Create a New SonarCloud Project**

If using GitHub app:

1. Go to **Projects → Analyze New Project**
2. Select your connected GitHub repository (example: `DevSecOps-FlappyBird`)
3. Click **Set Up**
4. Choose:
    - **Build method → GitHub Actions**
5. SonarCloud will:
    - Generate your **project key**
    - Show the sample GitHub Actions YAML

---

### **🔹  Get Your Sonar Project Key**

After project creation:

1. Go to **Project Settings**
2. Then **General Settings → Analysis Scope**
3. You will see:

```
sonar.projectKey=<your_project_key>
sonar.organization=<your_organization>

```

Example:

```
sonar.projectKey=techikrish_flappybird
sonar.organization=techikrish

```

You will paste these into your **sonar-properties file**.

---

### **🔹  Generate SonarCloud Token (SONAR_TOKEN)**

1. Click your profile picture → **My Account**
2. Go to **Security**
3. Under “Tokens”, click:

👉 **Generate Token**

1. Give a name → `github-actions-token`
2. Click **Generate**
3. Copy the token ONCE (you can’t see it again)

Open file `sonar-properties` (repo root) and set:

```
sonar.projectKey=your_sonar_project_key_here
sonar.organization=your_sonar_org_here
sonar.projectName=flappydevsecops

```

(You must configure these values in SonarCloud for your project.)

---

### 4.6 Add required GitHub Secrets

Go to your GitHub repository → **Settings → Secrets → Actions**. Add:

- `SONAR_TOKEN` → Generate token in SonarCloud (My Account → Security → Generate token)
- `DOCKER_USERNAME` → Docker Hub username
- `DOCKER_TOKEN` → Docker Hub access token (or PAT)

**Note:** GitHub Actions provides `GITHUB_TOKEN` automatically; you **do not** need to add it manually.

### Trigger CI / Build & Push Images

Push code or change something to trigger the pipeline:

```bash
git add .
git commit -m "Update helm values"
git push origin main

```

GitHub Actions will run:

- Checkout
- Install dependencies
- Run SonarCloud (requires `SONAR_TOKEN`)
- Run Trivy scan for images
- Build Docker images and push to `docker.io/techikrish/*` (requires `DOCKER_USERNAME` & `DOCKER_TOKEN`)
- Update Helm values (if workflow configured to commit new tags) — if not automated, ensure the image tags referenced in Helm match pushed images.

### Apply Argo CD app

**(Argo app is present at `argocd/application.yaml`)**

1. Argo install it in cluster:

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

```

Apply the Argo CD App manifest (it references your repo/helm path):

```bash
kubectl apply -f argocd/application.yaml

```

Argo CD will pick the repo, path and create the Helm release in the `flappy` namespace. It will also install **Prometheus & Grafana** (they are packaged inside Helm). Grafana is exposed with `service.type: LoadBalancer`.

### Verify deployments & access endpoints

**Check pods & services**

```bash
kubectl get pods -n flappy
kubectl get svc -n flappy

```

 **Access the Deployed App**

Once deployed, get the LoadBalancer URL: 

`kubectl get svc -n flappy`

![Screenshot from 2025-11-30 14-49-00.png](FlappyBird%20%E2%80%94%20DevSecOps%20&%20GitOps%20Project/Screenshot_from_2025-11-30_14-49-00.png)

![Screenshot from 2025-11-30 17-53-10.png](FlappyBird%20%E2%80%94%20DevSecOps%20&%20GitOps%20Project/Screenshot_from_2025-11-30_17-53-10.png)

![Screenshot from 2025-11-30 18-59-01.png](FlappyBird%20%E2%80%94%20DevSecOps%20&%20GitOps%20Project/Screenshot_from_2025-11-30_18-59-01.png)

![Screenshot from 2025-11-30 18-59-56.png](FlappyBird%20%E2%80%94%20DevSecOps%20&%20GitOps%20Project/Screenshot_from_2025-11-30_18-59-56.png)
