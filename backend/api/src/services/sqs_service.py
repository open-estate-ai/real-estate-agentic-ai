"""
SQS Service for sending messages to AWS SQS queues.

Handles message sending to SQS queues for asynchronous processing
by other services like the Planner Agent.
"""

import json
import logging
import os
import uuid
from typing import Any

import boto3

logger = logging.getLogger(__name__)

# SQS Configuration
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

# Global SQS client - initialized once
_sqs_client = None


def _get_sqs_client():
    """Get or create SQS client singleton."""
    global _sqs_client
    if _sqs_client is None:
        _sqs_client = boto3.client('sqs')
    return _sqs_client


class SQSService:
    """Service for sending messages to SQS queue."""

    @staticmethod
    def send_message_to_queue(payload: dict) -> dict[str, str]:
        """
        Send message to SQS queue.

        Args:
            payload: Dictionary containing job_id, user_id, and request_payload

        Returns:
            Dictionary containing SQS response information

        Raises:
            ValueError: If SQS_QUEUE_URL is not configured
            Exception: If SQS message sending fails
        """
        if not SQS_QUEUE_URL:
            logger.error(
                "SQS_QUEUE_URL not configured for production environment")
            raise ValueError("SQS configuration missing")

        try:
            # Get SQS client (singleton)
            sqs = _get_sqs_client()

            # Use the provided payload directly
            job_id = payload.get("job_id")
            user_id = payload.get("user_id")

            logger.info(f"Sending message to SQS queue for job_id={job_id}")
            logger.debug(f"Message payload: {payload}")

            # Send message to SQS
            response = sqs.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps(payload),
                MessageAttributes={
                    'job_id': {
                        'StringValue': job_id,
                        'DataType': 'String'
                    },
                    'user_id': {
                        'StringValue': user_id or 'anonymous',
                        'DataType': 'String'
                    }
                }
            )

            logger.info(
                f"Successfully sent message to SQS - MessageId: {response.get('MessageId')}")
            logger.debug(f"Full SQS Response: {response}")

            # MD5OfBody might not be present in all cases
            if 'MD5OfBody' in response:
                logger.info(f"SQS Response: MD5={response['MD5OfBody']}")

            return {
                "sqs_message_id": response.get("MessageId", "unknown"),
                "md5_of_body": response.get("MD5OfBody", "")
            }

        except Exception as sqs_error:
            job_id = payload.get("job_id", "unknown")
            logger.error(
                f"Failed to send message to SQS for job_id={job_id}: {sqs_error}")
            logger.exception("Full exception details:")
            raise
