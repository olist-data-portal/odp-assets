variable "prefix" {
    description = "Resource name prefix"
    type = string
    default = "twitch-dp"
}

variable "project_id" {
    description = "GCP Project ID"
    type = string
}

variable "region" {
    description = "GCP Region"
    type = string
    default = "asia-northeast1"
}