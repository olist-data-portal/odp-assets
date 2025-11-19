variable "prefix" {
  description = "Resource name prefix"
  type        = string
  default     = "twitch-dp"
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}


variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
}

variable "prefix_list_ids" {
  description = "Prefix list IDs for ALB security group"
  type        = list(string)
  default     = []
}

variable "dagster_postgres_db" {
  description = "Dagster DB name"
  type        = string
  default     = "dagster"
}

variable "dagster_postgres_user" {
  description = "Dagster DB username"
  type        = string
  default     = "dagster_user"
}

variable "dbt_env_secret_bigquery_project" {
  description = "DBT env secret BigQuery project ID"
  type        = string
}

variable "dbt_env_secret_bigquery_dataset" {
  description = "DBT env secret BigQuery dataset name (legacy, kept for backward compatibility)"
  type        = string
  default     = ""
}

variable "dbt_env_secret_bigquery_location" {
  description = "DBT env secret BigQuery location"
  type        = string
  default     = "asia-northeast1"
}

variable "dbt_environments" {
  description = "List of environment names for DBT (e.g., ['dev', 'prod'])"
  type        = list(string)
  default     = ["dev"]
}

variable "dbt_model_directories" {
  description = "List of model directory names for DBT (e.g., ['staging', 'models'])"
  type        = list(string)
  default     = ["staging", "models"]
}

variable "dataset_prefix" {
  description = "Prefix for BigQuery dataset names"
  type        = string
  default     = "dp"
}