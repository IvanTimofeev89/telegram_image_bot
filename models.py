import os

import sqlalchemy as sa
import sqlalchemy.orm as so
from dotenv import load_dotenv
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
TABLE_NAME = os.getenv("TABLE_NAME")

DSN = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgresdb:5432/{POSTGRES_DB}"
engine = sa.create_engine(url=DSN, echo=False)
Session = sessionmaker(bind=engine)
session = Session()


class Base(DeclarativeBase):
    pass


class ImageBase(Base):
    __tablename__ = TABLE_NAME

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    image_id: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    image_path: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)


def create_tables(engine):
    Base.metadata.create_all(bind=engine)

def table_exists(table_name: str | None) -> bool:
    insp = inspect(engine)
    return insp.has_table(table_name)

if __name__ == "__main__":
    create_tables(engine)
