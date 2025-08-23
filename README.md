# GCP Project Exceptions Processor

Generates Terraform variables based on exceptions schema.

## Setup

### Python Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## Usage

```bash
# Process exceptions using example schema file (for testing/validation only)
python3 process_exceptions.py \
  --schema-file-path exceptions_schema.example.json \
  --project-id "prj-rad-01-fanta-qwe" \
  --output-file terraform/terraform.tfvars.json

# Process exceptions using JSON string
python3 process_exceptions.py \
  --schema-json-string '{"version":"1.0.0","exceptions":[...]}' \
  --project-id "prj-rad-01-fanta-qwe" \
  --output-file output/vars.json
```

> **Note**: The script performs validation and generates `terraform.tfvars.json` but does NOT run terraform.
> Use `exceptions_schema.example.json` for testing. For production changes, modify `exceptions_schema.json` (without the .example part).

## exceptions_schema.json

Exception IDs must be exactly 3 digits (e.g., "100", "042").

```json
{
  "version": "1.0.0",
  "exceptions": [
    {
      "id": "100",
      "type": "create_service_accounts",
      "project_id_regex": "^lab-(dev|test)-.*$",
      "description": "Lab environment service accounts",
      "spec": {
        "service_accounts": [
          {
            "name_suffix": "api",
            "description": "API service account",
            "create_json_key": true,
            "iam_roles": ["roles/viewer"]
          }
        ]
      }
    }
  ]
}
```

## Schema

<details>
<summary>JSON Schema</summary>

```json
{
  "$defs": {
    "Exception": {
      "description": "Exception rule that matches project IDs against regex patterns and defines service accounts to create.\n\nWhen a GCP project ID matches the project_regex pattern, all service accounts defined in the spec\nwill be created with their specified configurations.",
      "properties": {
        "id": {
          "description": "Unique identifier for this exception rule",
          "examples": [
            "100",
            "200",
            "003"
          ],
          "pattern": "^\\d{3}$",
          "title": "Id",
          "type": "string"
        },
        "type": {
          "const": "create_service_accounts",
          "description": "Type of exception - currently only 'create_service_accounts' is supported",
          "title": "Type",
          "type": "string"
        },
        "project_id_regex": {
          "description": "Regular expression pattern to match against GCP project IDs. When a project ID matches this pattern, the service accounts defined in 'spec' will be created.",
          "examples": [
            "^lab-(xcs|xxx|rad)-client2$",
            "^prod-.*$",
            "^dev-team-[0-9]+$"
          ],
          "minLength": 1,
          "title": "Project Id Regex",
          "type": "string"
        },
        "description": {
          "description": "Human-readable description of what this exception rule does",
          "examples": [
            "Create service accounts for lab environment projects",
            "Production environment service account setup"
          ],
          "minLength": 1,
          "title": "Description",
          "type": "string"
        },
        "spec": {
          "$ref": "#/$defs/ServiceAccountSpec",
          "description": "Specification of what service accounts to create when this exception matches"
        }
      },
      "required": [
        "id",
        "type",
        "project_id_regex",
        "description",
        "spec"
      ],
      "title": "Exception",
      "type": "object"
    },
    "ServiceAccount": {
      "description": "Service account specification defining what to create and configure.\n\nThis model represents a single service account that will be created in GCP\nwhen the parent exception matches a project ID.",
      "properties": {
        "name_suffix": {
          "description": "Name suffix for the service account (will be prefixed with base name in actual GCP)",
          "examples": [
            "data",
            "comp",
            "brow"
          ],
          "maxLength": 4,
          "minLength": 1,
          "pattern": "^[a-z](?:[-a-z0-9]*[a-z0-9])?$",
          "title": "Name Suffix",
          "type": "string"
        },
        "iam_roles": {
          "description": "List of IAM roles to assign to this service account",
          "examples": [
            [
              "roles/viewer"
            ],
            [
              "roles/editor",
              "roles/storage.objectViewer"
            ]
          ],
          "items": {
            "type": "string"
          },
          "minItems": 1,
          "title": "Iam Roles",
          "type": "array"
        },
        "create_json_key": {
          "description": "Whether to generate a JSON key for this service account and store it in Google Secret Manager. Set to true for service accounts that need downloadable credentials, false for those using workload identity or other authentication methods.",
          "examples": [
            true,
            false
          ],
          "title": "Create Json Key",
          "type": "boolean"
        },
        "description": {
          "default": "",
          "description": "Optional description for the service account explaining its purpose",
          "examples": [
            "Data processing service account",
            "Admin service account",
            ""
          ],
          "maxLength": 256,
          "title": "Description",
          "type": "string"
        }
      },
      "required": [
        "name_suffix",
        "iam_roles",
        "create_json_key"
      ],
      "title": "ServiceAccount",
      "type": "object"
    },
    "ServiceAccountSpec": {
      "description": "Specification of what service accounts to create when an exception matches.",
      "properties": {
        "service_accounts": {
          "description": "List of service accounts to create for matching projects",
          "items": {
            "$ref": "#/$defs/ServiceAccount"
          },
          "minItems": 1,
          "title": "Service Accounts",
          "type": "array"
        }
      },
      "required": [
        "service_accounts"
      ],
      "title": "ServiceAccountSpec",
      "type": "object"
    }
  },
  "description": "Root schema defining project-specific service account creation exceptions for Terraform automation.\n\nThis schema controls which GCP service accounts are created and whether JSON keys are generated\nand stored in Secret Manager. The processor matches project IDs against regex patterns to determine\nwhich service accounts need to be created.",
  "properties": {
    "version": {
      "description": "Schema version for compatibility tracking (semantic versioning: MAJOR.MINOR.PATCH)",
      "examples": [
        "1.0.0",
        "1.1.0",
        "2.0.0"
      ],
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "title": "Version",
      "type": "string"
    },
    "exceptions": {
      "description": "List of exception rules that match project IDs against regex patterns and define service accounts to create. Rules are processed in order, and multiple rules can match the same project.",
      "items": {
        "$ref": "#/$defs/Exception"
      },
      "minItems": 1,
      "title": "Exceptions",
      "type": "array"
    }
  },
  "required": [
    "version",
    "exceptions"
  ],
  "title": "ExceptionsSchema",
  "type": "object"
}
```

</details>
