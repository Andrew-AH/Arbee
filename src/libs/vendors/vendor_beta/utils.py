# Vendor Beta API endpoints
from enum import Enum
import requests

from libs.utils.env import VENDOR_BETA_API_KEY, VENDOR_BETA_PASS, VENDOR_BETA_USER


LOGIN_URL = "https://api.example-vendor-beta.com/auth/login"
MARKET_CATALOGUE_URL = "https://api.example-vendor-beta.com/exchange/v1.0/listMarketCatalogue/"
MARKET_BOOK_URL = "https://api.example-vendor-beta.com/exchange/v1.0/listMarketBook/"
CURRENT_ORDERS_URL = "https://api.example-vendor-beta.com/exchange/v1.0/listCurrentOrders/"
PLACE_ORDERS_URL = "https://api.example-vendor-beta.com/exchange/v1.0/placeOrders/"
GET_BALANCE_URL = "https://api.example-vendor-beta.com/account/v1/getAccountFunds/"


class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    EXECUTION_COMPLETE = "EXECUTION_COMPLETE"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"
    EXECUTABLE = "EXECUTABLE"


class UnhandledVendorBetaOrderStatusException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def construct_headers() -> dict:
    return {
        "X-Application": VENDOR_BETA_API_KEY,
        "X-Authentication": get_ssoid(
            api_key=VENDOR_BETA_API_KEY, username=VENDOR_BETA_USER, password=VENDOR_BETA_PASS
        ),
        "Content-Type": "application/json",
    }


def get_ssoid(api_key: str, username: str, password: str):
    headers = {
        "Accept": "application/json",
        "X-Application": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {"username": username, "password": password}

    response = requests.post(LOGIN_URL, data=payload, headers=headers)
    response.raise_for_status()

    return response.json().get("token")
