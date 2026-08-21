output "api_url" {
  value       = google_cloud_run_v2_service.api.uri
  description = "Public URL of the SwarmOps API on Cloud Run."
}

output "web_url" {
  value       = google_cloud_run_v2_service.web.uri
  description = "Public URL of the SwarmOps web console on Cloud Run."
}

output "artifact_registry" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.swarmops.repository_id}"
  description = "Artifact Registry path to push images to."
}

output "run_service_account" {
  value = google_service_account.run.email
}
