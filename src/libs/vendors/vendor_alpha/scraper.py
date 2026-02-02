from time import sleep
from datetime import datetime
from typing import Dict, List, Tuple
from multiprocessing import Process, Queue

from selenium_driverless.sync import webdriver
from selenium_driverless.types.by import By
from selenium.webdriver.support.ui import WebDriverWait

from libs.interfaces.detector import VendorDetector
from libs.interfaces.scraper import VendorScraper
from libs.utils.retry import retry_on_exception
from libs.vendors.vendor_alpha.layout import (
    ClassName,
    XPath,
)
from libs.models.odds import PriceData
from libs.utils.log import get_logger
from libs.utils.strings import standardize_string

DEFAULT_TIMEOUT = 10


class VendorAlphaScraper(VendorScraper):
    def __init__(self) -> None:
        self.log = get_logger()
        self.driver = self.__initialise_driver()
        self.wait = WebDriverWait(self.driver, DEFAULT_TIMEOUT)

    def get_current_item_prices(self) -> PriceData:
        return PriceData(timestamp=datetime.now(), data=self.__get_item_prices())

    def __initialise_driver(self) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.headless = True
        driver = retry_on_exception(
            lambda: webdriver.Chrome(options=options), logger=self.log
        )  # Has on occasion failed to initialise
        return driver

    def navigate_url(self, url: str) -> None:
        self.log.info(f"Navigating to: {url}")
        self.driver.get(url)
        self.driver.sleep(1)

    def get_event_info(self) -> tuple[str, str]:
        event_info = self.driver.find_element(
            By.XPATH, f".{XPath.EVENT_INFO}", timeout=DEFAULT_TIMEOUT
        ).children
        event_time = event_info[2].text
        venue_name = self.driver.find_element(
            By.XPATH, f".{XPath.VENUE_NAME}", timeout=DEFAULT_TIMEOUT
        ).text

        return venue_name, event_time

    def reject_cookies(self):
        reject_cookies_button = self.driver.find_element(
            By.XPATH, XPath.REJECT_COOKIES_BUTTON, timeout=DEFAULT_TIMEOUT
        )
        reject_cookies_button.click()

    def __get_item_elements(self) -> dict[str, float]:
        self.__refresh_page()

        sleep(1)

        item_elements = {}
        items = self.driver.find_elements(By.XPATH, XPath.RUNNER)

        for h in items:
            # if you want to query for child elements from a specific parent element, use By.CSS_SELECTOR
            name = standardize_string(
                h.find_element(
                    By.CSS_SELECTOR,
                    f".{ClassName.RUNNER_NAME_CLASS}",
                    timeout=DEFAULT_TIMEOUT,
                ).text
            )
            buy_price_element = h.find_element(By.CSS_SELECTOR, f".{ClassName.BUY_PRICE}")
            item_elements[name] = buy_price_element

        return item_elements

    def __get_item_prices(self) -> dict[str, float]:
        item_prices = {}
        try:
            item_elements = self.__get_item_elements()

            for item in item_elements:
                item_prices[item] = float(item_elements[item].text)

        except Exception as e:
            self.log.error(f"Exception thrown: {e}")

        return item_prices

    def __refresh_page(self) -> None:
        self.driver.refresh()
        sleep(4)


def start_cycling_scrapers_for_all_venues(
    detector: VendorDetector,
    venues: Dict[str, List[Tuple[str, int, str, datetime]]],
    processes: List[Process],
    queue: Queue,
    # True = split venues into two halves (e.g. venues 1-5 and venues 6-10 -> new behaviour)
    # False = do not split venues (e.g. venues 1-10 -> old behaviour)
    split_venues: bool = True,
    # Represents which half of the venues to scrape, only relevant if split_venues is True
    # True = first half of venues (e.g. venues 1-5)
    # False = second half of venues (e.g. venues 6-10)
    is_first_half: bool = True,
):
    # Filter out venues with no events
    non_empty_venue_items = [(name, events) for name, events in venues.items() if events]

    # Separate venues into two halves if needed
    if split_venues:
        mid = len(non_empty_venue_items) // 2
        if is_first_half:
            venue_items = non_empty_venue_items[:mid]
        else:
            venue_items = non_empty_venue_items[mid:]
    else:
        venue_items = non_empty_venue_items

    # 2 processes per venue (events in first half and events in second half)
    if split_venues:
        for _, event_urls in venue_items:
            venue_name = event_urls[0][2]
            mid = len(event_urls) // 2
            event_urls_first_half = event_urls[:mid]
            event_urls_second_half = event_urls[mid:]

            index = 0
            for split_event_urls in (event_urls_first_half, event_urls_second_half):
                index += 1
                if split_event_urls:
                    process = Process(
                        target=detector.detect_venue_opps_cyclic,
                        args=(queue, venue_name, index, split_event_urls),
                    )
                    processes.append(process)

    # 1 process per venue
    else:
        for _, event_urls in venue_items:
            venue_name = event_urls[0][2]
            process = Process(
                target=detector.detect_venue_opps_cyclic,
                args=(
                    queue,
                    venue_name,
                    event_urls,
                ),
            )
            processes.append(process)

    for process in processes:
        process.start()
