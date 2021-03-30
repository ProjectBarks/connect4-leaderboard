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
log = logging.getLogger('cron_app')
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=os.environ.get('LOGLEVEL', 'INFO'),
    datefmt='%Y-%m-%d %H:%M:%S'
)

def single_game(players):
    p1, p2 = players
    executions = int(os.getenv('MATCH_EXECUTIONS'))

    result = run_benchmark(p1['code'].encode(), p2['code'].encode(),
                           executions=executions,
                           rotate_first_move=True,
                           max_execution_millis=int(os.getenv('MAX_EXECUTION_MILLIS')) * 2  # Double for two AI's
            )

    if not result['success']:
        # Errors or timeouts are considered ties
        # This is the best response to the halting problem and reflects how ties are handled in chess
        return [
            (p1['username'], (0, executions, 0)),
            (p2['username'], (0, executions, 0))
        ]

    return [
        (p1['username'], (result['wins'], result['ties'], result['loss'])),
        (p2['username'], (result['loss'], result['ties'], result['wins']))
    ]


def tournament(force=False):
    def score(wins, ties, loss):
        total = wins + ties + loss
        return 0 if total == 0 else wins / total
    with db_cur() as cur:
        cur.execute('SELECT username, code, submissions FROM users;')
        users = cur.fetchall()

        cur.execute('SELECT submissions FROM computation_history ORDER BY timestamp DESC LIMIT 1;')
        history = cur.fetchone()

    total_submissions = sum(u['submissions'] for u in users)
    if not force and history is not None and total_submissions == history['submissions']:
        log.info('Aborting! No changes detected.')
        return

    # TODO - Cache game results from unchanged submissions
    # If players ABCD have all played each other and a new player E joins.
    # Only compute the new E matches to avoid unnecessary computation.
    # Also handle case when player submits new code invaliding old code.
    user_matches = list(combinations(users, 2))
    results, succeeded, start = {}, 0, time.time()
    for (player, scores) in chain.from_iterable(process_map(single_game, user_matches)):
        past_scores = results.get(player, (0, 0, 0))
        results[player] = tuple(map(add, scores, past_scores))
        succeeded += 1
    duration = int(time.time() - start)
    succeeded //= 2

    with db_cur() as cur:
        sql = 'INSERT INTO computation_history (duration, failed, computed, submissions) VALUES (%s, %s, %s, %s) RETURNING id'
        cur.execute(sql, (duration, len(user_matches) - succeeded, succeeded, total_submissions))
        computation_id = cur.fetchone()['id']

    with db_cur() as cur:
        sql = 'INSERT INTO results (username, computation_ID, wins, ties, loss, score) VALUES (%s, %s, %s, %s, %s, %s)'
        query_var_iter = ((username, computation_id, *scores, score(*scores)) for username, scores in results.items())
        execute_batch(cur, sql, query_var_iter)


if __name__ == '__main__':
    args = set( sys.argv[i].lower() for i in range(1, len(sys.argv)))
    is_forced = bool(args & { '-f', '--force' })

    if args & { '-n', '--now' }:
        tournament(force=is_forced)
        sys.exit()


    schedule = os.getenv('COMPUTE_SCHEDULE')
    log.info('Awaiting next scheduled computation window')
    while True:
        if pycron.is_now(schedule):
            log.info('Running')
            tournament(force=is_forced)
            time.sleep(60) # Wait 60 Seconds to Stop Trigger
        else:
            time.sleep(15)  # Check again in 15 seconds
