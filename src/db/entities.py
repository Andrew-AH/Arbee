from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import expression


class Base(DeclarativeBase):
    pass


class Events(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("venue", "start_time", name="unique_venue_start_time"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    venue: Mapped[str]
    start_time: Mapped[datetime]
    event_number: Mapped[int]
    number_of_items: Mapped[Optional[int]]
    vendor_beta_market_id: Mapped[str]
    vendor_alpha_url: Mapped[str]
    winner: Mapped[Optional[str]]


class Accounts(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("username", name="unique_username"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    is_limited: Mapped[bool] = mapped_column(server_default=expression.false())


class Machines(Base):
    __tablename__ = "machines"
    __table_args__ = (UniqueConstraint("name", name="unique_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]


class Opportunities(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "item",
            "buy_price",
            "sell_price",
            name="unique_event_item_buy_sell",
        ),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"))
    item: Mapped[str]
    buy_price: Mapped[float]
    sell_price: Mapped[float]
    ev_percentage: Mapped[float]
    first_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class Transactions(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"))
    amount: Mapped[float]
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
