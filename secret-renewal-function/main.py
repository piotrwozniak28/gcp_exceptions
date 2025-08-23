import json
import logging
import base64
import re
from datetime import datetime, timedelta, timezone
from google.cloud import secretmanager
from google.cloud import iam_admin_v1
import functions_framework

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_time_duration(duration_str):
    """
    Parse duration string like '1h', '2d', '30m', '1.5d' into days.
    Returns float representing days.
    Units are required for clarity.
    """
    if not duration_str:
        raise ValueError("Duration string is empty")
    
    # Parse with time units (required)
    match = re.match(r'^(\d*\.?\d+)([dhm])$', duration_str.lower())
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}. Must include time unit. Use formats like '1h', '2d', '30m'")
    
    value, unit = match.groups()
    value = float(value)
    
    if unit == 'd':  # days
        return value
    elif unit == 'h':  # hours
        return value / 24.0
    elif unit == 'm':  # minutes
        return value / (24.0 * 60.0)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")


@functions_framework.cloud_event
def handle_secret_expiration(cloud_event):
    """
    Cloud Run function to handle secret expiration events.
    Creates a new service account key and updates the secret with the new key.
    Only processes secrets with required ccoe_* labels: ccoe_service_account_name and ccoe_expiration_extension_time.
    """
    try:
        logger.info("Secret renewal function triggered - only processing secrets with required ccoe_* labels: ccoe_service_account_name and ccoe_expiration_extension_time")
        # Parse the Cloud Event
        event_data = cloud_event.data
        logger.info(f"Received event: {json.dumps(event_data, indent=2)}")
        
        # Extract relevant information from the log entry
        json_payload = event_data.get('jsonPayload', {})
        resource_labels = event_data.get('resource', {}).get('labels', {})
        
        # Check if this is an EXPIRES_IN_1_HOUR event
        event_type = json_payload.get('type')
        if event_type != 'EXPIRES_IN_1_HOUR':
            logger.info(f"Ignoring event type: {event_type}")
            return "OK"
        
        # Extract secret information
        secret_name = json_payload.get('name')  # Full secret path
        secret_id = resource_labels.get('secret_id')
        project_number = resource_labels.get('resource_container').replace('projects/', '')
        
        # Extract project ID from log name (e.g., "projects/lab-xcs-client2/logs/...")
        log_name = event_data.get('logName', '')
        project_id = log_name.split('/')[1] if '/logs/' in log_name else None
        
        if not all([secret_name, secret_id, project_number, project_id]):
            logger.error("Missing required information from event")
            return "ERROR: Missing required information"
        
        logger.info(f"Processing secret expiration for: {secret_id} in project: {project_id} (number: {project_number})")
        
        # Get the secret to retrieve the service account name from labels
        secret_client = secretmanager.SecretManagerServiceClient()
        secret_resource = secret_client.get_secret(name=secret_name)
        
        ccoe_service_account_name = secret_resource.labels.get('ccoe_service_account_name')
        ccoe_expiration_extension_time_str = secret_resource.labels.get('ccoe_expiration_extension_time')
        
        # Only process secrets that have both required ccoe_* labels
        if not ccoe_service_account_name or not ccoe_expiration_extension_time_str:
            logger.info(f"Ignoring secret: has_ccoe_service_account_name={bool(ccoe_service_account_name)}, has_ccoe_expiration_extension_time={bool(ccoe_expiration_extension_time_str)} for secret: {secret_id}")
            return "OK"
        
        # Parse expiration extension from label (required)
        try:
            expiration_extension_time = parse_time_duration(ccoe_expiration_extension_time_str)
        except ValueError as e:
            logger.error(f"Invalid ccoe_expiration_extension_time value '{ccoe_expiration_extension_time_str}': {e}")
            return "ERROR: Invalid ccoe_expiration_extension_time value"
        
        logger.info(f"Using expiration extension: {ccoe_expiration_extension_time_str}")
        
        logger.info(f"Found service account name: {ccoe_service_account_name}")
        
        # Create a new service account key
        iam_client = iam_admin_v1.IAMClient()
        service_account_email = f"{ccoe_service_account_name}@{project_id}.iam.gserviceaccount.com"
        service_account_resource = f"projects/{project_id}/serviceAccounts/{service_account_email}"
        
        logger.info(f"Creating new key for service account: {service_account_email}")
        
        # Create the key
        request = iam_admin_v1.CreateServiceAccountKeyRequest(
            name=service_account_resource,
            private_key_type=iam_admin_v1.ServiceAccountPrivateKeyType.TYPE_GOOGLE_CREDENTIALS_FILE
        )
        
        key_response = iam_client.create_service_account_key(request=request)
        
        # The key data comes as bytes, we need to base64 encode it to match Terraform format
        key_data = base64.b64encode(key_response.private_key_data).decode('utf-8')
        
        logger.info("Successfully created new service account key")
        
        # Create a new version of the secret with the new key
        logger.info(f"Adding new version to secret: {secret_id}")
        
        response = secret_client.add_secret_version(
            request={
                "parent": secret_name,
                "payload": {"data": key_data.encode("utf-8")},
            }
        )
        
        logger.info(f"Successfully created new secret version: {response.name}")
        logger.info(f"Access new secret version with: gcloud secrets versions access latest --secret='{secret_id}' --project='{project_id}'")
        
        # Extend the secret's expiration from current expiration time
        current_expiration = secret_resource.expire_time
        logger.info(f"Current secret expiration: {current_expiration}")
        
        # Parse current expiration and extend by configured duration
        if current_expiration:
            # Convert protobuf timestamp to datetime
            current_exp_dt = current_expiration.replace(tzinfo=timezone.utc)
            new_expiration = current_exp_dt + timedelta(days=expiration_extension_time)
            new_expiration_str = new_expiration.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
            logger.info(f"Extending secret expiration from {current_expiration} to: {new_expiration_str} (+{ccoe_expiration_extension_time_str})")
        else:
            logger.error("No current expiration time found on secret")
            return "ERROR: No current expiration time found"
        
        # Update the secret with new expiration time
        update_request = secretmanager.UpdateSecretRequest(
            secret=secretmanager.Secret(
                name=secret_name,
                expire_time=new_expiration_str
            ),
            update_mask={"paths": ["expire_time"]}
        )
        
        updated_secret = secret_client.update_secret(request=update_request)
        logger.info(f"Successfully extended secret expiration from {current_expiration} to: {updated_secret.expire_time}")
        
        return "OK"
        
    except Exception as e:
        logger.error(f"Error processing secret expiration: {str(e)}", exc_info=True)
        return f"ERROR: {str(e)}"


if __name__ == "__main__":
    # For local testing
    import os
    os.environ["FUNCTIONS_SIGNATURE_TYPE"] = "cloudevent"
    
    # Mock event for testing with real infrastructure data
    # Project ID: lab-xcs-client2, Project Number: 401870235293
    mock_event_data = {
        "jsonPayload": {
            "@type": "type.googleapis.com/google.cloud.secretmanager.logging.v1.SecretEvent",
            "name": "projects/401870235293/secrets/sa-key-srva-rad-01-dsgcl2919-ody-brow",
            "type": "EXPIRES_IN_1_HOUR",
            "logMessage": "Secret projects/401870235293/secrets/sa-key-srva-rad-01-dsgcl2919-ody-brow is scheduled to be irreversibly deleted in 1 hour."
        },
        "resource": {
            "type": "secretmanager.googleapis.com/Secret",
            "labels": {
                "resource_container": "projects/401870235293",
                "secret_id": "sa-key-srva-rad-01-dsgcl2919-ody-brow",
                "location": "global"
            }
        },
        "timestamp": "2025-08-25T10:59:14.531612Z",
        "severity": "NOTICE",
        "logName": "projects/lab-xcs-client2/logs/secretmanager.googleapis.com%2Fsecret_event",
        "receiveTimestamp": "2025-08-25T10:59:15.169494932Z"
    }
    
    class MockCloudEvent:
        def __init__(self, data):
            self.data = data
    
    # Test the function
    result = handle_secret_expiration(MockCloudEvent(mock_event_data))
    print(f"Function result: {result}")