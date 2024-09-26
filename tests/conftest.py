import pytest
from aws_lambda_typing.context import Context
from sqlalchemy import text

from metr import database
from tests import factories


@pytest.fixture(scope="session")
def setup_db():
    # Ensure all models are in scope so `Base.metadata` is complete:
    import metr.models  # noqa

    database.configure_database()
    database.Base.metadata.create_all(bind=database.Session.kw["bind"])


@pytest.fixture(scope="class")
def fresh_db(setup_db):
    yield
    with database.Session.begin() as s:
        tablenames = [str(t) for t in database.Base.metadata.tables.values()]
        for table in tablenames:
            s.execute(text(f"DELETE FROM {table}"))


@pytest.fixture()
def db_meters(fresh_db):
    with database.Session.begin() as s:
        meters = factories.generate_meters(100)
        s.add_all(meters)
        s.flush()
        s.expunge_all()
    return meters


class MockContext(Context):
    @staticmethod
    def get_remaining_time_in_millis() -> int:
        return 5_000


@pytest.fixture()
def lambda_context():
    return MockContext()
