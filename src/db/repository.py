from datetime import datetime
from typing import Optional

from psycopg2 import OperationalError
from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.entities import Accounts, Transactions, Machines, Opportunities, Events
from libs.models.opportunity import Opportunity
from libs.utils.datetimes import melb_to_utc
from libs.utils.log import get_logger
from libs.utils.retry import retry_on_exception

log = get_logger(logs_to_file=True, logs_to_console=True)


class Repository:
    def __init__(self, engine: Engine):
        self.engine = engine

    @retry_on_exception(retries=5, delay=2, exceptions=(OperationalError,), logger=log)
    def save_venues_to_db(self, venues: dict[str, list[tuple[str, str, str, datetime]]]):
        with Session(self.engine) as session:
            for events in venues.values():
                values = [
                    {
                        "venue": venue_name,
                        "start_time": melb_to_utc(event_date_time),
                        "event_number": idx + 1,
                        "vendor_alpha_url": vendor_alpha_url,
                        "vendor_beta_market_id": vendor_beta_market_id,
                    }
                    for idx, (
                        vendor_alpha_url,
                        vendor_beta_market_id,
                        venue_name,
                        event_date_time,
                    ) in enumerate(events)
                ]

                stmt = (
                    insert(Events)
                    .values(values)
                    .on_conflict_do_nothing(
                        index_elements=["venue", "start_time"]
                    )  # unique constraint
                )

                session.execute(stmt)
                session.commit()
                log.info(f"`{events[0][2]}` events saved to database")

    @retry_on_exception(retries=5, delay=2, exceptions=(OperationalError,), logger=log)
    def save_account_to_db(self, username: str):
        with Session(self.engine) as session:
            stmt = (
                insert(Accounts)
                .values(username=username)
                .on_conflict_do_nothing(index_elements=["username"])
            )
            result = session.execute(stmt)
            session.commit()

            if result.rowcount:
                log.info(f"Account `{username}` saved to database")
            else:
                log.info(f"Account `{username}` already exists")

    @retry_on_exception(retries=5, delay=2, exceptions=(OperationalError,), logger=log)
    def save_machine_to_db(self, name: str):
        with Session(self.engine) as session:
            stmt = (
                insert(Machines).values(name=name).on_conflict_do_nothing(index_elements=["name"])
            )
            result = session.execute(stmt)
            session.commit()

            if result.rowcount:
                log.info(f"Machine `{name}` saved to database")
            else:
                log.info(f"Machine `{name}` already exists")

    @retry_on_exception(retries=5, delay=2, exceptions=(OperationalError,), logger=log)
    def save_opportunity_to_db(self, opp: Opportunity, machine_name: str) -> Optional[int]:
        with Session(self.engine) as session:
            query = select(Events.id).where(
                Events.venue == opp.venue_name,
                Events.start_time == melb_to_utc(opp.au_event_time),
            )

            event_id = session.scalar(query)
            machine_id = self.get_machine_id_by_name(machine_name)

            command = (
                insert(Opportunities)
                .values(
                    id=opp.get_common_hash(),
                    event_id=event_id,
                    machine_id=machine_id,
                    item=opp.vendor_alpha_standard_item_name,
                    buy_price=opp.vendor_alpha_buy_price,
                    sell_price=opp.vendor_beta_sell_price,
                    ev_percentage=opp.percentage_return,
                    first_detected_at=melb_to_utc(opp.detected_timestamp),
                )
                .on_conflict_do_nothing(index_elements=["event_id", "item", "buy_price", "sell_price"])
                .returning(Opportunities.id)
            )
            result = session.execute(command)
            opp_id = result.scalar_one_or_none()

            if opp_id:
                session.commit()
                log.info(f"Opportunity `{opp_id}` saved to database")
            return opp_id

    @retry_on_exception(retries=5, delay=2, exceptions=(OperationalError,), logger=log)
    def save_transaction_to_db(
        self,
        opp: Opportunity,
        amount: float,
        account_name: str,
        machine_name: str,
        executed_at: datetime,
    ):
        with Session(self.engine) as session:
            account_id = self.get_account_id_by_username(account_name)
            machine_id = self.get_machine_id_by_name(machine_name)
            opp_id = opp.get_common_hash()

            command = (
                insert(Transactions)
                .values(
                    opportunity_id=opp_id,
                    account_id=account_id,
                    machine_id=machine_id,
                    amount=amount,
                    detected_at=melb_to_utc(opp.detected_timestamp),
                    executed_at=melb_to_utc(executed_at),
                )
                .returning(Transactions.id)
            )
            result = session.execute(command)
            transaction_id = result.scalar_one_or_none()

            if transaction_id:
                session.commit()
                log.info(f"Transaction with id `{transaction_id}` tied to opportunity `{opp_id}` saved to database")

    def get_account_id_by_username(self, username: str) -> Optional[int]:
        with Session(self.engine) as session:
            query = select(Accounts.id).where(Accounts.username == username)
            account_id = session.scalar(query)
            return account_id

    def get_machine_id_by_name(self, name: str) -> Optional[int]:
        with Session(self.engine) as session:
            query = select(Machines.id).where(Machines.name == name)
            machine_id = session.scalar(query)
            return machine_id
