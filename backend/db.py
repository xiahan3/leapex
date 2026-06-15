"""SQLite + SQLModel setup. Single-file DB at ./easybookx.db"""
import os
from sqlmodel import SQLModel, create_engine, Session

DB_PATH = os.environ.get("EASYBOOKX_DB", os.path.join(os.path.dirname(__file__), "easybookx.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db():
    from . import models  # noqa: F401  ensure models register
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as s:
        yield s
