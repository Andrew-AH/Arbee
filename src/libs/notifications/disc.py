from datetime import datetime
import threading
from time import sleep
import requests

from discord import SyncWebhook, Embed

from libs.utils.env import (
    DISCORD_CLOUBEE_WEBHOOK_ID,
    DISCORD_CLOUBEE_WEBHOOK_TOKEN,
    DISCORD_DAILY_EVENTS_WEBHOOK_ID,
    DISCORD_DAILY_EVENTS_WEBHOOK_TOKEN,
    DISCORD_PLACED_ORDERS_WEBHOOK_ID,
    DISCORD_PLACED_ORDERS_WEBHOOK_TOKEN,
    MACHINE,
)
from libs.utils.log import get_logger


log = get_logger(logs_to_file=True, logs_to_console=True)


CLOUBEE_CHANNEL_WEBHOOK = SyncWebhook.from_url(
    f"https://discord.com/api/webhooks/{DISCORD_CLOUBEE_WEBHOOK_ID}/{DISCORD_CLOUBEE_WEBHOOK_TOKEN}"
)


def make_live_status_embed(status: str, color: int):
    embed = Embed(description=status, color=color, timestamp=datetime.now())
    embed.set_footer(text=f"Last checked on {MACHINE}")
    return embed


def run_live_status_tracker(
    offline_event: threading.Event,
    venue_name: str,
    frequency: int = 10,
):
    try:
        message = CLOUBEE_CHANNEL_WEBHOOK.send(
            username=venue_name,
            embed=make_live_status_embed("🟢 **Online**", color=0x2ECC71),
            wait=True,
        )
        message_id = message.id

        while not offline_event.is_set():
            try:
                sleep(frequency)
                CLOUBEE_CHANNEL_WEBHOOK.edit_message(
                    message_id=message_id,
                    embed=make_live_status_embed("🟢 **Online**", color=0x2ECC71),
                )
            except Exception as e:
                log.exception(f"Failed to update live status: {e}")

        try:
            CLOUBEE_CHANNEL_WEBHOOK.delete_message(message_id)
            CLOUBEE_CHANNEL_WEBHOOK.send(
                username=venue_name,
                embed=make_live_status_embed("⚪ **Offline**", color=0xE6E7E8),
            )
        except Exception as e:
            log.exception(f"Failed to clean up live status: {e}")

    except Exception as e:
        log.exception(f"Initial setup of live status tracker failed: {e}")


def notify_cloubee_channel(message: str):
    notify_discord(
        message=message,
        webhook_id=DISCORD_CLOUBEE_WEBHOOK_ID,
        webhook_token=DISCORD_CLOUBEE_WEBHOOK_TOKEN,
    )


def notify_daily_events_channel(message: str):
    notify_discord(
        message=message,
        webhook_id=DISCORD_DAILY_EVENTS_WEBHOOK_ID,
        webhook_token=DISCORD_DAILY_EVENTS_WEBHOOK_TOKEN,
    )


def notify_placed_orders_channel(message: str):
    # Leaving this here until team gets their webhooks set up
    if DISCORD_PLACED_ORDERS_WEBHOOK_ID and DISCORD_PLACED_ORDERS_WEBHOOK_TOKEN:
        notify_discord(
            message=message,
            webhook_id=DISCORD_PLACED_ORDERS_WEBHOOK_ID,
            webhook_token=DISCORD_PLACED_ORDERS_WEBHOOK_TOKEN,
        )


def notify_discord(message: str | dict, webhook_id: str, webhook_token: str):
    WEBHOOK_URL = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}"

    # If the message is a string, convert it to a dictionary
    payload = message if isinstance(message, dict) else {"content": message}
    response = requests.post(WEBHOOK_URL, json=payload)

    if response.status_code == 204:
        log.info("Discord message sent successfully!")
    else:
        log.error(
            f"Failed to send discord message: {response.status_code} - {response.text}"
        )
