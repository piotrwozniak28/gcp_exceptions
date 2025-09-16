output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "applied_policy_overrides" {
  description = "List of organization policies that have been overridden"
  value = [
    for policy in var.org_policy_overrides : {
      constraint   = policy.constraint
      policy_type  = policy.policy_type
      enforced     = policy.enforced
      allow        = policy.allow
      deny         = policy.deny
      allow_all    = policy.allow_all
      deny_all     = policy.deny_all
      description  = policy.description
    }
  ]
}

output "policy_override_count" {
  description = "Number of organization policy overrides applied"
  value       = length(var.org_policy_overrides)
}