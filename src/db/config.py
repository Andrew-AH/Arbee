from sqlalchemy import Engine, create_engine

from db.entities import Base
from libs.utils.log import get_logger

log = get_logger(logs_to_console=True)

IN_MEMORY_DB_URL = "sqlite:///:memory:"


def get_db_engine(url: str, verbose_logs: bool = False) -> Engine:
    # pool_pre_ping=True ensures that connections are checked before use
    engine = create_engine(url, pool_pre_ping=True, echo=verbose_logs)
    Base.metadata.create_all(bind=engine)
    return engine
