import json
import re
import argparse
import logging
from pathlib import Path
from schema_models import ExceptionsSchema

def process_exceptions(schema_data: dict, project_id: str, output_path: Path):
    """Processes the exceptions schema and generates a Terraform variables file."""
    logger = logging.getLogger(__name__)
    logger.info(f"Processing exceptions for project ID: '{project_id}'")
    
    try:
        full_schema = ExceptionsSchema.model_validate(schema_data)
        logger.info(f"Full schema validation successful! Version: {full_schema.version}")
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise ValueError(f"Invalid schema: {e}")
    
    valid_exceptions = full_schema.exceptions
    exception_ids = [exc.id for exc in valid_exceptions]
    logger.info(f"Processing {len(valid_exceptions)} exceptions: {exception_ids}")

    service_accounts = []
    iam_policy_overrides = []
    matched_exceptions = []
    
    for exception in valid_exceptions:
        if re.match(exception.project_id_regex, project_id):
            logger.info(f"Exception '{exception.id}' matches (regex: '{exception.project_id_regex}')")
            matched_exceptions.append(exception.id)
            
            if exception.type == "create_service_accounts":
                for sa in exception.spec.service_accounts:
                    sa_dict = sa.model_dump()
                    if sa_dict not in service_accounts:
                        service_accounts.append(sa_dict)
            elif exception.type == "override_iam_policies":
                for policy in exception.spec.boolean_policy_overrides:
                    policy_dict = policy.model_dump()
                    if policy_dict not in iam_policy_overrides:
                        iam_policy_overrides.append(policy_dict)
        else:
            logger.info(f"Exception '{exception.id}' does not match (regex: '{exception.project_id_regex}')")
    
    # Summary
    if matched_exceptions:
        logger.info(f"Found {len(matched_exceptions)} matching exception(s): {matched_exceptions}")
        logger.info(f"Total service accounts to create: {len(service_accounts)}")
        logger.info(f"Total IAM policy overrides to apply: {len(iam_policy_overrides)}")
    else:
        logger.info("No exceptions matched the project ID")

    terraform_vars = {
        "project_id": project_id,
        "region": region,
        "service_accounts": service_accounts,
        "iam_policy_overrides": iam_policy_overrides,
    }

    with open(output_path, 'w') as f:
        json.dump(terraform_vars, f, indent=4)
    logger.info(f"Successfully generated Terraform variables at: {output_path}")



def setup_logging():
    """Configure logging with appropriate format and level."""
    import time
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ'
    )

region="europe-west4"

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser(description="Process GCP project exceptions and generate Terraform variables.")
    
    schema_group = parser.add_mutually_exclusive_group(required=True)
    schema_group.add_argument("--schema-file-path", type=Path, help="Path to the exceptions JSON schema file.")
    schema_group.add_argument("--schema-json-string", type=str, help="Raw JSON string containing the exceptions schema.")
    
    parser.add_argument("--project-id", type=str, required=True, help="The GCP project ID to evaluate.")
    parser.add_argument("--output-file", type=Path, default="terraform.tfvars.json", help="Path for the output terraform.tfvars.json file.")
    
    args = parser.parse_args()

    if args.schema_file_path:
        logger.info(f"Loading schema from file: {args.schema_file_path}")
        with open(args.schema_file_path, 'r') as f:
            schema_data = json.load(f)
    else:
        logger.info("Loading schema from JSON string")
        try:
            schema_data = json.loads(args.schema_json_string)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in --schema-json-string: {e}")
            exit(1)

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    process_exceptions(schema_data, args.project_id, args.output_file)