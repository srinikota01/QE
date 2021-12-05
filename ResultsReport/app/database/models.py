from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, TEXT, NVARCHAR, DDL, event, Date
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "user"
    userId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userName = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)


class Results(Base):
    __tablename__ = "results"
    resultId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(150), nullable=False)
    testcases = Column(Integer, nullable=False)
    passed = Column(Integer, nullable=False)
    failed = Column(Integer, nullable=False)
    skipped = Column(Integer, nullable=False)
    passpercentage = Column(Integer, nullable=False)
    environment = Column(String(150), nullable=False)
    datetime = Column(DateTime, nullable=False)
    comments = Column(String(200), nullable=False)
