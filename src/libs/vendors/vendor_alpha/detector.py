from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from itertools import cycle
from multiprocessing import Queue
from threading import Event, Thread
from typing import List, Tuple

from cloubee.math.arbitrage import (
    calculate_sell_amount,
    calculate_liability,
    calculate_profit,
    calculate_roi,
)
from cloubee.math.criteria import (
    opportunity_is_not_detected,
    buy_price_exceeds_acceptable_limit,
    data_is_stale,
)
from libs.config.preferences import (
    BUY_AMOUNT,
    COMMISSION,
    MAXIMUM_ACCEPTABLE_BUY_PRICE,
    MINIMUM_ACCEPTABLE_PROFIT,
)
from libs.interfaces.detector import VendorDetector
from libs.models.odds import PriceData
from libs.models.opportunity import Opportunity
from libs.notifications.disc import run_live_status_tracker
from libs.utils.log import get_logger
from libs.vendors.vendor_alpha.scraper import VendorAlphaScraper
from libs.vendors.vendor_beta.client import VendorBetaClient
from libs.vendors.vendor_beta.utils import OrderType

# Setup
# =============================================================================
log = get_logger(logs_to_file=True, logs_to_console=True)
scraper_log = get_logger("scraper", logs_to_file=True, logs_to_console=False)

# =============================================================================
# Configurations
# =============================================================================
MAXIMUM_ACCEPTABLE_DATA_TIME_DIFFERENCE = timedelta(seconds=5)
MINIMUM_TIME_TO_JUMP = timedelta(minutes=2)


class VendorAlphaDetector(VendorDetector):
    def detect_venue_opps_cyclic(
        self,
        opp_queue: Queue,
        venue_name: str,
        suffix: int,
        events: List[Tuple[str, int, int, datetime]],
    ) -> None:
        try:
            vendor_beta_client = VendorBetaClient()
            vendor_alpha_scraper = VendorAlphaScraper()

            infinite_events = cycle(events)

            # Track online status in the background
            offline_event = Event()
            Thread(
                target=run_live_status_tracker,
                args=(
                    offline_event,
                    f"{venue_name} - {suffix}",
                ),
            ).start()

            log.info("Begin scraping..")
            while events:
                event = next(infinite_events)
                vendor_alpha_event_url = event[0]
                vendor_beta_market_id = event[1]
                event_date_time = event[3]
                if event_date_time < datetime.now():
                    events.remove(event)
                    if not events:
                        log.info(f"All events completed for venue: {venue_name}")
                        return
                    infinite_events = cycle(events)
                    continue

                vendor_alpha_scraper.navigate_url(vendor_alpha_event_url)

                try:
                    with ThreadPoolExecutor() as executor:
                        vendor_beta_future = executor.submit(
                            fetch_vendor_beta_prices, vendor_beta_client, vendor_beta_market_id
                        )
                        vendor_alpha_future = executor.submit(fetch_vendor_alpha_prices, vendor_alpha_scraper)

                        vendor_beta_data = vendor_beta_future.result()
                        vendor_alpha_data = vendor_alpha_future.result()

                    vendor_beta_time: datetime = vendor_beta_data.timestamp
                    vendor_alpha_time: datetime = vendor_alpha_data.timestamp

                    vendor_beta_prices = vendor_beta_data.data
                    vendor_alpha_prices = vendor_alpha_data.data

                    if not vendor_beta_prices or not vendor_alpha_prices:
                        if not vendor_alpha_prices:
                            scraper_log.warning(
                                f"No VENDOR_ALPHA prices scraped for {venue_name} {event_date_time.time()}"
                            )
                        if not vendor_beta_prices:
                            scraper_log.warning(
                                f"No VENDOR_BETA prices scraped for {venue_name} {event_date_time.time()}"
                            )
                        continue

                    scraper_log.info(
                        f"SCRAPED: {venue_name} {event_date_time.time()}\n{vendor_beta_prices}\n{vendor_alpha_prices}"
                    )

                    time_difference: timedelta = abs(vendor_beta_time - vendor_alpha_time)

                    if data_is_stale(time_difference, MAXIMUM_ACCEPTABLE_DATA_TIME_DIFFERENCE):
                        continue

                    # Only consider the intersection of items to work around issue of inconsistent cancelled items
                    common_items = vendor_alpha_prices.keys() & vendor_beta_prices.keys()

                    for item in common_items:
                        buy_price = vendor_alpha_prices[item]
                        sell_price = vendor_beta_prices[item][0]
                        sell_liquidity = vendor_beta_prices[item][1]

                        if opportunity_is_not_detected(sell_price, buy_price):
                            continue

                        profit = calculate_profit(BUY_AMOUNT, buy_price, sell_price, COMMISSION)

                        if profit < MINIMUM_ACCEPTABLE_PROFIT:
                            continue

                        rounded_sell_amount = calculate_sell_amount(
                            BUY_AMOUNT, buy_price, sell_price, COMMISSION, rounded=True
                        )

                        sell_amount = calculate_sell_amount(
                            BUY_AMOUNT, buy_price, sell_price, COMMISSION
                        )

                        log.info(
                            f"OPPORTUNITY DETECTED - VENUE: {venue_name} PROFIT: {profit} | ITEM: {item} | BUY: ${BUY_AMOUNT} @ {buy_price} | SELL: ${rounded_sell_amount} @ {sell_price} | SELL LIQUIDITY: ${sell_liquidity}"
                        )

                        opp = Opportunity(
                            venue_name=venue_name,
                            au_event_time=event_date_time,
                            vendor_beta_market_id=vendor_beta_market_id,
                            vendor_beta_item_id=vendor_beta_client.get_item_selection_ids(
                                vendor_beta_market_id
                            )[item],
                            vendor_beta_sell_price=sell_price,
                            vendor_beta_sell_amount=rounded_sell_amount,
                            vendor_beta_sell_liquidity=sell_liquidity,
                            vendor_alpha_url=vendor_alpha_event_url,
                            vendor_alpha_standard_item_name=item,
                            vendor_alpha_buy_price=buy_price,
                            vendor_alpha_buy_amount=BUY_AMOUNT,
                            vendor_beta_balance_required=calculate_liability(
                                sell_amount, sell_price, rounded=True
                            ),
                            profit_in_dollars=profit,
                            percentage_return=calculate_roi(BUY_AMOUNT, profit),
                            detected_timestamp=datetime.now(),
                        )

                        if buy_price_exceeds_acceptable_limit(
                            opp.vendor_alpha_buy_price, MAXIMUM_ACCEPTABLE_BUY_PRICE
                        ):
                            log.info("Skipping sending message because buy price exceeds limit")
                        else:
                            opp_queue.put_nowait(opp)

                except Exception as e:
                    log.exception(f"Exception thrown: {e}")

        except Exception as e:
            log.exception(f"Exception thrown: {e}")
        finally:
            offline_event.set()


# Define a function to fetch prices from Vendor Beta
def fetch_vendor_beta_prices(vendor_beta_client: VendorBetaClient, market_id: str):
    return PriceData(
        timestamp=datetime.now(),
        data=vendor_beta_client.get_item_prices(market_id, OrderType.SELL),
    )


# Define a function to fetch prices from Vendor Alpha
def fetch_vendor_alpha_prices(vendor_alpha_scraper: VendorAlphaScraper):
    return vendor_alpha_scraper.get_current_item_prices()
