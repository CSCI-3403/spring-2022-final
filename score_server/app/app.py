from datetime import datetime, timedelta
import logging
import sys
from typing import Union

import click
import pytz # type: ignore
from flask import Flask, abort, jsonify, render_template, request
from sqlalchemy import and_, func
from werkzeug.wrappers import Response

from lib.database import db, Goal, History, Score, Student # type: ignore
from lib.goals import goals # type: ignore

View = Union[Response, str]

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger('werkzeug').disabled = True

# Set up app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'qwer'

# Set up database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scores.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

    for goal in goals:
        db.session.merge(goal)

    db.session.commit()

@app.route('/')
def index() -> View:
    results = (
        db.session.query(Student.identikey, func.group_concat(Score.goal))
            .outerjoin(Score, Score.identikey==Student.identikey)
            .group_by(Student.identikey)
            .all())
    return render_template('index.html', results=results)

@app.route('/student/<identikey>')
def student(identikey: str) -> View:
    query = (db.session.query(Goal.id, Score.cheating_detected, Score.comment, Score.time)
            .outerjoin(Score, Score.goal==Goal.id)
            .filter(Score.identikey==identikey))
    goals = query.all()
    history = db.session.query(History).filter(History.identikey==identikey).all()
    return render_template('student.html', goals=goals, history=history)

@app.route('/goals')
def get_goals() -> View:
    return jsonify(Goal.query.all())

@app.route('/login/<identikey>', methods=['POST'])
def login(identikey: str) -> View:
    student = db.session.query(Student).filter(Student.identikey == identikey).first()
    if not student:
        return jsonify({ 'error': 'No student with that identikey' })
    
    now = datetime.now() - timedelta(hours=6)
    time_until_start = student.start - now
    if time_until_start.total_seconds() > 0:
        return jsonify({ 'error': 'Exam will become available at: {}'.format(student.start.strftime('%m/%d %I:%M%p')) })

    if now > student.end:
        return jsonify({ 'error': 'Exam has closed' })

    return jsonify({})

@app.route('/update/<identikey>', methods=['POST'])
def update(identikey: str) -> View:
    try:
        goal = int(request.json['goal']) # type: ignore
        cheating_detected = bool(request.json['cheating_detected']) # type: ignore
        comment = str(request.json['comment']) # type: ignore
    except KeyError:
        abort(400)

    instance = (db.session.query(Score)
        .filter_by(identikey=identikey, goal=goal)
        .first())
    
    if instance:
        return jsonify(instance)

    score = Score(
        identikey=identikey,
        goal=int(goal),
        time=datetime.now(pytz.timezone('US/Mountain')),
        cheating_detected=cheating_detected,
        comment=comment)
    db.session.merge(score)
    db.session.commit()

    return jsonify(score)

@app.route('/status/<identikey>')
def score(identikey: str) -> View:
    query = (db.session.query(Goal.id, Score.cheating_detected, Score.comment, Score.time)
            .outerjoin(Score, Score.goal==Goal.id)
            .filter(Score.identikey==identikey))
    return jsonify([q._asdict() for q in query.all()])

@app.route('/history')
def history() -> View:
    ip = request.json.get('ip') # type: ignore
    identikey = request.json.get('identikey') # type: ignore
    message = request.json.get('message') # type: ignore
    time = datetime.now()

    db.session.add(History(ip=ip, identikey=identikey, time=time, message=message))
    db.session.commit()

    return 'ok'

@click.command()
@click.option('--debug', is_flag=True)
@click.option('--port', type=int, default=80)
def main(debug: bool, port: int) -> None:
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    log.info('Starting grading server on port {}'.format(port))

    app.run("0.0.0.0", debug=debug, port=port)

if __name__ == '__main__':
    main()