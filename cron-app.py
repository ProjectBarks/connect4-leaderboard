import os
import sys
import time
import logging
from operator import add
from itertools import combinations, chain

import pycron
from tqdm.contrib.concurrent import process_map
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

from bench import run_benchmark, db_cur

load_dotenv()
log = logging.getLogger('cron-app')
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=os.environ.get('LOGLEVEL', 'INFO'),
    datefmt='%Y-%m-%d %H:%M:%S'
)

def single_game(players):
    p1, p2 = players
    max_execution = int(os.getenv('MAX_EXECUTION_MILLIS')) * 2  # Double for two AI's
    result = run_benchmark(p1['code'].encode(), p2['code'].encode(),
                           executions=2, rotate_first_move=False, max_execution_millis=max_execution)

    if not result['success']:
        return []

    return [
        (p1['username'], (result['wins'], result['ties'], result['loss'])),
        (p2['username'], (result['loss'], result['ties'], result['wins']))
    ]


def tournament():
    def score(wins, ties, loss):
        total = wins + ties + loss
        return 0 if total == 0 else wins / total
    with db_cur() as cur:
        cur.execute('SELECT username, code FROM users;')
        users = cur.fetchall()

    user_matches = list(combinations(users, 2))
    results, succeeded, start = {}, 0, time.time()
    for (player, scores) in chain.from_iterable(process_map(single_game, user_matches)):
        past_scores = results.get(player, (0,0,0))
        results[player] = tuple(map(add, scores, past_scores))
        succeeded += 1
    duration = int(time.time() - start)
    succeeded //= 2

    with db_cur() as cur:
        sql = 'INSERT INTO computation_history (duration, failed, computed) VALUES (%s, %s, %s) RETURNING id'
        cur.execute(sql, (duration, len(user_matches) - succeeded, succeeded))
        computation_id = cur.fetchone()['id']

    with db_cur() as cur:
        sql = 'INSERT INTO results (username, computation_ID, wins, ties, loss, score) VALUES (%s, %s, %s, %s, %s, %s)'
        query_var_iter = ((username, computation_id, *scores, score(*scores)) for username, scores in results.items())
        execute_batch(cur, sql, query_var_iter)


if __name__ == '__main__':
    if len(sys.argv) > 1 and (sys.argv[1] == '--now' or sys.argv[1] == '-n'):
        tournament()
        sys.exit()

    schedule = os.getenv('COMPUTE_SCHEDULE')
    log.info('Awaiting next scheduled computation window')
    while True:
        if pycron.is_now(schedule):
            log.info('Running')
            tournament()
        else:
            time.sleep(15)  # Check again in 15 seconds
