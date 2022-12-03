from dataclasses import dataclass
from typing import Any, List, Set
import requests

from flask import flash, request

SERVER_URL = 'http://score'

@dataclass
class Goal:
    id: int
    name: str
    description: str
    points: int

@dataclass
class Student:
    completed: Set[int]
    cheated: Set[int]

def login(identikey: str) -> Any:
    response = requests.post('{}/login/{}'.format(SERVER_URL, identikey))
    response.raise_for_status()

    return response.json()

def accomplish_goal(identikey: str, goal: Goal, cheating_detected: bool, comment: str) -> Any:
    response = requests.post(
        '{}/update/{}'.format(SERVER_URL, identikey),
        json={
            'goal': goal.id,
            'cheating_detected': cheating_detected,
            'comment': comment,
        })
    response.raise_for_status()

    history(identikey, 'Completed goal #{}: {}'.format(goal.id, comment))
    flash('Completed a goal: {}!'.format(goal.name), category='goal')

    return response.json()

def get_all_goals() -> List[Goal]:
    response = requests.get('{}/goals'.format(SERVER_URL))
    response.raise_for_status()

    return [
        Goal(
            id=goal['id'],
            name=goal['name'],
            description=goal['description'],
            points=goal['points'],
        )
        for goal in response.json()]

def get_completed(identikey: str) -> Set[int]:
    response = requests.get('{}/status/{}'.format(SERVER_URL, identikey))
    response.raise_for_status()

    return set(goal['id'] for goal in response.json())

def history(identikey: str, message: str) -> None:
    response = requests.get('{}/history'.format(SERVER_URL), json={
        'ip': request.headers.get('X-Forwarded-For', 'Unknown'),
        'identikey': identikey,
        'message': message,
    })
    response.raise_for_status()
