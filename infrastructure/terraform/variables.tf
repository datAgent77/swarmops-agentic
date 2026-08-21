variable "project_id" {
  type        = string
  description = "Google Cloud project id."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "Region for Cloud Run, Artifact Registry, and Firestore."
}

variable "api_image" {
  type        = string
  description = "Fully-qualified API container image (Artifact Registry)."
  # e.g. us-central1-docker.pkg.dev/PROJECT/swarmops/api:latest
}

variable "web_image" {
  type        = string
  description = "Fully-qualified Web container image (Artifact Registry)."
}

variable "gemini_model" {
  type    = string
  default = "gemini-3.5-flash"
}

variable "allow_unauthenticated" {
  type        = bool
  default     = true
  description = "Allow public access to the Cloud Run services (demo). Set false to lock down."
}
