# SwarmOps — Google Cloud infrastructure (P12).
#
# Provisions: enabled APIs, Artifact Registry, Firestore (native), Pub/Sub topics for
# the domain events, a least-privilege service account + IAM, a Secret Manager secret,
# and two Cloud Run services (API + Web). No credentials are stored in this file.

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- Enabled APIs ---------------------------------------------------------
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudtrace.googleapis.com",
    "aiplatform.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# --- Artifact Registry ----------------------------------------------------
resource "google_artifact_registry_repository" "swarmops" {
  location      = var.region
  repository_id = "swarmops"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

# --- Firestore (native mode) ---------------------------------------------
resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  depends_on  = [google_project_service.apis]
}

# --- Pub/Sub topics for domain events ------------------------------------
resource "google_pubsub_topic" "events" {
  for_each = toset([
    "AgentDiscovered", "RiskAssessmentCompleted", "AgentQuarantined",
    "ApprovalRequested", "ApprovalGranted", "ToolCallCompleted", "ExecutionCompleted",
  ])
  name       = "swarmops-${each.value}"
  depends_on = [google_project_service.apis]
}

# --- Service account for Cloud Run ---------------------------------------
resource "google_service_account" "run" {
  account_id   = "swarmops-run"
  display_name = "SwarmOps Cloud Run service account"
}

resource "google_project_iam_member" "run_roles" {
  for_each = toset([
    "roles/datastore.user",              # Firestore
    "roles/pubsub.publisher",            # event bus
    "roles/secretmanager.secretAccessor",
    "roles/cloudtrace.agent",            # OpenTelemetry export
    "roles/aiplatform.user",             # Gemini via Vertex AI
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.run.email}"
}

# --- Secret Manager (value set out of band; never in Terraform) ----------
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "swarmops-jwt-secret"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

# --- Cloud Run: API -------------------------------------------------------
resource "google_cloud_run_v2_service" "api" {
  name     = "swarmops-api"
  location = var.region

  template {
    service_account = google_service_account.run.email
    scaling {
      min_instance_count = 0 # scale to zero to keep costs near zero
      max_instance_count = 4
    }
    containers {
      image = var.api_image
      ports {
        container_port = 8080
      }
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "PERSISTENCE_BACKEND"
        value = "firestore"
      }
      env {
        name  = "EVENT_BUS"
        value = "pubsub"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "true"
      }
      env {
        name  = "GEMINI_MODEL"
        value = var.gemini_model
      }
      env {
        name  = "OTEL_ENABLED"
        value = "true"
      }
    }
  }
  depends_on = [google_project_service.apis, google_firestore_database.default]
}

# --- Cloud Run: Web -------------------------------------------------------
resource "google_cloud_run_v2_service" "web" {
  name     = "swarmops-web"
  location = var.region

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 4
    }
    containers {
      image = var.web_image
      ports {
        container_port = 3000
      }
      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.api.uri
      }
    }
  }
  depends_on = [google_project_service.apis]
}

# --- Public access (demo) -------------------------------------------------
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  count    = var.allow_unauthenticated ? 1 : 0
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "web_public" {
  count    = var.allow_unauthenticated ? 1 : 0
  location = var.region
  name     = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
