# VidID GCP Terraform Variables

variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The Google Cloud region to deploy resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The Google Cloud zone to deploy resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "The deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The environment must be one of: dev, staging, prod."
  }
}

variable "db_username" {
  description = "The PostgreSQL database username"
  type        = string
  default     = "vidid"
}

variable "db_password" {
  description = "The PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "db_machine_type" {
  description = "The Cloud SQL instance machine type"
  type        = string
  default     = "db-g1-small"
}

variable "api_image" {
  description = "The Docker image URL for the VidID API"
  type        = string
  default     = "gcr.io/PROJECT_ID/vidid-api:latest"
}

variable "min_instances" {
  description = "Minimum number of instances for the API service"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of instances for the API service"
  type        = number
  default     = 10
}
