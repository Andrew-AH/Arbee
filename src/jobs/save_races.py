from datetime import datetime
import json
import os
import re
from threading import Thread
from time import sleep
from typing import Dict, List, Tuple

from selenium_driverless.types.by import By

from db.config import get_db_engine
from libs.notifications.disc import notify_daily_events_channel
from libs.notifications.messages import make_todays_events_message
from libs.utils.datetimes import (
    DateTimeDecoder,
    DateTimeEncoder,
    determine_execution_date,
)
from libs.utils.env import DB_URL
from libs.utils.log import get_logger
from libs.utils.retry import retry_on_exception
from libs.utils.s3 import download_file_from_s3, file_exists_in_s3, upload_file_to_s3
from libs.vendors.vendor_alpha.urls import (
    get_url_for_vendor_alpha_today_page,
    get_url_for_vendor_alpha_tomorrow_page,
)
from libs.vendors.vendor_alpha.layout import XPath
from libs.vendors.vendor_alpha.scraper import VendorAlphaScraper
from libs.vendors.vendor_beta.client import VendorBetaClient
from db.repository import Repository

execution_date = determine_execution_date()

LOCAL_DIR = "data"
FILE_NAME = f"{execution_date}_enriched_venues.json"
ENRICHED_VENUES_PATH = os.path.join(LOCAL_DIR, FILE_NAME)
DEFAULT_TIMEOUT = 10
S3_BUCKET = "data-pipeline"


log = get_logger(logs_to_file=True, logs_to_console=True)


def load_enriched_venues() -> Dict[str, List[Tuple[str, int, int, datetime]]]:
    with open(ENRICHED_VENUES_PATH, "r") as file:
        return json.load(file, cls=DateTimeDecoder)


def generate_enriched_venues(skip_if_exists: bool = True) -> None:
    if os.path.exists(ENRICHED_VENUES_PATH) and skip_if_exists:
        log.info(f"Found {ENRICHED_VENUES_PATH}. Skipping file generation")
        return

    if file_exists_in_s3(S3_BUCKET, FILE_NAME):
        log.info("File exists in S3. Downloading...")
        download_file_from_s3(S3_BUCKET, FILE_NAME, ENRICHED_VENUES_PATH)

    else:
        log.info("File does not exist in S3. Generating enriched venues...")

        # Retry 100 times to bypass infinite spinner
        enriched_venues = retry_on_exception(
            lambda: get_enriched_venues(), delay=1, retries=100, logger=log
        )


        dump_enriched_venues_to_json(enriched_venues)

        upload_file_to_s3(S3_BUCKET, FILE_NAME, ENRICHED_VENUES_PATH)
        notify_daily_events_channel(make_todays_events_message(enriched_venues))

        repository = Repository(get_db_engine(DB_URL))
        Thread(target=repository.save_venues_to_db, args=(enriched_venues,)).start()


def dump_enriched_venues_to_json(
    enriched_venues: Dict[str, List[Tuple[str, str, str, datetime]]],
) -> None:
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(ENRICHED_VENUES_PATH), exist_ok=True)

    with open(ENRICHED_VENUES_PATH, "w") as json_file:
        json.dump(enriched_venues, json_file, indent=4, cls=DateTimeEncoder)

    log.info(f"Successfully dumped json file to {ENRICHED_VENUES_PATH}")


def get_enriched_venues() -> Dict[str, List[Tuple[str, str, str, datetime]]]:
    try:
        vendor_alpha = VendorAlphaScraper()
        vendor_beta = VendorBetaClient()

        enriched_venues = {}

        today_page = get_url_for_vendor_alpha_today_page()

        log.info("Navigating to today's page..")

        vendor_alpha.navigate_url(today_page)

        vendor_alpha.reject_cookies()

        log.info("Rejected cookies")

        __adjust_preferences(vendor_alpha)

        log.info("Unchecked non-UK market checkboxes")

        __enrich_venues_for_page(today_page, vendor_alpha, vendor_beta, enriched_venues)

        tomorrow_page = get_url_for_vendor_alpha_tomorrow_page()

        log.info("Navigating to tomorrow's page..")

        vendor_alpha.navigate_url(tomorrow_page)

        __enrich_venues_for_page(tomorrow_page, vendor_alpha, vendor_beta, enriched_venues)

        # Prune venues with empty events
        enriched_venues = {
            venue: events for venue, events in enriched_venues.items() if events != []
        }

        log.info("Successfully generated enriched venues")

        return enriched_venues

    finally:
        vendor_alpha.driver.quit()


def __adjust_preferences(vendor_alpha: VendorAlphaScraper) -> None:
    # Uncheck boxes that aren't UK market related
    sections = vendor_alpha.driver.find_elements(
        By.XPATH,
        "//section",
        timeout=DEFAULT_TIMEOUT,
    )

    checkboxes_section = sections[0]

    checkboxes = checkboxes_section.find_elements(By.XPATH, ".//label")

    for index, checkbox in enumerate(checkboxes):
        if index == 0 or index == 4:
            continue

        checkbox.click()


def __enrich_venues_for_page(
    initial_page: str,
    vendor_alpha: VendorAlphaScraper,
    vendor_beta: VendorBetaClient,
    enriched_venues: Dict[str, List[Tuple[str, str, str, datetime]]],
) -> None:
    headings = vendor_alpha.driver.find_elements(By.XPATH, "//h3", timeout=DEFAULT_TIMEOUT)

    for heading in headings:
        if heading.text == "UK & Ireland":
            uk_heading = heading

    venues = uk_heading.find_elements(By.XPATH, "../a")

    for index, venue in enumerate(venues):
        enriched_events = []
        headings = vendor_alpha.driver.find_elements(
            By.XPATH, "//h3", timeout=DEFAULT_TIMEOUT
        )

        for heading in headings:
            if heading.text == "UK & Ireland":
                uk_heading = heading

        venues = uk_heading.find_elements(By.XPATH, "../a")

        current_venue = venues[index]

        if "Resulted" not in current_venue.text:
            current_venue.click()

            sleep(2)

            events_section = vendor_alpha.driver.find_element(
                By.XPATH, "//section", timeout=DEFAULT_TIMEOUT
            )
            first_event = events_section.find_element(
                By.XPATH, ".//a", timeout=DEFAULT_TIMEOUT
            )
            first_event.click()

            sleep(2)

            # On first event for venue
            events = vendor_alpha.driver.find_element(
                By.XPATH, XPath.EVENT_NUMBERS_CONTAINER, timeout=DEFAULT_TIMEOUT
            ).children

            for i in range(len(events)):
                events = vendor_alpha.driver.find_element(
                    By.XPATH, XPath.EVENT_NUMBERS_CONTAINER, timeout=DEFAULT_TIMEOUT
                ).children

                # Event number is in the format "R1", "R2", etc.
                if re.match("R\d+", events[i].text):
                    events[i].click()

                    vendor_alpha.driver.sleep(2)

                    (venue, time) = vendor_alpha.get_event_info()

                    try:
                        (market_id, date_time) = vendor_beta.get_market_id_and_start_time(
                            venue_name=venue, time_str=time
                        )

                    except Exception as e:
                        log.error(f"Exception thrown: {e}")
                        log.error(
                            "This is likely due to vendor beta missing data for this event"
                        )
                        log.info(f"Skipping {venue} {time}")
                        continue

                    enriched_events.append(
                        (vendor_alpha.driver.current_url, market_id, venue, date_time)
                    )
                    log.info(f"Enriched {venue} {time}")

            if not enriched_venues.get(venue):
                enriched_venues[venue] = enriched_events

            vendor_alpha.navigate_url(initial_page)


if __name__ == "__main__":
    generate_enriched_venues(skip_if_exists=True)
