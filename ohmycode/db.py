from datetime import date

from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

from constants import DATABASE_URL

Base = declarative_base()


def init_db_session() -> Session:
    engine = create_engine(DATABASE_URL)
    print("Connected to DB")
    Base.metadata.create_all(engine)
    print("Created scheme")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal


class Repository(Base):
    __tablename__ = "repository"
    id = Column(Integer, primary_key=True)
    owner = Column(String)
    name = Column(String)
    stats = Column(JSONB, default={})
    __table_args__ = (UniqueConstraint("owner", "name", name="_owner_name_uq"),)

    @classmethod
    def get(cls, session: Session, owner: str, name: str):
        return (
            session.query(cls)
            .filter(cls.owner == owner, cls.name == name)
            .one_or_none()
        )

    @classmethod
    def get_stats(cls, session: Session, owner: str, name: str) -> dict:
        repo = cls.get(session, owner, name)
        print("Got full stats")
        if repo:
            return repo.stats
        else:
            return {}

    @classmethod
    def create_or_update(cls, session: Session, owner: str, name: str, stats: dict = {}):
        repo = cls.get(session, owner, name)
        if repo:
            repo.stats = stats
        else:
            repo = cls(owner=owner, name=name, stats=stats)
            session.add(repo)
        session.commit()

    @classmethod
    def add_today_stats(cls, session: Session, owner: str, name: str, stats: dict):
        today = date.today().strftime("%Y-%m-%d")
        full_stats = cls.get_stats(session, owner, name)
        full_stats[today] = stats
        cls.create_or_update(session, owner, name, full_stats)
        print("Added today stats")