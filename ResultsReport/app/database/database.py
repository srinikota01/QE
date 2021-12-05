from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from . import db_config

SQLALCHEMY_DATABASE_URL = db_config.DB_CON_STR
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    pool_recycle=300,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(object):
    __table_args__ = {
        "mysql_default_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_ai_ci",
    }


Base = declarative_base(Base)
