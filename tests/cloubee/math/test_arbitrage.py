from cloubee.math.arbitrage import (
    calculate_cash_out_amount_and_profit,
    calculate_lay_amount,
    calculate_liability,
)


def test_calculate_rounded_lay_amount():
    back_amount = 50
    back_odd = 5.5
    lay_odd = 5.8
    commission = 0.1
    expected_lay_amount = 48.25

    lay_amount = calculate_lay_amount(back_amount, back_odd, lay_odd, commission, rounded=True)

    assert lay_amount == expected_lay_amount


def test_calculate_lay_amount():
    back_amount = 50
    back_odd = 5.5
    lay_odd = 5.8
    commission = 0.1
    expected_lay_amount = 48.24561403508772

    lay_amount = calculate_lay_amount(back_amount, back_odd, lay_odd, commission)

    assert lay_amount == expected_lay_amount


def test_calculate_rounded_cash_out_amount_and_profit():
    back_odd = 10
    lay_odd = 10.5
    lay_amount = 5
    expected_back_amount = 5.25
    expected_profit = -0.25

    (cash_out_amount, profit) = calculate_cash_out_amount_and_profit(
        lay_amount, lay_odd, back_odd, rounded=True
    )

    assert cash_out_amount == expected_back_amount
    assert profit == expected_profit


def test_calculate_cash_out_amount_and_profit():
    back_odd = 10
    lay_odd = 10.5
    lay_amount = 2.50
    expected_back_amount = 2.625
    expected_profit = -0.12

    (cash_out_amount, profit) = calculate_cash_out_amount_and_profit(lay_amount, lay_odd, back_odd)

    assert cash_out_amount == expected_back_amount
    assert profit == expected_profit


def test_calculate_rounded_liability():
    lay_odd = 8.0
    lay_amount = 12.58
    expected_liability = 88.06

    liability = calculate_liability(lay_amount, lay_odd, rounded=True)

    assert liability == expected_liability


def test_calculate_liability():
    lay_odd = 8.0
    lay_amount = 12.578616352201257
    expected_liability = 88.0503144654088

    liability = calculate_liability(lay_amount, lay_odd)

    assert liability == expected_liability
