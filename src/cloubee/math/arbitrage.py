def calculate_profit(
    buy_amount: float, buy_price: float, sell_price: float, commission: float
) -> float:
    """
    Calculates profit which occurs no matter the outcome
    """
    sell_amount = sell_amount = (buy_amount * buy_price) / (sell_price - commission)
    profit = round(
        (buy_amount * buy_price - buy_amount) + (sell_amount - sell_amount * sell_price), 2
    )

    return profit


def calculate_sell_amount(
    buy_amount: float,
    buy_price: float,
    sell_price: float,
    commission: float,
    rounded: bool = False,
) -> float:
    """
    Calculates sell amount required which assumes no matter the outcome, there will be equal profits/losses
    """
    sell_amount = (buy_amount * buy_price) / (sell_price - commission)
    return round(sell_amount, 2) if rounded else sell_amount


def calculate_exit_amount_and_profit(
    sell_amount: float, sell_price: float, buy_price: float, rounded: bool = False
) -> tuple[float, float]:
    """
    Calculates buy amount required at current buy price to minimise losses after a sell order is placed
    """
    buy_amount = (sell_amount * sell_price) / buy_price

    buy_order_winnings = buy_amount * (buy_price - 1)

    sell_order_loss = calculate_liability(sell_amount, sell_price)

    profit = buy_order_winnings - sell_order_loss

    return (round(buy_amount, 2) if rounded else buy_amount, round(profit, 2))


def calculate_liability(
    sell_amount: float, sell_price: float, rounded: bool = False
) -> float:
    """
    Calculates the liability of a sell order
    """
    return (
        round(sell_amount * (sell_price - 1), 2) if rounded else sell_amount * (sell_price - 1)
    )


def calculate_roi(buy_amount: float, profit: float, rounded: bool = False):
    """
    Calculates percentage return on investment on a trade
    """
    return round(profit / buy_amount, 4) if rounded else profit / buy_amount
