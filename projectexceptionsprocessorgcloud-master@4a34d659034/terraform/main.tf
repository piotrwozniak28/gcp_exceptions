terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Organization Policy Overrides - Boolean Policies
resource "google_project_organization_policy" "boolean_policies" {
  for_each = {
    for idx, policy in var.org_policy_overrides : policy.constraint => policy
    if policy.policy_type == "boolean"
  }

  project    = var.project_id
  constraint = each.value.constraint

  boolean_policy {
    enforced = each.value.enforced
  }
}

# Organization Policy Overrides - List Policies (Allow All)
resource "google_project_organization_policy" "list_policies_allow_all" {
  for_each = {
    for idx, policy in var.org_policy_overrides : policy.constraint => policy
    if policy.policy_type == "list" && policy.allow_all == true
  }

  project    = var.project_id
  constraint = each.value.constraint

  list_policy {
    allow {
      all = true
    }
  }
}

# Organization Policy Overrides - List Policies (Deny All)
resource "google_project_organization_policy" "list_policies_deny_all" {
  for_each = {
    for idx, policy in var.org_policy_overrides : policy.constraint => policy
    if policy.policy_type == "list" && policy.deny_all == true
  }

  project    = var.project_id
  constraint = each.value.constraint

  list_policy {
    deny {
      all = true
    }
  }
}

# Organization Policy Overrides - List Policies (Allow Values)
resource "google_project_organization_policy" "list_policies_allow_values" {
  for_each = {
    for idx, policy in var.org_policy_overrides : policy.constraint => policy
    if policy.policy_type == "list" && try(length(policy.allow), 0) > 0
  }

  project    = var.project_id
  constraint = each.value.constraint

  list_policy {
    allow {
      values = each.value.allow
    }
  }
}

# Organization Policy Overrides - List Policies (Deny Values)
resource "google_project_organization_policy" "list_policies_deny_values" {
  for_each = {
    for idx, policy in var.org_policy_overrides : policy.constraint => policy
    if policy.policy_type == "list" && try(length(policy.deny), 0) > 0
  }

  project    = var.project_id
  constraint = each.value.constraint

  list_policy {
    deny {
      values = each.value.deny
    }
  }
}