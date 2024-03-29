
import os

import sqlalchemy as sa
import sqlalchemy.orm as so
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase, sessionmaker


load_dotenv()

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


DSN = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}'
engine = sa.create_engine(url=DSN, echo=False)
Session = sessionmaker(bind=engine)
session = Session()


class Base(DeclarativeBase):
    pass


class ImageBase(Base):
    __tablename__ = "telebot_table"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    image_id: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    image_path: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)


def create_tables(engine):
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables(engine)
