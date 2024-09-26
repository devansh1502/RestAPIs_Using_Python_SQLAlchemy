from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
Session = sessionmaker()


def configure_database(conn_url: str = "sqlite://"):
    engine = create_engine(conn_url, future=True)
    Session.configure(bind=engine, future=True)
