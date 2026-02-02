from queue import Queue
from threading import Thread
from time import sleep

from flask import Flask, jsonify, request
import requests

from libs.utils.log import get_logger
from groubee.config import LISTENER_PORT, LISTENER_HOST

log = get_logger(logs_to_file=True, logs_to_console=True)


# Subclass Flask to allow queue to be attached
class Listener(Flask):
    queue: Queue = None

    def __init__(self, import_name: str, **kwargs):
        super().__init__(import_name, **kwargs)


listener = Listener(__name__)


@listener.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


@listener.route("/message", methods=["POST"])
def message():
    log.info(f"Received {request.method} request")

    try:
        payload = request.get_json(force=True)

        if payload.get("Type") == "Notification":
            content = payload.get("Message")
            log.info(f"Received Notification: {content}")
            listener.queue.put(content)
            return "", 204

        # Check if this is a SubscriptionConfirmation message
        if payload.get("Type") == "SubscriptionConfirmation":
            subscribe_url = payload.get("SubscribeURL")
            if subscribe_url:
                # Confirm the subscription by visiting the SubscribeURL
                response = requests.get(subscribe_url)
                if response.status_code == 200:
                    log.info("Subscription confirmed successfully.")
                    return "", 204
                else:
                    log.error(
                        f"Failed to confirm subscription. Status Code: {response.status_code}"
                    )
            else:
                log.error("SubscribeURL not found in the payload.")

    except Exception as e:
        log.error("Error parsing JSON:", e)

    return "", 400


def start_listener(queue: Queue):
    log.info("Starting up listener...")

    listener.queue = queue

    Thread(
        target=listener.run,
        kwargs={"host": LISTENER_HOST, "port": LISTENER_PORT},
        daemon=True,
    ).start()  # daemon ensures thread exits when main thread does

    sleep(5)

    # Blocking until endpoint is ready to receive requests
    while True:
        log.info("Waiting for listener to be ready...")
        response = requests.get(f"http://{LISTENER_HOST}:{LISTENER_PORT}/health")
        if response.status_code == 200:
            break
        sleep(1)

    log.info("Listener is ready!")
