from time import time, sleep
import boto3

from libs.utils.env import AWS_DEFAULT_REGION
from libs.utils.log import get_logger


class SnsClient:
    def __init__(self):
        self.client = boto3.client("sns", region_name=AWS_DEFAULT_REGION)
        self.log = get_logger(logs_to_console=True)

    def subscribe_and_wait_for_confirmation(
        self, endpoint_url: str, topic_arn: str, timeout: int
    ) -> str:
        try:
            response = self.client.subscribe(
                TopicArn=topic_arn, Protocol="https", Endpoint=endpoint_url
            )
            subscription_arn = response["SubscriptionArn"]
            self.log.info(f"Initial SubscriptionArn: {subscription_arn}")

            start_time = time()
            while (time() - start_time) < timeout:
                response = self.client.list_subscriptions_by_topic(TopicArn=topic_arn)
                subscriptions = response.get("Subscriptions", [])
                for sub in subscriptions:
                    if sub["Endpoint"] == endpoint_url:
                        current_arn = sub["SubscriptionArn"]
                        if sub["SubscriptionArn"] != "PendingConfirmation":
                            self.log.info(
                                f"Subscription confirmed with ARN: {current_arn}"
                            )
                            return current_arn

                # Poll every second for confirmation
                sleep(1)

        except Exception as e:
            self.log.error(f"Error subscribing to topic: {e}")
            raise e

    def unsubscribe(self, subscription_arn: str):
        try:
            self.client.unsubscribe(SubscriptionArn=subscription_arn)
            self.log.info(f"Unsubscribed from ARN: {subscription_arn}")
        except Exception as e:
            self.log.error(f"Error unsubscribing: {e}")


if __name__ == "__main__":
    client = SnsClient()

    client.subscribe_and_wait_for_confirmation("asd", "asd", 1)
