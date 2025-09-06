# GKE CI Starter (Cloud Build + Artifact Registry)

This repository shows a minimal continuous integration (CI) pipeline that builds a Docker image, pushes it to **Artifact Registry**, and deploys it to **GKE** on each commit.

---

## Prerequisites

- Google Cloud project (e.g. `new-project-23jan2025`)
- Billing enabled
- `gcloud` CLI authenticated
- A GitHub repo you can connect to Cloud Build

> Replace the placeholders below before running (e.g. in Cloud Shell):
```
export PROJECT_ID="new-project-23jan2025"
export REGION="asia-south1"             # pick a region close to you
export AR_REPO="app-images"             # artifact registry repo name
export GKE_CLUSTER="ci-autopilot-cluster"
export GKE_REGION="asia-south1"
export K8S_NAMESPACE="default"
```

## 1) Enable required APIs
```
gcloud services enable   artifactregistry.googleapis.com   cloudbuild.googleapis.com   container.googleapis.com   compute.googleapis.com   containeranalysis.googleapis.com   --project=${PROJECT_ID}
```

## 2) Create Artifact Registry (Docker)
```
gcloud artifacts repositories create "${AR_REPO}"   --repository-format=docker   --location="${REGION}"   --description="App images"   --project="${PROJECT_ID}"
```

## 3) Create a GKE Autopilot cluster (or skip if you already have one)
```
gcloud container clusters create-auto "${GKE_CLUSTER}"   --region="${GKE_REGION}"   --project="${PROJECT_ID}"
```

## 4) Grant Cloud Build permissions (once)
Cloud Build's default service account is: `$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@cloudbuild.gserviceaccount.com`

```
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Let Cloud Build push to Artifact Registry
gcloud projects add-iam-policy-binding "$PROJECT_ID"   --member="serviceAccount:${CB_SA}"   --role="roles/artifactregistry.writer"

# Let Cloud Build read cluster info
gcloud projects add-iam-policy-binding "$PROJECT_ID"   --member="serviceAccount:${CB_SA}"   --role="roles/container.developer"

# (K8s RBAC) Give Cloud Build admin on the cluster (simple for demo; you can scope it down later)
gcloud container clusters get-credentials "$GKE_CLUSTER" --region="$GKE_REGION" --project="$PROJECT_ID"
kubectl create clusterrolebinding cloudbuild-admin-binding   --clusterrole=cluster-admin   --user="${CB_SA}"
```

## 5) Connect GitHub to Cloud Build
- Open **Cloud Build → Triggers → Connect Repository**
- Choose **GitHub (Cloud Build GitHub App)**, authorize, and select your repo.
- Create a trigger:
  - Event: *Push to a branch*
  - Branch: `^main$` (or your choice)
  - Build config: `cloudbuild.yaml`
  - Substitutions:
    - `_AR_REPO` = `${AR_REPO}`
    - `_AR_REGION` = `${REGION}`
    - `_GKE_CLUSTER` = `${GKE_CLUSTER}`
    - `_GKE_REGION` = `${GKE_REGION}`
    - `_K8S_NAMESPACE` = `${K8S_NAMESPACE}`

## 6) First deploy (from local, optional)
To test before creating the trigger:
```
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/hello-app"

# Build and push
gcloud builds submit --tag "${IMAGE}:test" app

# Create namespace if needed and apply manifests
gcloud container clusters get-credentials "$GKE_CLUSTER" --region="$GKE_REGION" --project="$PROJECT_ID"
kubectl create ns "$K8S_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/

# Expose external IP (wait a minute), then check:
kubectl get svc -n "$K8S_NAMESPACE"
```

## 7) After the trigger is on
Push to `main` and Cloud Build will:
- Build the image (tagged with commit SHA and `latest`)
- Push to Artifact Registry
- Apply the Kubernetes manifests
- Restart the Deployment to pick up the new image

---

## Files

- `app/` — a tiny Flask app
- `Dockerfile` — builds the container
- `k8s/` — Kubernetes manifests
- `cloudbuild.yaml` — CI pipeline
# Trigger test Sat Sep  6 12:44:23 IST 2025
