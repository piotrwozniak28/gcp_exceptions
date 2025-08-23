variable "service_accounts" {
  description = "A list of service accounts to create. JSON keys will be created conditionally based on create_json_key flag."
  type = list(object({
    name_suffix     = string
    iam_roles       = list(string)
    create_json_key = bool
    description     = string
  }))
  default = []
}

variable "project_id" {
  description = "The GCP project ID where resources will be created."
  type        = string
}


