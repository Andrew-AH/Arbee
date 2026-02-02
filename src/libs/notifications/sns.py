import boto3
import json

from libs.utils.env import (
    AWS_DEFAULT_REGION,
    AWS_SNS_OPPS_TOPIC_ARN,
)
from libs.utils.log import get_logger

log = get_logger(logs_to_file=True, logs_to_console=True)

sns_client = boto3.client("sns", region_name=AWS_DEFAULT_REGION)


def publish_to_sns(message):
    try:
        # Publish the message to the SNS topic
        log.info("Publishing to SNS..")
        response = sns_client.publish(
            TopicArn=AWS_SNS_OPPS_TOPIC_ARN,
            Message=json.dumps(message),
            MessageAttributes={
                "ContentType": {"DataType": "String", "StringValue": "application/json"}
            },
        )
        log.info(f"Message sent! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Failed to publish message: {e}")
