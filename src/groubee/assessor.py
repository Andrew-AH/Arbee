from typing import Tuple
from cloubee.math.criteria import (
    sell_price_exceeds_acceptable_limit,
    buy_price_exceeds_acceptable_limit,
)
from libs.models.opportunity import Opportunity
from libs.config.preferences import MAXIMUM_ACCEPTABLE_SELL_PRICE, MINIMUM_ACCEPTABLE_PROFIT, MAXIMUM_ACCEPTABLE_BUY_PRICE, MAXIMUM_NO_SUCCESSFUL_TRADES, MAXIMUM_NO_FAILED_TRADES

def assess(opportunity: Opportunity) -> Tuple[bool, str]:
    if sell_price_exceeds_acceptable_limit(opportunity.vendor_beta_sell_price, MAXIMUM_ACCEPTABLE_SELL_PRICE):
        return (
            False,
            f"sell price {opportunity.vendor_beta_sell_price} exceeds maximum {MAXIMUM_ACCEPTABLE_SELL_PRICE}",
        )

    if opportunity_has_expired(opportunity):
        return (False, "Opportunity expired")

    if buy_price_exceeds_acceptable_limit(opportunity.vendor_alpha_buy_price, MAXIMUM_ACCEPTABLE_BUY_PRICE):
        return (
            False,
            f"Buy price {opportunity.vendor_alpha_buy_price} exceeds maximum {MAXIMUM_ACCEPTABLE_BUY_PRICE}",
        )

    return (True, None)


def opportunity_has_expired(opportunity: Opportunity) -> bool:
    return opportunity.detected_timestamp > opportunity.au_event_time


def no_success_and_failed_trades_reaches_threshold(no_success_trades: int, no_failed_trades: int):
    return (
        no_success_trades >= MAXIMUM_NO_SUCCESSFUL_TRADES
        or no_failed_trades >= MAXIMUM_NO_FAILED_TRADES
    )
