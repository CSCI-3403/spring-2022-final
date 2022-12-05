from dataclasses import dataclass
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy # type: ignore
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text

db = SQLAlchemy()

@dataclass
class Score(db.Model): #type: ignore
    __tablename__ = 'scores'

    identikey: str = db.Column(String(16), ForeignKey('students.identikey'), primary_key=True, nullable=False)
    goal: int = db.Column(Integer, ForeignKey('goals.id'), primary_key=True, nullable=False)
    time: datetime = db.Column(DateTime, nullable=False)
    comment: str = db.Column(Text, nullable=False)

@dataclass
class Student(db.Model): #type: ignore
    __tablename__ = 'students'

    identikey: str = db.Column(db.String(16), primary_key=True, nullable=False)
    start: datetime = db.Column(DateTime, nullable=False)
    end: datetime = db.Column(DateTime, nullable=False)
    scores = db.relationship(Score)

@dataclass
class Goal(db.Model): #type: ignore
    __tablename__ = 'goals'

    id: int = db.Column(db.Integer, primary_key=True, nullable=False)
    name: str = db.Column(Text, nullable=False)
    description: str = db.Column(Text, nullable=False)
    points: int = db.Column(Integer, nullable=False)
    scores = db.relationship(Score)

@dataclass
class History(db.Model): #type: ignore
    __tablename__ = 'history'

    id: int = db.Column(db.Integer, primary_key=True, nullable=False)
    identikey: str = db.Column(String(16), nullable=False)
    ip: str = db.Column(String(16), nullable=False)
    time: datetime = db.Column(DateTime, nullable=False)
    message: str = db.Column(Text, nullable=False)