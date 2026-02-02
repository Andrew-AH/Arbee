import requests

from libs.utils.env import TELEGRAM_AUTH_TOKEN, TELEGRAM_CHAT_ID
from libs.utils.log import get_logger

log = get_logger(logs_to_file=True, logs_to_console=True)


def notify_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_AUTH_TOKEN}/sendMessage"
    data = {
        "chat_id": f"{TELEGRAM_CHAT_ID}",
        "text": message,
    }

    response = requests.post(url, data=data)

    if response.status_code == 200:
        log.info("Telegram message sent successfully!")
    else:
        log.error(
            f"Failed to send telegram message: {response.status_code} - {response.text}"
        )
