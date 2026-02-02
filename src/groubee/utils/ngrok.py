import ngrok

from libs.utils.log import get_logger

log = get_logger(logs_to_file=True, logs_to_console=True)


def generate_public_url_from(local_endpoint: str) -> str:
    # Open a ngrok tunnel to local http endpoint using NGROK_AUTHTOKEN from .env file
    listener = ngrok.forward(addr=local_endpoint, authtoken_from_env=True)
    log.info(f"Ingress established at: {listener.url()}")
    return listener.url()
