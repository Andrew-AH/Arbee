import time
import pyautogui
from selenium_driverless.sync import webdriver
from selenium_driverless.types.by import By
from selenium_driverless.types.webelement import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from asyncio import TimeoutError, CancelledError
from libs.interfaces.client import VendorClient
from libs.vendors.vendor_alpha.layout import (
    ClassName,
    XPath,
)
from libs.utils.retry import retry_on_exception
from libs.utils.log import get_logger
from libs.utils.strings import standardize_string
from libs.utils.env import VENDOR_ALPHA_PASS, VENDOR_ALPHA_USER

DEFAULT_TIMEOUT = 10


class AmountValueNotSetException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class OrderRequiresApprovalException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class VendorAlphaClient(VendorClient):
    def __init__(self, initial_url: str, default_order_amount: int = 1) -> None:
        self.log = get_logger(
            file_name="executor", logs_to_file=True, logs_to_console=True
        )
        self.driver = self.initialise_driver()
        self.wait = WebDriverWait(self.driver, DEFAULT_TIMEOUT)
        try:
            self.navigate_url(initial_url)

            self.log.info("SLEEPING 10 SECONDS.. DON'T PANIC -.-'")
            time.sleep(10)
            self.log.info("Simulating ENTER key press..")
            pyautogui.press("enter")

            self.__login_and_set_default_amount(default_order_amount)

        except Exception as e:
            self.driver.quit()
            raise e

    def initialise_driver(self) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = retry_on_exception(
            lambda: webdriver.Chrome(options=options), logger=self.log
        )  # Has on occasion failed to initialise
        return driver

    def __login_and_set_default_amount(self, default_order_amount: int) -> None:
        try:
            self.reject_cookies()
            self.login()
            self.set_orderslip_default_amount(default_order_amount)

        except Exception as e:
            self.driver.quit()
            raise e

    def navigate_url(self, url: str) -> None:
        self.log.info(f"Navigating to: {url}")
        self.driver.get(url)
        self.driver.sleep(1)

    def reject_cookies(self):
        reject_cookies_button = self.driver.find_element(
            By.XPATH, XPath.REJECT_COOKIES_BUTTON, timeout=DEFAULT_TIMEOUT
        )
        reject_cookies_button.click()

    def login(self) -> None:
        self.log.info(f"Logging in as {VENDOR_ALPHA_USER}..")
        login_button = self.driver.find_element(
            By.XPATH, XPath.LOGIN_BUTTON, timeout=DEFAULT_TIMEOUT
        )
        login_button.click()

        time.sleep(0.5)

        username = self.driver.find_element(
            By.XPATH, XPath.USER_NAME_INPUT, timeout=DEFAULT_TIMEOUT
        )
        username.clear()
        username.send_keys(VENDOR_ALPHA_USER)

        password = self.driver.find_element(
            By.XPATH, XPath.PASSWORD_INPUT, timeout=DEFAULT_TIMEOUT
        )
        password.clear()
        password.send_keys(VENDOR_ALPHA_PASS)

        modal_login_button = self.driver.find_element(
            By.XPATH, XPath.MODAL_LOGIN_BUTTON, timeout=DEFAULT_TIMEOUT
        )

        modal_login_button.click()
        self.driver.sleep(5)
        self.log.info("Login successful!")

    def set_orderslip_default_amount(self, default_amount: int | float):
        self.log.info("Setting orderslip default amount..")

        self.select_item()
        self.__set_amount(default_amount)
        self.__enable_remember_button()
        retry_on_exception(
            lambda: self.verify_set_amount(default_amount), delay=5, retries=10
        )  # Verify amount set to given value every 5 seconds
        self.close_amountbox()

        self.log.info(f"Successfully set orderslip default amount to ${default_amount}")

    def verify_set_amount(self, default_amount: int | float):
        """
        Verifies if amount is set to the correct value. Assumes amount box modal is showing.
        """
        amount_value = self.driver.find_element(
            By.XPATH, XPath.AMOUNT_BOX_AMOUNT_VALUE, timeout=DEFAULT_TIMEOUT
        ).text

        if not amount_value or float(amount_value) != default_amount:
            message = (
                "Amount value is not set"
                if not amount_value
                else f"Amount value: ${amount_value} does not match intended value: ${default_amount}"
            )
            self.log.warning(message)
            self.log.warning("Please correct manually")
            raise AmountValueNotSetException(message)

        self.log.info(f"Amount is: ${default_amount}")

    def prices_have_changed(self, desired_buy_price: float) -> bool:
        """
        Assumes amount box modal is showing.
        """
        try:
            current_buy_price = self.driver.find_element(
                By.XPATH, XPath.AMOUNT_BOX_PRICE, timeout=DEFAULT_TIMEOUT
            ).text

            if float(desired_buy_price) != float(current_buy_price):
                self.log.info(
                    f"Failed to place order @ {desired_buy_price} because prices have changed to {current_buy_price}"
                )
                return True

            return False

        except Exception as e:
            self.log.exception(f"Something went wrong while detecting price changes: {e}")
            return True

    def buy(self, item: str, price: float, amount: float) -> bool:
        # TODO: Implement this to satisfy abstract class. VendorAlphaClient breaks down the buy into multiple smaller functions
        # for optimisation purposes (e.g. select_item(), place_order()), but having this one function simplifies things
        # if we don't need the optimisation.
        pass

    def balance(self) -> float:
        balance_text = ""

        while balance_text == "":
            balance_element = self.driver.find_element(
                By.XPATH, XPath.USER_INFO_BALANCE, timeout=DEFAULT_TIMEOUT
            )
            balance_text = balance_element.text.replace("$", "").replace(",", "")

        return float(balance_text)

    def place_order(self, desired_buy_price: float) -> bool:
        """
        Places order by firstly verifying if buy price is still the same and then
        clicking "Place order" button on amountbox modal.
        Assumes default amount is set and amountbox is currently displayed.
        """
        try:
            if self.prices_have_changed(desired_buy_price):
                return False

            self.log.debug("Finding place order button..")
            place_order_button = self.driver.find_element(
                By.XPATH, XPath.PLACE_ORDER_BUTTON, timeout=DEFAULT_TIMEOUT
            )
            self.log.debug("Proceeding to click place order button..")
            # Sleep required here to prevent error
            self.driver.sleep(1)
            place_order_button.click()
            self.log.info("Clicked place order button")

        except Exception as e:
            self.log.exception(f"Exception thrown: {e}")
            return False

        return self.__is_order_confirmed()

    def select_item(self, event_url: str = None, item_name: str = None) -> bool:
        """
        Selects an item specified by its name on a given event url. If no item name provided,
        the first item on the webpage will be selected. If no event url is provided, the select
        will happen on the current webpage.
        """
        if event_url is not None:
            self.navigate_url(event_url)

        while True:
            try:
                self.refresh_page()
                self.driver.sleep(2)
                self.log.debug(f"Finding item called {item_name} to click..")
                items = self.wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, XPath.RUNNER))
                )

                for h in items:
                    name = standardize_string(
                        h.find_element(
                            By.CSS_SELECTOR,
                            f".{ClassName.RUNNER_NAME_CLASS}",
                            timeout=DEFAULT_TIMEOUT,
                        ).text
                    )

                    self.log.debug(name)

                    if name == item_name or item_name is None:
                        self.log.debug(
                            f"Found item called {item_name}, proceeding to click on item.."
                        )
                        buy_price_element = h.find_element(
                            By.CSS_SELECTOR,
                            f".{ClassName.BUY_PRICE}",
                            timeout=DEFAULT_TIMEOUT,
                        )
                        retry_on_exception(lambda: buy_price_element.click(), delay=0.5)
                        self.log.info(f"Clicked on item called {item_name}")
                        return True

                raise Exception(f"Couldn't locate item called {item_name}")

            except (TimeoutException, TimeoutError, CancelledError):
                self.log.warning("Timeout exception occurred, retrying in 5 seconds...")
                self.driver.sleep(5)
                continue

            except Exception as e:
                self.log.exception(f"Exception thrown: {e}")
                return False

    def close_order_confirmation(self) -> bool:
        try:
            order_confirmation_remove_button = self.driver.find_element(
                By.XPATH,
                XPath.ORDER_CONFIRMATION_RECEIPT_REMOVE_BUTTON,
                timeout=DEFAULT_TIMEOUT,
            )
            self.log.debug("Closing order confirmation modal..")
            retry_on_exception(
                lambda: order_confirmation_remove_button.click(), delay=0.5
            )
            # Sleep to ensure modal is fully closed
            self.driver.sleep(1)
            self.log.info("Closed order confirmation modal")
            return True

        except Exception as e:
            self.log.exception(
                f"Something went wrong while closing order confirmation modal: {e}"
            )
            return False

    def close_amountbox(self) -> bool:
        try:
            amount_box_remove_button = self.driver.find_element(
                By.XPATH, XPath.AMOUNT_BOX_REMOVE_BUTTON
            )
            self.log.debug("Closing amountbox modal..")
            amount_box_remove_button.click()
            self.log.info("Closed amountbox modal")
            return True

        except NoSuchElementException:
            self.log.warning("Amountbox not found. Nothing to close")
            return False

        except Exception as e:
            self.log.error(f"An unexpected error occurred: {e}")
            return False

    def refresh_page(self) -> None:
        self.driver.refresh()

    def __enable_remember_button(self):
        """
        Assumes amount box modal is showing.
        """
        if self.__remember_enabled():
            self.log.info("'Remember' button already enabled")

        else:
            remember_button = self.driver.find_element(
                By.XPATH, XPath.AMOUNT_BOX_REMEMBER_BUTTON, timeout=DEFAULT_TIMEOUT
            )
            remember_button.click()

        self.log.info("Successfully enabled 'Remember' button")

    def __remember_enabled(self) -> bool:
        """
        Assumes amount box modal is showing.
        """
        try:
            # No timeout specified as that would add a long delay for this check
            self.driver.find_element(By.XPATH, XPath.AMOUNT_BOX_REMEMBER_BUTTON_ACTIVE)
            return True

        except NoSuchElementException:
            return False

    def __is_order_confirmed(self) -> bool:
        try:
            self.log.info("Finding confirmation receipt..")
            self.driver.find_element(
                By.XPATH, XPath.CONFIRMATION_RECEIPT, timeout=DEFAULT_TIMEOUT
            )
            self.log.info("Order confirmed")
            return True
        except NoSuchElementException:
            self.log.warning("No confirmation receipt")

            self.log.info("Looking for order needs approval message..")

            try:
                self.driver.find_element(
                    By.XPATH, XPath.ORDER_NEEDS_APPROVAL_MESSAGE, timeout=5
                )
                self.log.warn("Found order needs approval message")

            except NoSuchElementException:
                self.log.debug("Did not find order needs approval message")
                pass

            return False

    def __set_amount(self, default_amount):
        """
        Assumes amount box modal is showing.
        """
        time.sleep(1)
        amount_box_input = self.driver.find_element(
            By.XPATH,
            XPath.AMOUNT_BOX_AMOUNT_INPUT_NOT_SET,
            timeout=DEFAULT_TIMEOUT,
        )
        amount_box_input.send_keys(str(default_amount))
