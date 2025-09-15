"""
Pydantic models for exceptions schema validation and documentation generation.
"""

from typing import List, Literal
from pydantic import BaseModel, Field
import re
import logging


class ServiceAccount(BaseModel):
    """
    Service account specification defining what to create and configure.
    
    This model represents a single service account that will be created in GCP
    when the parent exception matches a project ID.
    """
    
    name_suffix: str = Field(
        ...,
        description="Name suffix for the service account (will be prefixed with base name in actual GCP)",
        min_length=1,
        max_length=4,
        pattern=r'^[a-z](?:[-a-z0-9]*[a-z0-9])?$',
        examples=["data", "comp", "brow"]
    )
    
    iam_roles: List[str] = Field(
        ...,
        description="List of IAM roles to assign to this service account",
        min_length=1,
        examples=[["roles/viewer"], ["roles/editor", "roles/storage.objectViewer"]]
    )
    
    create_json_key: bool = Field(
        ...,
        description=(
            "Whether to generate a JSON key for this service account and store it in Google Secret Manager. "
            "Set to true for service accounts that need downloadable credentials, "
            "false for those using workload identity or other authentication methods."
        ),
        examples=[True, False]
    )
    
    description: str = Field(
        "",
        description="Optional description for the service account explaining its purpose",
        max_length=256,
        examples=["Data processing service account", "Admin service account", ""]
    )


class ServiceAccountSpec(BaseModel):
    """
    Specification of what service accounts to create when an exception matches.
    """
    
    service_accounts: List[ServiceAccount] = Field(
        ...,
        description="List of service accounts to create for matching projects",
        min_length=1
    )


class Exception(BaseModel):
    """
    Exception rule that matches project IDs against regex patterns and defines service accounts to create.
    
    When a GCP project ID matches the project_regex pattern, all service accounts defined in the spec
    will be created with their specified configurations.
    """
    
    id: str = Field(
        ...,
        description="Unique identifier for this exception rule",
        pattern=r'^\d{3}$',
        examples=["100", "200", "003"]
    )
    
    type: Literal["create_service_accounts"] = Field(
        ...,
        description="Type of exception - currently only 'create_service_accounts' is supported"
    )
    
    project_id_regex: str = Field(
        ...,
        description=(
            "Regular expression pattern to match against GCP project IDs. "
            "When a project ID matches this pattern, the service accounts defined in 'spec' will be created."
        ),
        min_length=1,
        examples=["^lab-(xcs|xxx|rad)-client2$", "^prod-.*$", "^dev-team-[0-9]+$"]
    )
    
    description: str = Field(
        ...,
        description="Human-readable description of what this exception rule does",
        min_length=1,
        examples=[
            "Create service accounts for lab environment projects",
            "Production environment service account setup"
        ]
    )
    
    spec: ServiceAccountSpec = Field(
        ...,
        description="Specification of what service accounts to create when this exception matches"
    )
    
    def validate_regex(self) -> 'Exception':
        """Validate that project_id_regex is a valid regular expression."""
        try:
            re.compile(self.project_id_regex)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{self.project_id_regex}': {e}")
        return self


class ExceptionsSchema(BaseModel):
    """
    Root schema defining project-specific service account creation exceptions for Terraform automation.
    
    This schema controls which GCP service accounts are created and whether JSON keys are generated
    and stored in Secret Manager. The processor matches project IDs against regex patterns to determine
    which service accounts need to be created.
    """
    
    version: str = Field(
        ...,
        description="Schema version for compatibility tracking (semantic versioning: MAJOR.MINOR.PATCH)",
        pattern=r'^\d+\.\d+\.\d+$',
        examples=["1.0.0", "1.1.0", "2.0.0"]
    )
    
    exceptions: List[Exception] = Field(
        ...,
        description=(
            "List of exception rules that match project IDs against regex patterns and define service accounts to create. "
            "Rules are processed in order, and multiple rules can match the same project."
        ),
        min_length=0
    )
    
    def validate_unique_ids(self) -> 'ExceptionsSchema':
        """Validate that all exception IDs are unique."""
        ids = [exc.id for exc in self.exceptions]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate exception IDs found: {set(duplicates)}")
        return self


# Example usage and validation
def validate_schema_file(file_path: str) -> ExceptionsSchema:
    """Validate a schema file and return the parsed model."""
    import json
    logger = logging.getLogger(__name__)
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    return ExceptionsSchema.model_validate(data)


if __name__ == "__main__":
    # Configure logging for standalone execution
    import time
    logging.Formatter.converter = time.gmtime  # Use UTC time
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ'
    )
    logger = logging.getLogger(__name__)
    
    # Test validation with current schema
    try:
        schema = validate_schema_file("exceptions_schema.json")
        logger.info(f"Schema validation successful! Found {len(schema.exceptions)} exceptions.")
        
        # Show what would be created
        for exc in schema.exceptions:
            logger.info(f"  - {exc.id}: {len(exc.spec.service_accounts)} service accounts")
            
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")