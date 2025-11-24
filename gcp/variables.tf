variable "project_id" {
  description = "GCPプロジェクトID"
  type        = string
  default     = "olist-data-portal"
}

variable "region" {
  description = "GCPリージョン"
  type        = string
  default     = "asia-northeast1"
}

variable "resource_prefix" {
  description = "リソース名のプレフィックス"
  type        = string
  default     = "odp"
}

variable "environment" {
  description = "環境（dev, prd）"
  type        = string
  default     = "prd"
}

