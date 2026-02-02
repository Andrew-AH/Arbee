import json
from datetime import datetime
from queue import Queue
from threading import Thread
from typing import Optional

from db.config import get_db_engine
from db.repository import Repository
from groubee.assessor import assess
from groubee.config import LISTENER_HOST, LISTENER_PORT
from groubee.listener import start_listener
from groubee.utils.aws import SnsClient
from groubee.utils.ngrok import generate_public_url_from
from groubee.utils.sheet import update_todays_balance
from jobs.save_races import (
    ENRICHED_VENUES_PATH,
    FILE_NAME,
    S3_BUCKET,
    load_enriched_venues,
)
from libs.config.preferences import (
    BUY_AMOUNT,
    FAKE_TRADE_SUCCESSES,
    MAXIMUM_NO_SAME_FAILED_OPPORTUNITIES,
    MAXIMUM_NO_SAME_SUCCESS_OPPORTUNITIES,
    MAXIMUM_INVESTED_ON_AN_EVENT,
)
from libs.interfaces.executor import (
    VendorPricesHaveChangedException,
    ItemCouldNotBeClickedException,
)
from libs.models.opportunity import Opportunity
from libs.notifications.messages import make_execution_success_message
from libs.notifications.telegram import notify_telegram
from libs.utils.enums import Vendor, Service
from libs.utils.env import AWS_SNS_OPPS_TOPIC_ARN, VENDOR_ALPHA_USER, DB_URL, MACHINE
from libs.utils.log import get_logger
from libs.utils.provider import get_service
from libs.utils.s3 import download_file_from_s3
from libs.vendors.vendor_alpha.executor import VendorAlphaExecutor, InsufficientBalanceException
from libs.vendors.vendor_beta.client import VendorBetaOrderFailedToPlaceException
from libs.vendors.vendor_beta.utils import UnhandledVendorBetaOrderStatusException

log = get_logger(logs_to_file=True, logs_to_console=True)

# Setup - Shared variables
opp_queue = Queue(maxsize=1)
success_opportunities_hashes = {}
failed_opportunities_hashes = {}
current_invested_on_each_event = {}


def main(vendor: Vendor):
    # Setup - Repository
    repository = Repository(get_db_engine(DB_URL))

    # Setup - SQS Listener
    start_listener(opp_queue)
    public_base_url = generate_public_url_from(f"{LISTENER_HOST}:{LISTENER_PORT}")
    sns_client = SnsClient()
    subscription_arn = sns_client.subscribe_and_wait_for_confirmation(
        endpoint_url=f"{public_base_url}/message",
        topic_arn=AWS_SNS_OPPS_TOPIC_ARN,
        timeout=30,
    )

    # Setup - Executor
    download_file_from_s3(S3_BUCKET, FILE_NAME, ENRICHED_VENUES_PATH)
    enriched_venues = load_enriched_venues()
    first_event = next((events[0][0] for events in enriched_venues.values() if events), None)
    executor_class = get_service(vendor, Service.EXECUTOR)
    executor = executor_class(initial_url=first_event, buy_amount=BUY_AMOUNT)

    # Setup - Counter Variables
    no_success_trades = 0
    no_failed_trades = 0

    # Sending current vendor balance to telegram
    log.info("Sending current balance to Telegram!")
    current_date = datetime.today().strftime("%d/%m/%Y")
    balance = (
        executor.vendor_alpha_client.balance()
    )  # NOTE: Using `exec.vendor_alpha_client` here is not generic, room for improvement
    message = f"Balance Update!\n  -  Date: {current_date}\n  -  User: {VENDOR_ALPHA_USER}\n  -  Vendor: {vendor.value}\n  -  Balance: ${balance}"
    notify_telegram(message)
    log.info(f"Successfully sent current balance to Telegram with message:\n{message}")

    # Track stats asynchronously
    Thread(target=update_todays_balance, args=(VENDOR_ALPHA_USER, balance, BUY_AMOUNT, MACHINE)).start()
    Thread(target=repository.save_account_to_db, args=(VENDOR_ALPHA_USER,)).start()
    Thread(target=repository.save_machine_to_db, args=(MACHINE,)).start()

    try:
        while True:
            opp = opp_queue.get()
            # NOTE: json.loads() needs to be called twice when the msg is received from SNS it's wrapped twice
            opp_dict = json.loads(json.loads(opp))
            opp: Opportunity = Opportunity.from_dict_of_strings(opp_dict)
            log.info(f"Received opportunity: {opp}")

            processed = process_op(executor, opp)

            # None indicates opportunity is skipped
            if processed is None:
                continue

            # True indicates a successful trade
            if processed:
                no_success_trades += 1
                log.info("Trade successful!")

                # Persist asynchronously
                Thread(
                    target=repository.save_transaction_to_db,
                    args=(
                        opp,
                        BUY_AMOUNT,
                        VENDOR_ALPHA_USER,
                        MACHINE,
                        datetime.now(),
                    ),
                ).start()

            # False indicates a failed trade
            else:
                no_failed_trades += 1
                log.info("Trade failed")

            log.info(f"Success trades: {no_success_trades} | Failed trades: {no_failed_trades}")

    except KeyboardInterrupt:
        sns_client.unsubscribe(subscription_arn)
        log.info("Closing listener..")


def process_op(executor: VendorAlphaExecutor, opportunity: Opportunity) -> Optional[bool]:
    """
    Processes an opportunity by assessing it against a certain criteria and then executing it.
    Returns True if opportunity successfully executes and resulting in a profit.
    Returns False if opportunity failed to execute and a small loss is incurred.
    Returns None if opportunity is skipped.
    """
    try:
        log.info("Processing opportunity:")
        log.info(opportunity)

        event = f"{opportunity.venue_name} {opportunity.au_event_time.strftime('%H:%M')}"

        opportunity_hash = opportunity.get_item_name_hash()

        # Checks if opportunity has succeeded too many times
        if (
            success_opportunities_hashes.get(opportunity_hash, 0)
            >= MAXIMUM_NO_SAME_SUCCESS_OPPORTUNITIES
        ):
            log.info(
                f"Skip opportunity because it has already succeeded {MAXIMUM_NO_SAME_SUCCESS_OPPORTUNITIES} times"
            )
            return None

        # Checks if opportunity has already failed too many times
        if (
            failed_opportunities_hashes.get(opportunity_hash, 0)
            >= MAXIMUM_NO_SAME_FAILED_OPPORTUNITIES
        ):
            log.info(
                f"Skip opportunity because it has been failed {MAXIMUM_NO_SAME_FAILED_OPPORTUNITIES} times"
            )
            return None

        # Checks if event has already too much invested on it
        if current_invested_on_each_event.get(event, 0) >= MAXIMUM_INVESTED_ON_AN_EVENT:
            log.info(
                f"Skip opportunity because total investment for {event} has reached ${MAXIMUM_INVESTED_ON_AN_EVENT}"
            )
            return None

        (should_trade, no_trade_reason) = assess(opportunity)

        if not should_trade:
            log.info(f"Skip opportunity because {no_trade_reason}")
            return None

        try:
            if FAKE_TRADE_SUCCESSES:
                executed = True
                message = make_execution_success_message(
                    venue_name=opportunity.venue_name,
                    event_time=opportunity.au_event_time,
                    profit_in_dollars=opportunity.profit_in_dollars,
                    percentage_return=opportunity.percentage_return,
                    item=opportunity.vendor_alpha_standard_item_name,
                    sell_price=opportunity.vendor_beta_sell_price,
                    sell_amount=opportunity.vendor_beta_sell_amount,
                    sell_liquidity=opportunity.vendor_beta_sell_liquidity,
                    buy_price=opportunity.vendor_alpha_buy_price,
                    buy_amount=opportunity.vendor_alpha_buy_amount,
                    detected_timestamp=opportunity.detected_timestamp,
                    executed_timestamp=datetime.now(),
                )
                executor.notify(message)

            else:
                executed = executor.execute(opportunity)

            log.info("Executed opportunity")

            # Record opportunity if successfully executed
            if executed:
                if opportunity_hash in success_opportunities_hashes:
                    success_opportunities_hashes[opportunity_hash] += 1
                else:
                    success_opportunities_hashes[opportunity_hash] = 1

                if event in current_invested_on_each_event:
                    current_invested_on_each_event[event] += BUY_AMOUNT

                else:
                    current_invested_on_each_event[event] = BUY_AMOUNT

            # Record failed opportunity if failed to execute
            else:
                if opportunity_hash in failed_opportunities_hashes:
                    failed_opportunities_hashes[opportunity_hash] += 1
                else:
                    failed_opportunities_hashes[opportunity_hash] = 1

            return executed

        except (
            InsufficientBalanceException,
            VendorPricesHaveChangedException,
            ItemCouldNotBeClickedException,
            VendorBetaOrderFailedToPlaceException,
        ) as e:
            log.exception(e)

        except UnhandledVendorBetaOrderStatusException:
            raise

    except Exception as e:
        message = f"Processing failed, shutting down. Exception thrown {e}"
        log.exception(message)
        notify_telegram(message)
        opp_queue.queue.clear()
        quit()


if __name__ == "__main__":
    main(vendor=Vendor.VENDOR_ALPHA)
