variable "project_id" {
  description = "The GCP project ID where resources will be created"
  type        = string
}

variable "region" {
  description = "The GCP region where resources will be created"
  type        = string
  default     = "europe-west4"
}

variable "service_accounts" {
  description = "List of service accounts to create (handled by existing infrastructure)"
  type = list(object({
    name_suffix      = string
    iam_roles        = list(string)
    create_json_key  = bool
    description      = string
  }))
  default = []
}

variable "org_policy_overrides" {
  description = "List of organization policies to override at project level"
  type = list(object({
    constraint   = string
    policy_type  = string # "boolean", "list"
    enforced     = optional(bool)
    allow        = optional(list(string))
    deny         = optional(list(string))
    allow_all    = optional(bool)
    deny_all     = optional(bool)
    description  = string
  }))
  default = []
}