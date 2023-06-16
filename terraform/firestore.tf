resource "google_app_engine_application" "transcribe-app" {
  project     = var.project_id
  location_id = var.app_engine_location
  database_type = "CLOUD_FIRESTORE"
}
