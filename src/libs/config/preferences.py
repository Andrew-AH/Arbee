from datetime import timedelta


# Preferences
# =============================================================================
BUY_AMOUNT = 4
COMMISSION = 0.05
MAXIMUM_ACCEPTABLE_SELL_PRICE = 30
MAXIMUM_ACCEPTABLE_BUY_PRICE = 16
MINIMUM_ACCEPTABLE_PROFIT = 0.2
OPPORTUNITY_EXPIRATION = timedelta(seconds=3)
MAXIMUM_NO_SUCCESSFUL_TRADES = 100
MAXIMUM_NO_FAILED_TRADES = 1
MAXIMUM_NO_SAME_SUCCESS_OPPORTUNITIES = 1
MAXIMUM_INVESTED_ON_AN_EVENT = 100
MAXIMUM_NO_SAME_FAILED_OPPORTUNITIES = 5

# When true, the program will treat all detected opportunities as successful trades (nice for testing)
# When false, the program will function as expected, trading on real opportunities
FAKE_TRADE_SUCCESSES = False
