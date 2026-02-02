from datetime import datetime

from libs.interfaces.executor import (
    VendorExecutor,
    VendorPricesHaveChangedException,
    ItemCouldNotBeClickedException,
)
from libs.notifications.disc import notify_placed_orders_channel
from libs.utils.env import VENDOR_ALPHA_USER, MACHINE
from libs.vendors.vendor_alpha.layout import (
    XPath,
)
from libs.vendors.vendor_alpha.client import VendorAlphaClient
from libs.vendors.vendor_beta.client import VendorBetaClient
from selenium_driverless.types.by import By
from selenium_driverless.types.webelement import NoSuchElementException
from libs.config.preferences import BUY_AMOUNT
from libs.models.opportunity import Opportunity
from libs.notifications.telegram import notify_telegram
from libs.utils.log import get_logger
from libs.utils.retry import retry_on_exception
from libs.notifications.messages import (
    make_execution_success_message,
    make_order_placed_message,
)

log = get_logger(logs_to_file=True, logs_to_console=True)


class InsufficientBalanceException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class VendorAlphaExecutor(VendorExecutor):
    def __init__(self, initial_url: str, buy_amount: int = 1):
        self.vendor_beta_client = VendorBetaClient()
        self.vendor_alpha_client = retry_on_exception(
            lambda: VendorAlphaClient(
                initial_url=initial_url, default_order_amount=buy_amount
            ),
            retries=10,
            delay=1,
            logger=log,
        )

    def execute(self, opportunity: Opportunity) -> bool:
        """
        Executes a given price arbitrage opportunity.
        Returns True if execution succeeds, resulting in a profit.
        Returns False if execution failed, incurring a small loss.
        """
        log.info("Executing on opportunity..")
        log.info(opportunity)

        venue_name = opportunity.venue_name
        event_time = opportunity.au_event_time
        sell_price = opportunity.vendor_beta_sell_price
        rounded_sell_amount = opportunity.vendor_beta_sell_amount
        sell_liquidity = opportunity.vendor_beta_sell_liquidity
        event_url = opportunity.vendor_alpha_url
        item = opportunity.vendor_alpha_standard_item_name
        buy_price = opportunity.vendor_alpha_buy_price
        buy_amount = opportunity.vendor_alpha_buy_amount
        profit = opportunity.profit_in_dollars
        roi = opportunity.percentage_return
        detected_timestamp = opportunity.detected_timestamp

        try:
            self.vendor_alpha_client.close_amountbox()

        except Exception as e:
            log.exception(f"No amount box to close: {e}")

        # Check if not logged in before executing
        try:
            login_button = self.vendor_alpha_client.driver.find_element(
                By.XPATH, XPath.LOGIN_BUTTON
            )

            if login_button:
                self.vendor_alpha_client.login()

        except NoSuchElementException:
            pass

        item_clicked = self.vendor_alpha_client.select_item(
            event_url=event_url, item_name=item
        )

        if not item_clicked:
            raise ItemCouldNotBeClickedException(
                "Failed to click item, aborting execution"
            )

        if self.vendor_alpha_client.prices_have_changed(desired_buy_price=buy_price):
            self.vendor_alpha_client.close_amountbox()
            raise VendorPricesHaveChangedException(
                "Prices have changed on Vendor Alpha, aborting execution"
            )

        self.vendor_alpha_client.verify_set_amount(default_amount=BUY_AMOUNT)

        vendor_alpha_order_placed = self.vendor_alpha_client.place_order(desired_buy_price=buy_price)

        executed_timestamp = datetime.now()

        if vendor_alpha_order_placed:
            message = make_execution_success_message(
                venue_name=venue_name,
                event_time=event_time,
                profit_in_dollars=profit,
                percentage_return=roi,
                item=item,
                sell_price=sell_price,
                sell_amount=rounded_sell_amount,
                sell_liquidity=sell_liquidity,
                buy_price=buy_price,
                buy_amount=buy_amount,
                detected_timestamp=detected_timestamp,
                executed_timestamp=executed_timestamp,
            )
            log.info(message)
            notify_telegram(message)
            notify_placed_orders_channel(
                make_order_placed_message(
                    venue_name=venue_name,
                    event_time=event_time,
                    item=item,
                    amount=BUY_AMOUNT,
                    profit_percentage=roi,
                    account_username=VENDOR_ALPHA_USER,
                    machine=MACHINE,
                    detected_timestamp=detected_timestamp,
                    executed_timestamp=executed_timestamp,
                )
            )
            self.vendor_alpha_client.close_order_confirmation()
            return True

        else:
            self.vendor_alpha_client.close_amountbox()
            return False

    def notify(self, message: str) -> None:
        log.info(message)
        notify_telegram(message)
