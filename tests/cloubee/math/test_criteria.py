from datetime import timedelta

from cloubee.math.criteria import (
    arb_is_not_detected,
    data_is_stale,
    insufficient_bet365_balance,
    insufficient_betfair_balance,
    insufficient_lay_liquidity,
    insufficient_profit_is_detected,
    lay_odd_exceeds_acceptable_limit,
    odds_are_not_properly_populated,
)


def test_odds_are_not_properly_populated():
    betfair_odds = {"A": 2.0, "B": 3.0}
    bet365_odds = {"A": 2.0, "B": 3.0, "C": 4.0}

    result = odds_are_not_properly_populated(betfair_odds, bet365_odds)

    assert result is True


def test_data_is_stale():
    time_difference = timedelta(seconds=80)
    max_allowed_time_diff = timedelta(seconds=60)

    result = data_is_stale(time_difference, max_allowed_time_diff)

    assert result is True


def test_lay_odd_exceeds_acceptable_limit():
    lay_odd = 3.0
    max_acceptable_lay_odd = 2.5

    result = lay_odd_exceeds_acceptable_limit(lay_odd, max_acceptable_lay_odd)

    assert result is True


def test_arb_is_not_detected():
    lay_odd = 2.5
    back_odd = 2.0

    result = arb_is_not_detected(lay_odd, back_odd)

    assert result is True


def test_insufficient_profit_is_detected():
    profit = 10.0
    min_acceptable_profit = 20.0

    result = insufficient_profit_is_detected(profit, min_acceptable_profit)

    assert result is True


def test_insufficient_bet365_balance():
    bet365_balance = 30
    back_amount = 50

    result = insufficient_bet365_balance(bet365_balance, back_amount)

    assert result is True


def test_sufficient_bet365_balance():
    bet365_balance = 50
    back_amount = 30

    result = insufficient_bet365_balance(bet365_balance, back_amount)

    assert result is False


def test_insufficient_betfair_balance():
    betfair_balance = 60
    lay_amount = 50
    lay_odd = 3

    result = insufficient_betfair_balance(betfair_balance, lay_amount, lay_odd)

    assert result is True


def test_sufficient_betfair_balance():
    betfair_balance = 50
    lay_amount = 10
    lay_odd = 3

    result = insufficient_betfair_balance(betfair_balance, lay_amount, lay_odd)

    assert result is False


def test_insufficient_lay_liquidity_when_not_enough_liquidity():
    lay_liquidity = 1.62
    lay_amount = 1.73

    result = insufficient_lay_liquidity(lay_amount, lay_liquidity)

    assert result is True


def test_insufficient_lay_liquidity_when_enough_liquidity():
    lay_liquidity = 1.82
    lay_amount = 1.73

    result = insufficient_lay_liquidity(lay_amount, lay_liquidity)

    assert result is False
