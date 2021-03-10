from base_game import ShadowGame, Color


def single_game(P1Game, P1Agent, P2Game, P2Agent):
    # Create base grid and initialize the game agent for both players
    grid = [['-' for _ in range(8)] for _ in range(8)]
    p1_g, p2_g, sg = P1Game(grid), P2Game(grid), ShadowGame(grid)
    p1, p2 = P1Agent(Color.RED), P2Agent(Color.BLACK)
    cur_player, cur_game, cur_color = p1, p1_g, Color.RED
    while True:
        mv = cur_player.move(cur_game)
        sg, p1_g, p2_g = sg.neighbor(mv, cur_color), p1_g.neighbor(mv, cur_color), p2_g.neighbor(mv, cur_color)
        if sg.winning_state() is not None:
            break
        cur_player, cur_game, cur_color = (p2, p2_g, Color.BLACK) if cur_player == p1 else (p1, p1_g, Color.RED)
    print(sg.winning_state())
    return sg


def tournament(P1Game, P1Agent, P2Game, P2Agent, simulations=50, rotate_first_move=False):
    r_win, b_win, tie = 0, 0, 0
    player_groups = [(P1Game, P1Agent), (P2Game, P2Agent)]
    import inspect
    print(inspect.getsource(P1Agent))
    print(inspect.getsource(P2Agent))

    for i in range(simulations):
        p1_i, p2_i = (i % 2, (i + 1) % 2) if rotate_first_move else (0, 1)
        g = single_game(*player_groups[p1_i], *player_groups[p2_i])
        if g.winning_state() == float('inf'):
            if p1_i == 0: r_win += 1
            else: b_win += 1
        elif g.winning_state() == float('-inf'):
            if p1_i == 0: b_win += 1
            else: r_win += 1
        elif g.winning_state() == 0:
            tie += 1
    return r_win, tie, b_win


if __name__ == '__main__':
    import sys, player1, player2

    if len(sys.argv) < 3:
        raise Exception('Too few arguments! Syntax benchmark.py [simulations] [rotate_first_move]')

    sims = int(sys.argv[1])
    is_rotate_first_move = sys.argv[2] in ('yes', 'true', 't', '1')
    results = tournament(
        player1.Game, player1.MinimaxAgent,
        player2.Game, player2.MinimaxAgent,
        simulations=sims, rotate_first_move=is_rotate_first_move
    )
    print('\n' + ','.join(map(str, results)), end='')
