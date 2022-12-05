import logging
import json
import sqlite3
import sys
from typing import Any, Dict, Optional, Tuple, Union
import click

from flask import Flask, abort, current_app, flash, redirect, render_template, request, session, g, url_for
from flask_wtf import FlaskForm # type: ignore
from werkzeug.wrappers import Response
from wtforms import DecimalField, StringField # type: ignore
from wtforms.validators import InputRequired, Length # type: ignore
from sqlalchemy.exc import DatabaseError
from sqlalchemy import or_

from lib.database import DatabaseManager, Message, Transaction, User # type: ignore
from lib.goals import accomplish_goal, get_all_goals, get_completed, history, login # type: ignore
from lib.support import handle_message # type: ignore

View = Union[Response, str, Tuple[str, int]]
class InsecureForm(FlaskForm):
    class Meta:
        csrf = False

with open('secrets.json') as f:
    secrets = json.loads(f.read())

# Init app
app = Flask(__name__)
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.secret_key = secrets['secret_key']

# Init database
db = DatabaseManager()

# Init goals
goals = get_all_goals()

# Init logging
log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

@app.context_processor
def inject_vars() -> Dict[str, Any]:
    identikey = session.get('identikey')

    if not identikey:
        return {}

    return {
        'identikey': identikey,
        'goals': goals,
        'completed': get_completed(identikey),
    }

@app.before_request
def before_request() -> Optional[Response]:
    # The support server will add this StudentIdentikey header, so we know which database to use
    # If it exists, the message is from that server (or a very clever student, but hopefully not)
    if 'StudentIdentikey' in request.headers:
        g.identikey = 'support'
        g.dbsession = db.session(request.headers['StudentIdentikey'])
    # Otherwise, check for the identikey in the session cookie
    elif identikey := session.get('identikey'):
        g.identikey = identikey
        g.dbsession = db.session(identikey)
    # If it does not exist, redirect to /set_identikey
    elif request.path not in ['/set_identikey', '/static/main.css']:
        log.info('Got non-logged-in request for {}'.format(request.path))
        return redirect(url_for('set_identikey'))

    return None

@app.teardown_appcontext
def shutdown_session(exception: BaseException = None) -> None:
    if 'dbsession' in g:
        g.dbsession.remove()

@app.route('/')
def index() -> View:
    return render_template('index.html')

@app.route('/users')
def users() -> View:
    query = request.args.get('query', '')
    sql = "SELECT username, profile_picture FROM users WHERE username LIKE '%" + query + "%' AND private=False"

    history(g.identikey, 'Ran SQL search: {}'.format(sql))

    # Check for different kinds of SQL errors, and report them to the user
    try:
        results = g.dbsession.execute(sql).all()
    except sqlite3.Warning as e:
        return render_template('users.html', query=query, error=e, sql=sql)
    except DatabaseError as e:
        return render_template('users.html', query=query, error=e.orig, sql=sql)
        
    if not results:
        return render_template('users.html', query=query, error='No results for: {}'.format(query))

    # If any of the results are the private user or balance, accomplish those goals! \[T]/
    if any(db.PRIVATE_USERNAME in result for result in results):
        accomplish_goal(g.get('identikey'), goals[0], sql)
    if any(db.ALICE_BALANCE in result for result in results):
        accomplish_goal(g.get('identikey'), goals[1], sql)

    return render_template('users.html', query=query, results=results)

class BioForm(InsecureForm):
    biography = StringField('Biography', [InputRequired()])

class TransactionForm(InsecureForm):
    to = StringField('To', [InputRequired()])
    amount = DecimalField('Amount', [InputRequired()], places=2)

@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username: str) -> View:
    user = g.dbsession.query(User).filter(User.username == username).first()
    form = BioForm()

    if form.validate_on_submit():
        history(g.identikey, 'Updated bio: {}'.format(form.biography.data))

        if username == g.identikey:
            g.dbsession.query(User).filter(User.username==username).update({ 'biography': form.biography.data })
            g.dbsession.commit()

        redirect(url_for('profile', username=username))

    transactions = (g.dbsession.query(Transaction)
        .filter(or_(Transaction.sender == username, Transaction.recipient == username))
        .all())
    
    return render_template(
        'profile.html',
        user=user,
        transactions=transactions)

@app.route('/transaction', methods=['POST'])
def transaction() -> View:
    identikey = g.identikey
    form = TransactionForm()

    if form.validate_on_submit():
        amount = float(form.amount.data)
        history(g.identikey, 'Made transaction: ${} to {}'.format(amount, form.to.data))

        # If the transaction is to the current user, prevent it
        if form.to.data == identikey:
            referer = request.headers.get('Referer', '')
            # ...however, if the request did not come from this page (which we can tell from the 
            # Referer header) then it came from a CSRF attack. Or they removed the Referer header,
            # but what are the chances of that?
            if 'final.csci3403.com' not in referer and 'burp' not in referer:
                accomplish_goal(identikey, goals[3], 'Referer: {}'.format(referer))

            flash('You cannot send money to yourself', category='warning')
            return redirect(url_for('profile', username=identikey))

        # If they sent a negative amount, mark that goal as complete!
        if identikey != 'support' and amount < 0:
            accomplish_goal(identikey, goals[2], str(form))

        # If the request comes from support, somebody must have tricked them into sending money
        # through XSS! Goal complete.
        if identikey == 'support':
            student_identikey = request.headers['StudentIdentikey']
            history(student_identikey, 'Tricked support: ${} to {}'.format(amount, form.to.data))

            # Only accomplish the goal if the student is sending it to themselves (and not another user)
            if form.to.data == student_identikey:
                accomplish_goal(student_identikey, goals[4], '')

        g.dbsession.add(Transaction(
            sender=identikey,
            recipient=form.to.data,
            amount=amount))
        g.dbsession.commit()

        return render_template(
            'transaction.html',
            form=form,
            recipient=form.to.data,
            amount=amount)
    
    return render_template('transaction.html', form=form)

class SupportForm(InsecureForm):
    message = StringField('Message', [InputRequired(), Length(min=0, max=512)])

@app.route('/support')
def support() -> View:
    form = SupportForm()

    messages = g.dbsession.query(Message).filter(Message.user == g.get('identikey')).all()
    return render_template('support.html', messages=messages, form=form)

# I don't know why GET /support and POST /message use separate paths. Well, I do know, and the
# answer is tech debt. They should both just point to /support but whatever.
@app.route('/message', methods=['POST'])
def message() -> View:
    identikey = g.get('identikey')
    form = SupportForm()

    if form.validate_on_submit():
        history(g.identikey, 'Messaged support: {}'.format(form.message.data))
        response = handle_message(form.message.data, identikey)
        
        g.dbsession.add(Message(user=identikey, message=form.message.data, from_support=False))
        g.dbsession.add(Message(user=identikey, message=response, from_support=True))
        g.dbsession.commit()
    
        return (response, 200)
    else:
        # This should never happen unless the student is mucking around with the support HTML
        return ('Bad form', 400)

@app.route('/instructions')
def instructions() -> View:
    return render_template('instructions.html', goals=goals)

@app.route('/reset', methods=['POST'])
def reset() -> View:
    history(g.identikey, 'Reset account')

    g.dbsession.query(Transaction).delete()
    g.dbsession.query(User).update({ 'biography': 'No biography' })
    g.dbsession.commit()
    return redirect(url_for('index'))

class IdentikeyForm(InsecureForm):
    identikey = StringField('Identikey', [InputRequired(), Length(min=1, max=16)])

@app.route('/set_identikey', methods=['GET', 'POST'])
def set_identikey() -> View:
    # Automatically use test_student as the identikey when running locally, no need to log in then
    if app.debug:
        session['identikey'] = 'test_student'

        return redirect(url_for('instructions'))

    form = IdentikeyForm()

    if form.validate_on_submit():
        result = login(form.identikey.data)
        if 'error' in result:
            form.identikey.errors.append(result['error'])
        else:
            session['identikey'] = form.identikey.data
            return redirect(url_for('instructions'))

    return render_template('set_identikey.html', form=form)

@click.command()
@click.option('--debug', is_flag=True)
@click.option('--port', type=int, default=80)
def main(debug: bool, port: int) -> None:
    log.info('Running on port {}'.format(port))
    app.run("0.0.0.0", debug=debug, port=port)

if __name__ == "__main__":
    main()
