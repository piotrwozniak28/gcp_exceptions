terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
  
  backend "gcs" {
    bucket = "buc-tfstate"
    prefix = "terraform/state"
  }
}

resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"
}

provider "google" {
  project = var.project_id
}

locals {
  base_name_google_service_account = join("-", ["srva", "rad", "01", "dsgcl2919", "ody"])
  
  # Single map for all service accounts
  all_service_accounts = {
    for sa in var.service_accounts :
    "${local.base_name_google_service_account}-${sa.name_suffix}" => sa
  }
  
  # Filter for service accounts that need JSON keys
  sa_with_keys_map = {
    for sa_name, sa_details in local.all_service_accounts :
    sa_name => sa_details
    if sa_details.create_json_key
  }
}

resource "google_service_account" "exception_sa" {
  for_each = local.all_service_accounts

  account_id   = each.key
  display_name = "${each.key} (Managed by Exception)"
  description  = each.value.description
}

resource "google_service_account_key" "exception_sa_key" {
  for_each = local.sa_with_keys_map

  service_account_id = google_service_account.exception_sa[each.key].id
}

resource "google_secret_manager_secret" "sa_key_secret" {
  for_each = local.sa_with_keys_map

  project   = var.project_id
  secret_id = "sa-key-${each.key}"

  expire_time = timeadd(timestamp(), "3660s")
  version_destroy_ttl = "86400s"

  labels = {
    ccoe_service_account_name = each.key
    # Extension time when secret expires. Supported units: m (minutes), h (hours), d (days)
    # Examples: "30m", "1h", "12h", "1d", "7d", "365d" - unit is required
    ccoe_expiration_extension_time = "5m"
  }

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]

  lifecycle {
    ignore_changes = [expire_time]
  }
}

resource "google_secret_manager_secret_version" "sa_key_secret_version" {
  for_each = local.sa_with_keys_map

  secret      = google_secret_manager_secret.sa_key_secret[each.key].id
  secret_data = google_service_account_key.exception_sa_key[each.key].private_key
}

resource "google_project_iam_member" "exception_sa_roles" {
  for_each = {
    for pair in flatten([
      for sa_name, sa_details in local.all_service_accounts : [
        for role in sa_details.iam_roles : {
          sa_name = sa_name
          role    = role
        }
      ]
    ]) : "${pair.sa_name}-${pair.role}" => pair
  }

  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.exception_sa[each.value.sa_name].email}"
}

output "gcloud_secret_access_commands" {
  description = "Commands to access service account keys from Secret Manager"
  value = {
    for sa_name in keys(local.sa_with_keys_map) : sa_name => 
    "gcloud secrets versions access latest --secret='sa-key-${sa_name}' --project='${var.project_id}'"
  }
}

output "service_account_emails" {
  description = "Created service account email addresses"
  value = {
    for sa_name in keys(local.all_service_accounts) : sa_name => 
    google_service_account.exception_sa[sa_name].email
  }
}