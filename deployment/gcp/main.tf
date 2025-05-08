# VidID GCP Terraform Configuration

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# VPC Network
resource "google_compute_network" "vidid_network" {
  name                    = "vidid-network-${var.environment}"
  auto_create_subnetworks = false
}

# Subnet for VidID services
resource "google_compute_subnetwork" "vidid_subnet" {
  name          = "vidid-subnet-${var.environment}"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vidid_network.id
}

# Firewall rule for VidID API
resource "google_compute_firewall" "vidid_api_firewall" {
  name    = "vidid-api-firewall-${var.environment}"
  network = google_compute_network.vidid_network.id

  allow {
    protocol = "tcp"
    ports    = ["8000", "80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["vidid-api"]
}

# Firewall rule for Cloud SQL
resource "google_compute_firewall" "vidid_db_firewall" {
  name    = "vidid-db-firewall-${var.environment}"
  network = google_compute_network.vidid_network.id

  allow {
    protocol = "tcp"
    ports    = ["5432"]
  }

  source_tags = ["vidid-api"]
  target_tags = ["vidid-db"]
}

# Cloud SQL PostgreSQL instance
resource "google_sql_database_instance" "vidid_postgres" {
  name             = "vidid-postgres-${var.environment}"
  database_version = "POSTGRES_13"
  region           = var.region

  settings {
    tier = var.db_machine_type

    ip_configuration {
      ipv4_enabled    = true
      private_network = google_compute_network.vidid_network.id
    }

    backup_configuration {
      enabled            = true
      start_time         = "02:00"
      binary_log_enabled = false
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }

  deletion_protection = true
}

# PostgreSQL database
resource "google_sql_database" "vidid_db" {
  name     = "vidid"
  instance = google_sql_database_instance.vidid_postgres.name
}

# Database user
resource "google_sql_user" "vidid_db_user" {
  name     = var.db_username
  instance = google_sql_database_instance.vidid_postgres.name
  password = var.db_password
}

# GCS bucket for video storage
resource "google_storage_bucket" "video_storage" {
  name          = "vidid-video-storage-${var.environment}-${var.project_id}"
  location      = var.region
  force_destroy = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  uniform_bucket_level_access = true
}

# GCS bucket for feature vectors
resource "google_storage_bucket" "feature_vectors" {
  name          = "vidid-feature-vectors-${var.environment}-${var.project_id}"
  location      = var.region
  force_destroy = false
  uniform_bucket_level_access = true
}

# Cloud Run service for VidID API
resource "google_cloud_run_service" "vidid_api" {
  name     = "vidid-api-${var.environment}"
  location = var.region

  template {
    spec {
      containers {
        image = var.api_image

        resources {
          limits = {
            cpu    = "2.0"
            memory = "4Gi"
          }
        }

        env {
          name  = "VIDID_DB_URL"
          value = "postgresql://${var.db_username}:${var.db_password}@${google_sql_database_instance.vidid_postgres.private_ip_address}:5432/vidid"
        }

        env {
          name  = "VIDID_ENV"
          value = var.environment
        }

        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }

        env {
          name  = "VIDEO_STORAGE_BUCKET"
          value = google_storage_bucket.video_storage.name
        }

        env {
          name  = "FEATURE_VECTOR_BUCKET"
          value = google_storage_bucket.feature_vectors.name
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"      = "10"
        "autoscaling.knative.dev/minScale"      = "1"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.vidid_postgres.connection_name
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}

# Cloud Run service IAM binding
resource "google_cloud_run_service_iam_member" "vidid_api_public" {
  location = google_cloud_run_service.vidid_api.location
  service  = google_cloud_run_service.vidid_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Service account for VidID API
resource "google_service_account" "vidid_service_account" {
  account_id   = "vidid-service-account-${var.environment}"
  display_name = "VidID Service Account for ${var.environment}"
}

# Grant access to GCS buckets
resource "google_storage_bucket_iam_member" "service_account_video_storage" {
  bucket = google_storage_bucket.video_storage.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.vidid_service_account.email}"
}

resource "google_storage_bucket_iam_member" "service_account_feature_vectors" {
  bucket = google_storage_bucket.feature_vectors.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.vidid_service_account.email}"
}

# Vertex AI custom job for background processing
resource "google_vertex_ai_endpoint" "vidid_endpoint" {
  name         = "vidid-endpoint-${var.environment}"
  display_name = "VidID Endpoint for ${var.environment}"
  location     = var.region
}

# Cloud Scheduler for periodic tasks
resource "google_cloud_scheduler_job" "vidid_scheduler" {
  name        = "vidid-scheduler-job-${var.environment}"
  description = "Triggers VidID scheduled tasks"
  schedule    = "0 */4 * * *"  # Every 4 hours
  region      = var.region

  http_target {
    uri         = "${google_cloud_run_service.vidid_api.status[0].url}/api/scheduler/trigger"
    http_method = "POST"
    oidc_token {
      service_account_email = google_service_account.vidid_service_account.email
    }
  }
}

# Output values
output "db_instance_connection_name" {
  value = google_sql_database_instance.vidid_postgres.connection_name
}

output "db_instance_ip" {
  value = google_sql_database_instance.vidid_postgres.private_ip_address
}

output "video_storage_bucket" {
  value = google_storage_bucket.video_storage.name
}

output "feature_vectors_bucket" {
  value = google_storage_bucket.feature_vectors.name
}

output "api_url" {
  value = google_cloud_run_service.vidid_api.status[0].url
}
