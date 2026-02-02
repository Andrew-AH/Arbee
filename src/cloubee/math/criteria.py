from datetime import datetime, timedelta

from cloubee.math.arbitrage import calculate_liability


def prices_are_not_properly_populated(
    vendor_beta_prices: dict[str, float], vendor_alpha_prices: dict[str, float]
) -> bool:
    """Returns True if prices are not properly populated (especially from Vendor Alpha side), False otherwise."""
    return len(vendor_beta_prices) != len(vendor_alpha_prices)


def data_is_stale(time_difference: timedelta, max_allowed_time_diff: timedelta) -> bool:
    """Returns True if data is stale (e.g. Vendor Alpha may occasionally infinite load), False otherwise."""
    return time_difference >= max_allowed_time_diff


def sell_price_exceeds_acceptable_limit(sell_price: float, max_acceptable_sell_price: float) -> bool:
    return sell_price > max_acceptable_sell_price

def buy_price_exceeds_acceptable_limit(buy_price: float, max_acceptable_buy_price: float) -> bool:
    return buy_price > max_acceptable_buy_price


def opportunity_is_not_detected(sell_price: float, buy_price: float) -> bool:
    return sell_price >= buy_price


def insufficient_profit_is_detected(profit: float, min_acceptable_profit: float) -> bool:
    return profit < min_acceptable_profit


def insufficient_vendor_alpha_balance(vendor_alpha_balance: float, buy_amount: float) -> bool:
    return vendor_alpha_balance < buy_amount


def insufficient_vendor_beta_balance(vendor_beta_balance: float, sell_amount: float, sell_price: float) -> bool:
    return vendor_beta_balance < calculate_liability(sell_amount, sell_price, rounded=True)


def event_time_too_close(event_time: datetime, minimum_time_buffer: timedelta) -> bool:
    time_remaining = event_time.replace(tzinfo=None) - datetime.now()
    return time_remaining <= minimum_time_buffer


def insufficient_sell_liquidity(
    sell_amount: float,
    sell_liquidity: float,
):
    return sell_amount > sell_liquidity
