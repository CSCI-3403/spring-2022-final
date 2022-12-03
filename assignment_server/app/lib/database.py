from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.sql import func # type: ignore
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Float, create_engine, DateTime, ForeignKey, Integer, String, Text

Base = declarative_base()

@dataclass
class User(Base): # type: ignore
    __tablename__ = 'users'

    username: str = Column(String(16), primary_key=True, nullable=False) # type: ignore
    profile_picture: str = Column(Text, nullable=False, default='user.jpg') # type: ignore
    balance: float = Column(Float, nullable=False, default=0) # type: ignore
    private: bool = Column(Boolean, nullable=False, default=False) # type: ignore
    biography: str = Column(Text, nullable=False, default='No biography') # type: ignore

@dataclass
class Transaction(Base): # type: ignore
    __tablename__ = 'transactions'

    id: int = Column(Integer, primary_key=True, autoincrement=True) # type: ignore
    sender: str = Column(String(16), nullable=False) # type: ignore
    recipient: bool = Column(String(16), nullable=False) # type: ignore
    amount: float = Column(Float, nullable=False) # type: ignore
    time: datetime = Column(DateTime, server_default=func.now(), nullable=False) # type: ignore

@dataclass
class Message(Base): # type: ignore
    __tablename__ = 'messages'

    id: int = Column(Integer, primary_key=True, autoincrement=True) # type: ignore
    user: str = Column(String(16), ForeignKey('users.username'),  nullable=False) # type: ignore
    from_support: bool = Column(Boolean, nullable=False) # type: ignore
    time: datetime = Column(DateTime, server_default=func.now()) # type: ignore
    message: str = Column(Text, nullable=False) # type: ignore

class DatabaseManager:
    PRIVATE_USERNAME = 'Eve'
    ALICE_BALANCE = 729.75
    sessions: Dict[str, scoped_session] = {}

    def new_session(self, identikey: str) -> scoped_session:
        engine_url = 'sqlite:///dbs/{}.sqlite3'.format(identikey)
        engine = create_engine(engine_url)
        Base.metadata.create_all(bind=engine)

        session = scoped_session(sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine))
        
        for user in [
            User(username=identikey, balance=100.00, profile_picture='user.jpg'),
            User(username='Alice', balance=self.ALICE_BALANCE, profile_picture='alice.jpg', biography='Hi! I\'m Alice! 🙂'),
            User(username='Bob', balance=184.12, profile_picture='bob.jpg', biography='This is a cool site. I love being super secure!'),
            User(username='Carol', balance=-67.19, profile_picture='carol.jpg', biography='No biography'),
            User(username='support', balance=999.99, profile_picture='support.jpg', biography='No biography', private=True),
            User(username=self.PRIVATE_USERNAME, balance=782.21, profile_picture='private.jpg', private=True, biography='If you are reading this, don\'t tell the admins about me...')]:
            session.merge(user)

        session.commit()

        return session

    def session(self, identikey: str) -> scoped_session:
        session = self.sessions.get(identikey)

        if not session:
            session = self.new_session(identikey)
            self.sessions[identikey] = session
        
        return session