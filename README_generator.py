#!/usr/bin/env python3
"""
Generate documentation.
"""

import json
import logging
from datetime import datetime
from schema_models import ExceptionsSchema


def generate_simple_docs():
    """Generate simple, concise documentation."""
    logger = logging.getLogger(__name__)
    
    # Generate JSON schema from Pydantic models
    json_schema = ExceptionsSchema.model_json_schema()
    logger.debug("Generated JSON schema from Pydantic models")
    
    # Create simple Markdown documentation
    md = f"""# GCP Project Exceptions Processor

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
python3 process_exceptions.py \\
  --schema-file-path exceptions_schema.example.json \\
  --project-id "prj-rad-01-fanta-qwe" \\
  --output-file terraform/terraform.tfvars.json

# Process exceptions using JSON string
python3 process_exceptions.py \\
  --schema-json-string '{{"version":"1.0.0","exceptions":[...]}}' \\
  --project-id "prj-rad-01-fanta-qwe" \\
  --output-file output/vars.json
```

> **Note**: The script performs validation and generates `terraform.tfvars.json` but does NOT run terraform.
> Use `exceptions_schema.example.json` for testing. For production changes, modify `exceptions_schema.json` (without the .example part).

## exceptions_schema.json

Exception IDs must be exactly 3 digits (e.g., "100", "042").

```json
{{
  "version": "1.0.0",
  "exceptions": [
    {{
      "id": "100",
      "type": "create_service_accounts",
      "project_id_regex": "^lab-(dev|test)-.*$",
      "description": "Lab environment service accounts",
      "spec": {{
        "service_accounts": [
          {{
            "name_suffix": "api",
            "description": "API service account",
            "create_json_key": true,
            "iam_roles": ["roles/viewer"]
          }}
        ]
      }}
    }}
  ]
}}
```

## Schema

<details>
<summary>JSON Schema</summary>

```json
{json.dumps(json_schema, indent=2)}
```

</details>
"""
    
    return md


if __name__ == "__main__":
    # Configure logging
    import time
    logging.Formatter.converter = time.gmtime  # Use UTC time
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Generating simple documentation...")
    
    docs = generate_simple_docs()
    
    with open("README.md", "w") as f:
        f.write(docs)
    
    logger.info("Simple documentation generated: README.md")