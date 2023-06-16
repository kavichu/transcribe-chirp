resource "google_storage_bucket" "function_bucket" {
    name     = "${var.project_id}-function"
    location = var.region
}

resource "google_storage_bucket" "transcribe_bucket" {
    name     = "${var.project_id}-transcribe"
    location = var.region
}