import re, os
import logging
import traceback
from operator import itemgetter

from flask import Flask, render_template, request, abort, Response
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException

from bench import load_file, run_benchmark, db_cur

load_dotenv()
app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    log = gunicorn_logger

log = app.logger

def notify(**kwargs):
    return render_template('notify.html', level='success', **kwargs)


def warn_input(username, **kwargs):
    log.info(f'{username} - {kwargs["message"]}')
    abort(Response(render_template('notify.html', title='Invalid Input!', level='warning', **kwargs)))


def error(username, title='Error!', **kwargs):
    log.warning(f'{username} - {kwargs["message"]}')
    abort(Response(render_template('notify.html', title=title, level='danger', **kwargs)))


@app.route('/run', methods=('POST',))
def run():
    cl, args = request.content_length, request.args
    username, fullname, passcode = args.get('username', '').lower(), args.get('fullname', '').title(), args.get('passcode', '')
    cl_max = int(os.getenv('MAX_CONTENT_SIZE_MB'))

    # Username
    log.info(f'{username} atttempting submission.')
    code = request.get_data() # Must read the upload in to return an error. Unsure why.
    if len(username) <= 5: warn_input(username=username, message='Username must be longer than 5 characters!')
    if len(username) >= 50: warn_input(username=username, message='Username must be longer shorter than 50 characters.')
    if not username.isalnum(): warn_input(username=username, message='Username must be alphanumeric only!')
    # Name
    if len(fullname) <= 5: warn_input(username=username, message='Name must be longer than 5 characters!')
    if len(fullname) >= 100: warn_input(username=username, message='Name must be shorter than 100 characters!')
    if not re.match('^[a-zA-Z0-9 ]+$', fullname): return warn_input(username=username, message='Full name must be alphanumeric only!')
    # Code
    if cl is None or cl <= 0: warn_input(username=username, message='No code submitted!')
    if cl > cl_max * 1024 * 1024: warn_input(username=username, message=f'Code must not be larger than {cl_max}MB!')
    # Passcode
    if len(passcode) < 5: warn_input(username=username, message='5-Digit code is required!')
    if len(passcode) > 10: warn_input(username=username, message='5-Digit code cannot be longer than 10 digits!')
    if not passcode.isnumeric(): warn_input(username=username, message='5-Digit code must be numeric only!')

    with db_cur() as cur:
        cur.execute('select passcode from users where username = %s;', (username,))
        user = cur.fetchone()
        if user is not None and user['passcode'] != passcode: return warn_input(message='Incorrect passcode! Try again.')


    stats = run_benchmark(code, load_file('base_game.py').encode(),
        executions=int(os.getenv('BENCHMARK_EXECUTIONS')),
        max_execution_millis=int(os.getenv('MAX_EXECUTION_MILLIS'))
    )

    if not stats['success']:
        if stats['timeout']:
            error(username=username, title='Execution Error!', message=f'Execution did not complete before timeout. Please optimize code '
                                                                        'before re-submitting.')
        else:
            error(username=username, message=f'Unknown error \n{stats["stdout"].decode()} \n{stats["stderr"].decode()}')

    wins, ties, loss, duration = stats['wins'], stats['ties'], stats['loss'], stats['duration']
    with db_cur() as cur:
        if user is None:
            sql = 'INSERT INTO users (username, passcode, code, fullname) VALUES (%s,%s,%s,%s)'
            cur.execute(sql, (username, passcode, request.get_data().decode(), fullname))
        else:
            sql = '''UPDATE users 
                     SET submissions = submissions + 1,
                         code = %s
                     WHERE username = %s;'''
            cur.execute(sql, (code.decode(), username))
    log.info(f'{username} - {wins} {ties} {loss}')
    return notify(title='Leaderboard Submission Success!',  message=f'Wins: {wins}, Ties: {ties}, Loss: {loss}, Duration: {duration}')



@app.route('/')
def index():
    with db_cur() as cur:
        cur.execute('SELECT id, timestamp FROM computation_history ORDER BY timestamp DESC LIMIT 1;')
        computation = cur.fetchone()

        if computation is not None:
            sql = '''
                SELECT r.username, r.wins, r.ties, r.loss, r.score, u.fullname, u.submissions, (duration / (r.wins + r.ties + r.loss)) as avg_duration
                FROM results r
                LEFT JOIN users u on u.username = r.username
                WHERE computation_id = %s
                ORDER BY score DESC, duration ASC
            '''
            cur.execute(sql, (computation['id'],))
            submissions = list(sorted((dict(row) for row in cur.fetchall()), reverse=True, key=itemgetter('score')))
        else:
            submissions = []

    for i, row in enumerate(submissions, start=1):
        row['rank'] = i
        row['username'] = row['username'].strip()
        row['fullname'] = row['fullname'].strip()

    return render_template(
        'index.html',
        submissions=submissions,
        max_content_size=int(os.getenv('MAX_CONTENT_SIZE_MB')),
        max_execution_millis=int(os.getenv('MAX_EXECUTION_MILLIS')),
        executions=int(os.getenv('BENCHMARK_EXECUTIONS')),
        container_memory=int(os.getenv('CONTAINER_MEMORY_MB')),
        updated=computation['timestamp'] if computation else 'Awaiting First Update',
        compute_schedule=os.getenv('COMPUTE_SCHEDULE')
    )
