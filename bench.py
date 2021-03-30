import os
from contextlib import contextmanager

import epicbox
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

log = logging.getLogger(__name__)

def load_file(file_name):
    root = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(root, file_name), 'r') as t:
        return '\n'.join(t.readlines())


def run_benchmark(player1_code, player2_code, executions, max_execution_millis=None, rotate_first_move=False, base_files=None):
    if not base_files: base_files = ['benchmark.py', 'base_game.py']
    memory_mb = int(os.getenv('CONTAINER_MEMORY_MB'))
    container_img = os.getenv('CONTAINER_IMAGE')

    epicbox.configure( profiles=[ epicbox.Profile('python', container_img) ] )

    limits = {
        'cputime': (executions * max_execution_millis) // 1000,
        'realtime': (executions * max_execution_millis) // 1000,
        'memory': memory_mb
    }
    files = [
        { 'name': 'player1.py', 'content': player1_code },
        { 'name': 'player2.py', 'content': player2_code }
    ] + [ { 'name': x, 'content': load_file(x).encode() } for x in base_files ]

    stats = epicbox.run(
        'python', f'python3 benchmark.py {executions} {rotate_first_move}',
        files=files,
        limits=limits
    )

    stats['success'] = stats['exit_code'] == 0 and not stats['timeout']
    if stats['success']:
        raw_results = stats['stdout'].decode().split('\n')[-1].split(',')
        if len(raw_results) < 3:
            stats['success'] = False
            return stats
        wins, ties, loss = map(int, raw_results)
        stats['wins'] = wins
        stats['ties'] = ties
        stats['loss'] = loss
    else:
        log.error(stats['stdout'].decode())

    return stats


@contextmanager
def db_cur():
    with psycopg2.connect(database=os.getenv('DATABASE_NAME'),
                          user=os.getenv('DATABASE_USER'),
                          password=os.getenv('DATABASE_PASSWORD'),
                          host=os.getenv('DATABASE_HOST'),
                          port=os.getenv('DATABASE_PORT'),
                          cursor_factory=RealDictCursor) as conn:
        with conn.cursor() as curs:
            yield curs

