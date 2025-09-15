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

### Python 3.12 Virtual Environment

```bash
# Create virtual environment
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install requirements
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Usage

```bash
# Process exceptions using example schema file (for testing/validation only)
python3 process_exceptions.py \\
  --schema-file-path exceptions_schema.example.json \\
  --project-id "prj-rad-01-fanta-qwe" \\
  --output-file terraform.tfvars.json

# Process exceptions using JSON string
python3 process_exceptions.py \\
  --schema-json-string '{{"version":"1.0.0","exceptions":[...]}}' \\
  --project-id "prj-rad-01-fanta-qwe" \\
  --output-file terraform.tfvars.json
```

> **Note**: The script performs validation and generates `terraform.tfvars.json` but does NOT run terraform.
> Use `exceptions_schema.example.json` for testing. For production changes, modify `exceptions_schema.json` (without the .example part).

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
    import time
    logging.Formatter.converter = time.gmtime
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