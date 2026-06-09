"""AWS Lambda Function for S3 Ingestion Notification forwarding.

Parses S3 ObjectCreated events, structures them according to the ingestion
webhook DTO contract, and forwards the payload to the configured API.
"""

import json
import logging
import os
import urllib.request
import urllib.error

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Retrieve configuration from environment variables
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev").lower()

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")


def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda entry point for processing S3 bucket upload notifications.

    Args:
        event: Dict containing the AWS event payload (S3 records).
        context: Lambda context object containing execution metadata.

    Returns:
        A dictionary containing the HTTP response status code and execution log.
    """
    logger.info("Received event: %s", json.dumps(event))

    records = event.get("Records", [])
    if not records:
        logger.warning("No S3 records found in event payload.")
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "No S3 records found in payload"})
        }

    successful_count = 0
    failed_count = 0
    errors = []

    # Iterate through all incoming S3 event records
    for record in records:
        s3_data = record.get("s3")
        if not s3_data:
            logger.warning("Record is missing S3 metadata: %s", record)
            continue

        bucket_name = s3_data.get("bucket", {}).get("name")
        object_key = s3_data.get("object", {}).get("key")

        if not bucket_name or not object_key:
            logger.warning("Incomplete S3 metadata in record: bucket=%s, key=%s", bucket_name, object_key)
            continue

        # Construct payload matching /data-hub/webhooks/s3-ingest contract
        payload = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": bucket_name},
                        "object": {"key": object_key}
                    }
                }
            ]
        }

        # Issue HTTP POST request using urllib to keep lambda dependency-free and cheap
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            logger.info("Forwarding ingestion notification to: %s for file: %s", WEBHOOK_URL, object_key)
            with urllib.request.urlopen(req, timeout=15) as response:
                resp_code = response.getcode()
                resp_body = response.read().decode("utf-8")
                logger.info("Webhook endpoint responded with status %d: %s", resp_code, resp_body)
                
                if 200 <= resp_code < 300:
                    successful_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Non-2xx response status: {resp_code}")
        except urllib.error.HTTPError as e:
            failed_count += 1
            err_msg = e.read().decode("utf-8")
            logger.error("HTTP Error forwarding S3 event: Code %d, Reason: %s", e.code, err_msg)
            errors.append(f"HTTP {e.code}: {err_msg}")
        except Exception as e:
            failed_count += 1
            logger.error("System error forwarding S3 event: %s", str(e))
            errors.append(str(e))

    result_summary = {
        "processed": len(records),
        "success": successful_count,
        "failed": failed_count,
        "errors": errors
    }
    logger.info("Execution complete: %s", json.dumps(result_summary))

    status_code = 200 if failed_count == 0 else 502
    return {
        "statusCode": status_code,
        "body": json.dumps(result_summary)
    }
