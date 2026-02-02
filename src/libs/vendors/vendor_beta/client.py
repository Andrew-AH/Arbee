from datetime import datetime, timedelta
import json
import math
from typing import List, Optional, Tuple

import pytz
import requests
from libs.vendors.vendor_beta.utils import (
    GET_BALANCE_URL,
    MARKET_BOOK_URL,
    MARKET_CATALOGUE_URL,
    PLACE_ORDERS_URL,
    OrderType,
    OrderStatus,
    UnhandledVendorBetaOrderStatusException,
    construct_headers,
)
from libs.utils.log import get_logger
from libs.utils.strings import standardize_string


class VendorBetaOrderFailedToPlaceException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class VendorBetaClient:
    def __init__(self):
        self.headers = construct_headers()
        self.log = get_logger(
            file_name="executor", logs_to_file=True, logs_to_console=True
        )
        self.cache = {}

    def get_item_selection_ids(self, market_id: str) -> dict[str, str]:
        """
        Given a specific event, returns a dictionary of item names along with their respective selection ids
        """
        catalogue_payload = json.dumps(
            {
                "filter": {"marketIds": [market_id]},
                "maxResults": "1",
                "marketProjection": ["RUNNER_DESCRIPTION"],
            }
        )

        response = requests.post(
            MARKET_CATALOGUE_URL, data=catalogue_payload, headers=self.headers
        )
        response.raise_for_status()

        item_data = {}

        catalogue_data = response.json()
        if catalogue_data:
            runners = catalogue_data[0].get("runners", [])
            for runner in runners:
                item_name = runner.get("runnerName")
                selection_id = runner.get("selectionId")
                item_data[standardize_string(item_name)] = selection_id
        else:
            self.log.warning("No data returned for marketId:", market_id)

        return item_data

    def place_order(
        self,
        market_id: str,
        selection_id: str,
        order_type: OrderType,
        price: float,
        size: float,
    ) -> bool:
        """
        Place order on a specific item
        """
        # Construct the instruction for the order
        instruction = {
            "selectionId": selection_id,
            "handicap": 0,
            "side": order_type.value,
            "orderType": "LIMIT",
            "limitOrder": {
                "size": size,
                "price": price,
                "persistenceType": "LAPSE",
                "minFillSize": size,
                "timeInForce": "FILL_OR_KILL",
            },
        }

        # Payload for the placeOrders request
        payload = json.dumps({"marketId": market_id, "instructions": [instruction]})

        self.log.debug(f"Sending place order request: {payload}")

        response = requests.post(PLACE_ORDERS_URL, data=payload, headers=self.headers)
        response.raise_for_status()

        order_result = response.json()

        self.log.debug(f"Received place order response: {order_result}")

        if order_result["instructionReports"][0]["status"] == "FAILURE":
            error_code = order_result["instructionReports"][0]["errorCode"]
            raise VendorBetaOrderFailedToPlaceException(
                f"Vendor Beta order failed to replace due to error code: {error_code}"
            )

        order_status = order_result["instructionReports"][0]["orderStatus"]

        if order_status == OrderStatus.EXECUTION_COMPLETE.value:
            self.log.info(
                f"Order placed successfully - {order_type} Amount: {size}, {order_type} Price: {price}"
            )
            return True

        elif order_status == OrderStatus.EXPIRED.value:
            self.log.error(
                "Order failed to place because order could not be matched fully"
            )
            return False

        else:
            raise UnhandledVendorBetaOrderStatusException(
                f"Cannot handle order status: {order_status}"
            )

    def get_balance(self) -> float:
        """
        Retrieves total available balance for trading
        """
        params = {"wallet": "AUSTRALIAN"}

        response = requests.post(GET_BALANCE_URL, headers=self.headers, params=params)
        response.raise_for_status()

        account_funds = response.json()

        balance = float(account_funds["availableToBetBalance"])

        return balance

    def get_item_current_buy_price(self, market_id: str, selection_id: str) -> float:
        """
        Retrieves the current buy price for a given item (selectionId) in a specific market (marketId).
        :param market_id: The market ID for the event
        :param selection_id: The selection ID for the item
        :return: The current buy price for the item
        """
        # Payload for the listMarketBook request
        request_payload = json.dumps(
            {
                "marketIds": [market_id],
                "priceProjection": {
                    "priceData": [
                        "EX_BEST_OFFERS"
                    ],  # Requesting the best available offers
                },
            }
        )

        response = requests.post(
            MARKET_BOOK_URL, data=request_payload, headers=self.headers
        )
        response.raise_for_status()

        market_books = response.json()

        if market_books:
            # Iterating through the market book to find the matching selectionId
            for market_book in market_books:
                for runner in market_book.get("runners", []):
                    if runner["selectionId"] == selection_id:
                        if "availableToBack" in runner["ex"]:
                            # Assuming you want the best available buy price
                            best_buy_offer = runner["ex"]["availableToBack"][
                                0
                            ]  # The first element is the best offer
                            return best_buy_offer["price"]
                        else:
                            self.log.info(
                                f"No buy price available for selectionId: {selection_id}"
                            )
                            return None
        else:
            self.log.info("No market book data returned.")
            return None

    def manual_cashout(
        self,
        market_id: str,
        selection_id: str,
        item_buy_price: float,
        buy_amount: float,
    ) -> bool:
        return self.place_order(
            market_id, selection_id, OrderType.BUY, item_buy_price, buy_amount
        )

    def get_item_prices(
        self, market_id: str, order_type: OrderType
    ) -> dict[str, Tuple[float, float]]:
        if market_id not in self.cache:
            self.cache[market_id] = self.get_selection_id_to_item_name_map(market_id)

        ids_to_item_name = self.cache[market_id]

        request_payload = json.dumps(
            {
                "marketIds": [market_id],
                "priceProjection": {
                    "priceData": [
                        "EX_BEST_OFFERS"
                    ],  # Requesting all offers to get both buy and sell prices
                },
            }
        )

        response = requests.post(
            MARKET_BOOK_URL, data=request_payload, headers=self.headers
        )
        response.raise_for_status()

        market_books = response.json()
        item_prices = {}

        if market_books:
            for market_book in market_books:
                for runner in market_book.get("runners", []):
                    if runner.get("status") == "ACTIVE":
                        name = ids_to_item_name[runner.get("selectionId")]
                        standard_name = standardize_string(name)

                        price_list = (
                            runner["ex"]["availableToBack"]
                            if order_type == OrderType.BUY
                            else runner["ex"]["availableToLay"]
                        )
                        if price_list:
                            best_offer = price_list[0]  # Taking the best (first) offer
                            item_prices[standard_name] = (
                                best_offer["price"],
                                best_offer["size"],
                            )
                        else:
                            item_prices[standard_name] = (math.inf, None)
        else:
            self.log.warning("No market book data returned.")

        return item_prices

    def get_selection_id_to_item_name_map(self, market_id: str) -> dict[str, str]:
        """
        Fetches and returns a dictionary mapping selection IDs to item names for a given market ID.
        :param market_id: The market ID for which to fetch the mapping.
        :return: A dictionary where keys are selection IDs and values are item names.
        """
        catalogue_payload = json.dumps(
            {
                "filter": {"marketIds": [market_id]},
                "maxResults": "1",
                "marketProjection": ["RUNNER_DESCRIPTION"],
            }
        )

        response = requests.post(
            MARKET_CATALOGUE_URL, data=catalogue_payload, headers=self.headers
        )
        response.raise_for_status()

        selection_id_to_item_name = {}

        catalogue_data = response.json()

        if catalogue_data:
            runners = catalogue_data[0].get("runners", [])
            for runner in runners:
                selection_id_to_item_name[runner.get("selectionId")] = runner.get(
                    "runnerName"
                )
        else:
            self.log.warning("No data returned for market id:", market_id)

        return selection_id_to_item_name

    def get_market_id_and_start_time(
        self, venue_name: str, time_str: str, country_codes: List[str] = ["GB", "IE"]
    ) -> Tuple[Optional[str], datetime]:
        """
        Gets the market ID of the earliest event that matches time of format "HH:MM" in GB and IRE regions
        by default.
        """
        timezone_aedt = pytz.timezone("Australia/Melbourne")
        timezone_utc = pytz.utc

        now_aedt = datetime.now(timezone_aedt)

        # Construct datetime object of format: 2024-03-30T00:18:00+11:00
        given_time_aedt = (
            datetime.strptime(time_str, "%H:%M")
            .replace(year=now_aedt.year, month=now_aedt.month, day=now_aedt.day)
            .astimezone(timezone_aedt)
        )

        # If the given time is in the past, assume it refers to the next day
        if given_time_aedt < now_aedt:
            given_time_aedt += timedelta(days=1)

        # Converts to UTC datetime object of format: 2024-03-29T13:18:00+00:00
        given_time_utc = given_time_aedt.astimezone(timezone_utc)

        payload = {
            "filter": {
                "eventTypeIds": ["7"],  # Events with id = 7 are market events
                "marketCountries": country_codes,
                "marketTypeCodes": ["WIN"],
                # TODO: Can optimise here by only supplying a range of t to t + 1 day
                # "marketStartTime": {"from": f"{date_from}T00:00:00Z", "to": f"{date_to}T23:59:59Z"},
            },
            "sort": "FIRST_TO_START",
            "maxResults": "1000",
            "marketProjection": ["MARKET_START_TIME", "EVENT"],
        }

        response = requests.post(
            MARKET_CATALOGUE_URL, headers=self.headers, json=payload
        )
        response.raise_for_status()

        market_catalogues = response.json()

        for catalogue in market_catalogues:
            # Convert to datetime object of format: 2024-03-29T13:18:00.000Z
            formatted_event_dt = datetime.strptime(
                catalogue["marketStartTime"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            # Convert to datetime object of format: 2024-03-29T13:18:00+00:00
            utc_event_dt = pytz.timezone("UTC").localize(formatted_event_dt)

            event_name = catalogue["event"]["name"]

            if utc_event_dt == given_time_utc and venue_name in event_name:
                return catalogue["marketId"], given_time_aedt

        # If no exact match is found, consider handling this case (e.g., returning closest match)
        return None


if __name__ == "__main__":
    client = VendorBetaClient()
