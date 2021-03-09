from flask import Flask, render_template, request
from contextlib import contextmanager
from operator import itemgetter
import epicbox
import psycopg2
from psycopg2.extras import RealDictCursor
import os, re

app = Flask(__name__)

@contextmanager
def db_cur():
    with psycopg2.connect(database='connect4', user='', password='', host='127.0.0.1', port='5432', cursor_factory=RealDictCursor) as conn:
        with conn.cursor() as curs:
            yield curs

@app.route('/run', methods=('POST',))
def run():
    username, fullname = request.args.get('username', '').lower(), request.args.get('fullname', '').title()
    if username is None or len(username) <= 5:
        return render_template('notify.html', level='warning', title='Invalid Input', message='Username must be longer '
                                                                                             'than 5 characters!')
    if len(username) >= 50:
        return render_template('notify.html', level='warning', title='Invalid Input', message='Username must be longer '
                                                                                              'shorter than 50 characters.')
    if not username.isalnum():
        return render_template('notify.html', level='warning', title='Invalid Input', message='Username must be alphanumeric '
                                                                                              'only!')
    if fullname is None or len(fullname) <= 5:
        return render_template('notify.html', level='warning', title='Invalid Input', message='Name must be longer '
                                                                                              'than 5 characters!')
    if len(fullname) >= 50:
        return render_template('notify.html', level='warning', title='Invalid Input', message='Your full name must be '
                                                                                              'shorter than 50 characters!')
    if not re.match('^[a-zA-Z0-9 ]+$', fullname):
        return render_template('notify.html', level='warning', title='Invalid Input', message='Full name must be alphanumeric '
                                                                                              'only!')
    if len(request.get_data()) <= 0:
        return render_template('notify.html', level='warning', title='Invalid Input', message='No code submitted!')

    root = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    epicbox.configure(
        profiles=[
            epicbox.Profile('python', 'python:3.6.5-alpine')
        ]
    )

    limits = {'cputime': int(60 * 5.5), 'realtime': None, 'memory': 64}
    files = [{'name': 'game.py', 'content': request.get_data()}]
    for file_name in ['benchmark.py', 'game_base.py']:
        with open(os.path.join(root, file_name), 'r') as t:
            data = '\n'.join(t.readlines())
        files.append({'name': file_name, 'content': data.encode()})
    stats = epicbox.run('python', 'python3 benchmark.py', files=files, limits=limits)

    if stats['exit_code'] == 0:
        raw_results = stats['stdout'].decode().split('\n')[-1].split(',')
        if len(raw_results) < 3:
            return render_template('notify.html', level='danger', title='Error!',
                                   message=f'Unknown error \n{stats["stdout"].decode()} \n{stats["stderr"].decode()}')

        wins, ties, loss = map(int, raw_results)
        score, duration = wins / (wins + ties + loss), stats['duration']
        with db_cur() as cur:
            sql = 'INSERT INTO submissions (username,fullname,score,wins,loss,ties,duration) VALUES(%s,%s,%s,%s,%s,%s,%s)'
            cur.execute(sql, (username, fullname, score, wins, loss, ties, duration))
        return render_template('notify.html', level='success', title='Leaderboard Submission Success!',
                               message=f'Wins: {wins}, Ties: {ties}, Loss: {loss}, Duration: {duration}')
    else:
        print(stats)
        return render_template('notify.html', level='danger',title='Error!',
                               message=f'Unknown error \n{stats["stdout"].decode()} \n{stats["stderr"].decode()}')


@app.route('/')
def index():
    sql = '''
      SELECT DISTINCT ON (t1.username)
            *
        FROM submissions t1
        INNER JOIN (SELECT username, COUNT(*) FROM submissions GROUP BY username) t2
        ON t1.username = t2.username
        ORDER BY t1.username, score DESC;
    '''
    with db_cur() as cur:
        cur.execute(sql)
        submissions = list(sorted((dict(row) for row in cur.fetchall()), reverse=True, key=itemgetter('score')))
        for i, row in enumerate(submissions, start=1):
            row['rank'] = i
            row['username'] = row['username'].strip()
            row['fullname'] = row['fullname'].strip()
    return render_template('index.html', submissions=submissions)
