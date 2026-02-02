import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict

from libs.utils.hash import get_hash


@dataclass(frozen=True)
class Opportunity:
    venue_name: str
    au_event_time: datetime
    vendor_beta_market_id: str
    vendor_beta_item_id: int
    vendor_beta_sell_price: float
    vendor_beta_sell_amount: float
    vendor_beta_sell_liquidity: float
    vendor_alpha_url: str
    vendor_alpha_standard_item_name: str
    vendor_alpha_buy_price: float
    vendor_alpha_buy_amount: float
    vendor_beta_balance_required: float
    profit_in_dollars: float
    percentage_return: float
    detected_timestamp: datetime

    def __str__(self) -> str:
        return (
            f"Price Arbitrage Opportunity:\n"
            f"  Venue: {self.venue_name}\n"
            f"  Event Time: {self.au_event_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  Vendor Beta Market ID: {self.vendor_beta_market_id}\n"
            f"  Vendor Beta Item ID: {self.vendor_beta_item_id}\n"
            f"  Vendor Beta Sell Price: {self.vendor_beta_sell_price}\n"
            f"  Vendor Beta Sell Amount: {self.vendor_beta_sell_amount}\n"
            f"  Vendor Beta Sell Liquidity: {self.vendor_beta_sell_liquidity}\n"
            f"  Vendor Alpha URL: {self.vendor_alpha_url}\n"
            f"  Vendor Alpha Standard Item Name: {self.vendor_alpha_standard_item_name}\n"
            f"  Vendor Alpha Buy Price: {self.vendor_alpha_buy_price}\n"
            f"  Vendor Alpha Buy Amount: {self.vendor_alpha_buy_amount}\n"
            f"  Vendor Beta Balance Required: {self.vendor_beta_balance_required}\n"
            f"  Profit in Dollars: {self.profit_in_dollars}\n"
            f"  Percentage Return: {self.percentage_return * 100}%\n"
            f"  Detected Timestamp: {self.detected_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

    def to_json(self) -> str:
        """Convert the Opportunity instance to a JSON string."""
        return json.dumps(
            asdict(self),
            indent=2,
            default=str,  # Converts non-serializable objects like datetime to strings
        )

    @classmethod
    def from_dict_of_strings(cls, data: Dict[str, str]):
        """Handles casting dictionary into the Opportunity class, converting types. Assumes values are strings."""

        data["venue_name"] = str(data["venue_name"])
        data["au_event_time"] = datetime.fromisoformat(data["au_event_time"])
        data["vendor_beta_market_id"] = str(data["vendor_beta_market_id"])
        data["vendor_beta_item_id"] = int(data["vendor_beta_item_id"])
        data["vendor_beta_sell_price"] = float(data["vendor_beta_sell_price"])
        data["vendor_beta_sell_amount"] = float(data["vendor_beta_sell_amount"])
        data["vendor_beta_sell_liquidity"] = float(data["vendor_beta_sell_liquidity"])
        data["vendor_alpha_url"] = str(data["vendor_alpha_url"])
        data["vendor_alpha_standard_item_name"] = str(data["vendor_alpha_standard_item_name"])
        data["vendor_alpha_buy_price"] = float(data["vendor_alpha_buy_price"])
        data["vendor_alpha_buy_amount"] = float(data["vendor_alpha_buy_amount"])
        data["vendor_beta_balance_required"] = float(data["vendor_beta_balance_required"])
        data["profit_in_dollars"] = float(data["profit_in_dollars"])
        data["percentage_return"] = float(data["percentage_return"])
        data["detected_timestamp"] = datetime.fromisoformat(data["detected_timestamp"])

        # Safely call the constructor with the converted data
        return cls(**data)

    def get_item_name_hash(self) -> int:
        """
        This hash function exists for the sole purpose of avoiding duplicates.
        An opportunity with the same item name, will hash to the same opportunity
        which will allow main to skip same item opportunities.
        """
        return hash(self.vendor_alpha_standard_item_name)

    def get_common_hash(self) -> str:
        """
        This hash function is used to uniquely identify an opportunity
        based on its key attributes, mainly for database storage and retrieval.
        """
        return get_hash(
            self.au_event_time,
            self.vendor_alpha_standard_item_name,
            self.vendor_beta_sell_price,
            self.vendor_alpha_buy_price,
        )
