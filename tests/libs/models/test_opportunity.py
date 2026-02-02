from datetime import datetime

from libs.models.opportunity import Opportunity


def test_opportunity_get_horse_name_hash_when_same():
    track_name = "Lingfield"
    horse = "Great Horse"
    lay_odd = 3
    back_odd = 4

    opportunity1 = Opportunity(
        track_name=track_name,
        au_race_time=datetime.now(),
        betfair_market_id="123456789",
        betfair_horse_id=123,
        betfair_lay_odd=lay_odd,
        betfair_lay_amount=100.0,
        betfair_lay_liquidity=10,
        bet365_url="https://example.com",
        bet365_standard_horse_name=horse,
        bet365_back_odd=back_odd,
        bet365_back_amount=95.0,
        betfair_balance_required=105.0,
        profit_in_dollars=10.0,
        percentage_return=9.5,
        detected_timestamp=datetime.now(),
    )

    opportunity2 = Opportunity(
        track_name=track_name,
        au_race_time=datetime.now(),
        betfair_market_id="123456789",
        betfair_horse_id=123,
        betfair_lay_odd=lay_odd,
        betfair_lay_amount=100.0,
        betfair_lay_liquidity=10,
        bet365_url="https://example.com",
        bet365_standard_horse_name=horse,
        bet365_back_odd=back_odd,
        bet365_back_amount=95.0,
        betfair_balance_required=105.0,
        profit_in_dollars=10.0,
        percentage_return=9.5,
        detected_timestamp=datetime.now(),
    )

    assert opportunity1.get_horse_name_hash() == opportunity2.get_horse_name_hash()


def test_opportunity_get_horse_name_hash_when_different():
    track_name = "Lingfield"
    horse_1 = "Great Horse"
    horse_2 = "Good Horse"
    lay_odd_1 = 3
    back_odd_1 = 4

    lay_odd_2 = 5
    back_odd_2 = 6

    opportunity1 = Opportunity(
        track_name=track_name,
        au_race_time=datetime.now(),
        betfair_market_id="123456789",
        betfair_horse_id=123,
        betfair_lay_odd=lay_odd_1,
        betfair_lay_amount=100.0,
        betfair_lay_liquidity=10,
        bet365_url="https://example.com",
        bet365_standard_horse_name=horse_1,
        bet365_back_odd=back_odd_1,
        bet365_back_amount=95.0,
        betfair_balance_required=105.0,
        profit_in_dollars=10.0,
        percentage_return=9.5,
        detected_timestamp=datetime.now(),
    )

    opportunity2 = Opportunity(
        track_name=track_name,
        au_race_time=datetime.now(),
        betfair_market_id="123456789",
        betfair_horse_id=123,
        betfair_lay_odd=lay_odd_2,
        betfair_lay_amount=100.0,
        betfair_lay_liquidity=10,
        bet365_url="https://example.com",
        bet365_standard_horse_name=horse_2,
        bet365_back_odd=back_odd_2,
        bet365_back_amount=95.0,
        betfair_balance_required=105.0,
        profit_in_dollars=10.0,
        percentage_return=9.5,
        detected_timestamp=datetime.now(),
    )

    assert opportunity1.get_horse_name_hash() != opportunity2.get_horse_name_hash()


def test_opportunity_get_common_hash_when_same():
    track_name = "Lingfield"
    au_race_time = datetime.now()
    horse = "Great Horse"
    lay_odd = 3
    back_odd = 4

    opportunity1 = Opportunity(
        track_name=track_name,
        au_race_time=au_race_time,
        betfair_market_id="123456789",
        betfair_horse_id=123,
        betfair_lay_odd=lay_odd,
        betfair_lay_amount=100.0,
        betfair_lay_liquidity=10,
        bet365_url="https://example.com",
        bet365_standard_horse_name=horse,
        bet365_back_odd=back_odd,
        bet365_back_amount=95.0,
        betfair_balance_required=105.0,
        profit_in_dollars=10.0,
        percentage_return=9.5,
        detected_timestamp=datetime.now(),
    )

    opportunity2 = Opportunity(
        track_name=track_name,
        au_race_time=au_race_time,
        betfair_market_id="123456789",
        betfair_horse_id=123,
        betfair_lay_odd=lay_odd,
        betfair_lay_amount=100.0,
        betfair_lay_liquidity=10,
        bet365_url="https://example.com",
        bet365_standard_horse_name=horse,
        bet365_back_odd=back_odd,
        bet365_back_amount=95.0,
        betfair_balance_required=105.0,
        profit_in_dollars=10.0,
        percentage_return=9.5,
        detected_timestamp=datetime.now(),
    )

    assert (
        opportunity1.get_common_hash() == opportunity2.get_common_hash()
    ), "Hashes should be equal for same opportunities"


def test_opportunity_get_common_hash_when_different():
    track_name = "Lingfield"
    au_race_time = datetime.now()
    horse = "Great Horse"
    lay_odd = 3

    opportunity1 = Opportunity(
        track_name=track_name,
        au_race_time=au_race_time,
        betfair_market_id="123456789",
        betfair_horse_id=123,
        betfair_lay_odd=lay_odd,
        betfair_lay_amount=100.0,
        betfair_lay_liquidity=10,
        bet365_url="https://example.com",
        bet365_standard_horse_name=horse,
        bet365_back_odd=2,
        bet365_back_amount=95.0,
        betfair_balance_required=105.0,
        profit_in_dollars=10.0,
        percentage_return=9.5,
        detected_timestamp=datetime.now(),
    )

    opportunity2 = Opportunity(
        track_name=track_name,
        au_race_time=au_race_time,
        betfair_market_id="123456789",
        betfair_horse_id=123,
        betfair_lay_odd=lay_odd,
        betfair_lay_amount=100.0,
        betfair_lay_liquidity=10,
        bet365_url="https://example.com",
        bet365_standard_horse_name=horse,
        bet365_back_odd=4,
        bet365_back_amount=95.0,
        betfair_balance_required=105.0,
        profit_in_dollars=10.0,
        percentage_return=9.5,
        detected_timestamp=datetime.now(),
    )

    assert (
        opportunity1.get_common_hash() != opportunity2.get_common_hash()
    ), "Hashes should not be equal for different opportunities"
