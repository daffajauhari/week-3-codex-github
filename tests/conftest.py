import os
from collections.abc import Iterator

import pytest
from sqlalchemy import URL, Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ids import ALL_ID_SPECS
from models import Base

TEST_POSTGRES_DB = os.environ.get("TEST_POSTGRES_DB", "week2_test_db")


def _admin_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        database="postgres",
    )


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    admin_engine = create_engine(_admin_url(), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{TEST_POSTGRES_DB}"'))
        connection.execute(text(f'CREATE DATABASE "{TEST_POSTGRES_DB}"'))
    admin_engine.dispose()

    engine = create_engine(_admin_url().set(database=TEST_POSTGRES_DB))
    Base.metadata.create_all(engine)
    # Base.metadata.create_all() only knows about ORM-mapped tables - the
    # sequential ID scheme's sequences live outside that metadata (created
    # via raw SQL in a migration), so recreate them here too.
    with engine.begin() as connection:
        for _, sequence_name, _ in ALL_ID_SPECS:
            connection.execute(text(f"CREATE SEQUENCE {sequence_name} START WITH 1"))

    yield engine

    engine.dispose()
    admin_engine = create_engine(_admin_url(), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{TEST_POSTGRES_DB}"'))
    admin_engine.dispose()


@pytest.fixture()
def db_session(test_engine: Engine) -> Iterator[Session]:
    connection = test_engine.connect()
    transaction = connection.begin()
    # create_savepoint: endpoint code under test commits its own
    # transaction (the revision endpoints wrap their work in a single
    # commit); this makes that commit release a SAVEPOINT instead of the
    # outer connection-level transaction, so the rollback below still
    # discards everything the test wrote.
    session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
