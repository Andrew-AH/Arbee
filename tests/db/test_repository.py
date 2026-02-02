from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.config import IN_MEMORY_DB_URL, get_db_engine
from db.entities import Accounts, Bets, Machines, Opportunities, Races
from db.repository import Repository
from libs.models.opportunity import Opportunity
from libs.utils.datetimes import melb_to_utc

BET365_USER = "user@gmail.com"
MACHINE = "test_machine"


@pytest.fixture(scope="function")
def repository():
    return Repository(get_db_engine(IN_MEMORY_DB_URL))


def test_save_account_and_idempotency(repository):
    # GIVEN no accounts exist
    with Session(repository.engine) as session:
        assert session.query(Accounts).count() == 0

    # WHEN I save BET365_USER twice
    repository.save_account_to_db(BET365_USER)
    repository.save_account_to_db(BET365_USER)

    # THEN exactly one account row exists, and lookup returns an int
    with Session(repository.engine) as session:
        rows = session.query(Accounts).all()
        assert len(rows) == 1
        assert rows[0].username == BET365_USER
    id = repository.get_account_id_by_username(BET365_USER)
    assert isinstance(id, int)


def test_save_machine_and_idempotency(repository):
    # GIVEN no machines exist
    with Session(repository.engine) as session:
        assert session.query(Machines).count() == 0

    # WHEN I save MACHINE twice
    repository.save_machine_to_db(MACHINE)
    repository.save_machine_to_db(MACHINE)

    # THEN exactly one machine row exists, and lookup returns an int
    with Session(repository.engine) as session:
        rows = session.query(Machines).all()
        assert len(rows) == 1
        assert rows[0].name == MACHINE
    id = repository.get_machine_id_by_name(MACHINE)
    assert isinstance(id, int)


def test_save_tracks_and_idempotency(repository):
    # GIVEN two UK meetings with realistic times
    ascot_time = datetime(2025, 7, 20, 15, 30)
    epsom_time = datetime(2025, 7, 23, 14, 45)
    tracks = {
        "Ascot": [
            ("https://bet365/ascot1", "BF1", "Ascot", ascot_time),
            ("https://bet365/ascot2", "BF2", "Ascot", ascot_time + timedelta(minutes=50)),
        ],
        "Epsom": [
            ("https://bet365/epsom1", "BF3", "Epsom", epsom_time),
        ],
    }

    # WHEN I save them for the first time
    repository.save_tracks_to_db(tracks)

    # THEN I see 3 races in UTC (naive) and correct conversion
    with Session(repository.engine) as session:
        all_races = session.execute(select(Races)).scalars().all()
        assert len(all_races) == 3

        ascot_race = (
            session.query(Races).filter(Races.track == "Ascot", Races.race_number == 1).one()
        )
        expected_utc = melb_to_utc(ascot_time).replace(tzinfo=None)
        assert ascot_race.start_time == expected_utc

    # WHEN I save them again
    repository.save_tracks_to_db(tracks)

    # THEN still only 3 unique races
    with Session(repository.engine) as session:
        assert session.query(Races).count() == 3


def test_save_opportunity_and_idempotency(repository):
    # GIVEN a race at Chepstow exists
    chep_time = datetime(2025, 8, 1, 13, 15)
    repository.save_tracks_to_db(
        {"Chepstow": [("https://bet365/chepstow1", "BF4", "Chepstow", chep_time)]}
    )
    # GIVEN known machine
    repository.save_machine_to_db(MACHINE)

    # AND a real Opportunity for that race
    detected = datetime(2025, 8, 1, 11, 0)
    opp = Opportunity(
        track_name="Chepstow",
        au_race_time=chep_time,
        betfair_market_id="BF4",
        betfair_horse_id=101,
        betfair_lay_odd=5.2,
        betfair_lay_amount=100.0,
        betfair_lay_liquidity=500.0,
        bet365_url="https://bet365/chepstow1",
        bet365_standard_horse_name="Sea The Stars",
        bet365_back_odd=5.0,
        bet365_back_amount=200.0,
        betfair_balance_required=50.0,
        profit_in_dollars=100.0,
        percentage_return=95.0,
        detected_timestamp=detected,
    )

    # WHEN I save it twice
    first_id = repository.save_opportunity_to_db(opp, MACHINE)
    second_id = repository.save_opportunity_to_db(opp, MACHINE)

    # THEN the first returns the hash string and the second is no-op
    assert isinstance(first_id, str)
    assert first_id == opp.get_common_hash()
    assert second_id is None
    with Session(repository.engine) as session:
        assert session.query(Opportunities).count() == 1


def test_save_bet_to_db(repository):
    # GIVEN known account & machine names
    repository.save_account_to_db(BET365_USER)
    repository.save_machine_to_db(MACHINE)

    # AND there is one race & opportunity
    york_time = datetime(2025, 9, 10, 14, 0)
    repository.save_tracks_to_db({"York": [("https://bet365/york1", "BF5", "York", york_time)]})
    detected = datetime(2025, 9, 10, 12, 30)
    opp = Opportunity(
        track_name="York",
        au_race_time=york_time,
        betfair_market_id="BF5",
        betfair_horse_id=202,
        betfair_lay_odd=1.9,
        betfair_lay_amount=150.0,
        betfair_lay_liquidity=1000.0,
        bet365_url="https://bet365/york1",
        bet365_standard_horse_name="Frankel",
        bet365_back_odd=1.8,
        bet365_back_amount=250.0,
        betfair_balance_required=100.0,
        profit_in_dollars=80.0,
        percentage_return=98.5,
        detected_timestamp=detected,
    )
    repository.save_opportunity_to_db(opp, MACHINE)

    # WHEN I place a bet of £25 at 15:00
    exec_time = datetime(2025, 9, 10, 15, 0)
    repository.save_bet_to_db(
        opp, stake=25.0, account_name=BET365_USER, machine_name=MACHINE, executed_at=exec_time
    )

    # THEN a Bets row is created linked to the right entities
    with Session(repository.engine) as session:
        bets = session.query(Bets).filter(Bets.opportunity_id == opp.get_common_hash()).all()
        assert len(bets) == 1
        bet = bets[0]
        assert bet.stake == 25.0
        assert bet.account_id == repository.get_account_id_by_username(BET365_USER)
        assert bet.machine_id == repository.get_machine_id_by_name(MACHINE)
