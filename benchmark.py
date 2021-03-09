from game_base import ShadowGame, Color, RandomShadowAgent
import game

def single_game():
    """Create a game and have two agents play it."""
    grid = [['-' for _ in range(8)] for _ in range(8)]
    g, sg = game.Game(grid), ShadowGame(grid)
    player, shadow_player = game.MinimaxAgent(Color.RED), RandomShadowAgent(Color.BLACK)
    cur_player = player
    while True:
        mv = cur_player.move(g)
        g, sg = g.neighbor(mv, cur_player.color), sg.neighbor(mv, cur_player.color)
        if sg.winning_state() is not None:
            break
        cur_player = shadow_player if cur_player == player else player

    return sg

def tournament(simulations=1000):
    r_win, b_win, tie = 0, 0, 0
    for i in range(simulations):
        g = single_game()
        if g.winning_state() == float('inf'):
            r_win += 1
        elif g.winning_state() == float('-inf'):
            b_win += 1
        elif g.winning_state() == 0:
            tie += 1

    return r_win,tie,b_win

if __name__ == '__main__':
    import sys
    sims = 50
    if len(sys.argv) > 2:
        sims = int(sys.argv[1])
    print('\n' + ','.join(map(str, tournament(simulations=sims))), end='')

