from itertools import product
from random import choice as random_choice
from abc import abstractmethod
import copy

class Color(object):
    RED = 'R'
    BLACK = 'B'
    BLANK = '-'

class GameException(Exception):
    pass


class ShadowGame(object):
    """A connect four game."""
    VALID_STATES = {}

    def __init__(self, grid):
        """Instances differ by their board."""
        self.grid = copy.deepcopy(grid)  # No aliasing!

        rows, cols = len(grid), len(grid[0])
        if (rows, cols) not in ShadowGame.VALID_STATES:
            valid_states = []
            for r, c in product(reversed(range(rows)), reversed(range(cols))):
                if c + 3 < cols: # Horizontal
                    valid_states.append(((r, c), (r, c + 1), (r, c + 2), (r, c + 3)))
                if r + 3 < rows: # Vertical
                    valid_states.append(((r, c), (r + 1, c), (r + 2, c), (r + 3, c)))
                if c + 3 < cols and r + 3 < rows: # Diagonal
                    valid_states.append(((r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)))
                if c - 3 > -1 and r + 3 < rows: # Diagonal
                    valid_states.append(((r, c), (r + 1, c - 1), (r + 2, c - 2), (r + 3, c - 3)))
            ShadowGame.VALID_STATES[(rows, cols)] = valid_states

    def possible_moves(self):
        """Return a list of possible moves given the current board."""
        top_row = self.grid[0]
        return [ i for i, x in enumerate(top_row) if x == Color.BLANK ]


    def neighbor(self, col, color):
        """Return a Game instance like this one but with a move made into the specified column."""
        if col <= -1 or col >= len(self.grid[0]):
            raise GameException(f'Invalid column index: {col}')
        if color != Color.RED and color != Color.BLACK:
            raise GameException(f'Invalid color: {color}')
        r, nxt_game = len(self.grid) // 2, ShadowGame(self.grid)
        if self.grid[r][col] == Color.BLANK:
            while r + 1 < len(self.grid) and nxt_game.grid[r + 1][col] == Color.BLANK:
                r += 1
        else:
            while r - 1 > -1 and nxt_game.grid[r][col] != Color.BLANK:
                r -= 1
        if nxt_game.grid[r][col] != Color.BLANK:
            raise GameException(f'Invalid Position - Col: {col}')
        nxt_game.grid[r][col] = color
        return nxt_game


    def winning_state(self):
        rows, cols, filled_spaces = len(self.grid), len(self.grid[0]), 0
        for (r0, c0), (r1, c1), (r2, c2), (r3, c3) in ShadowGame.VALID_STATES[(rows, cols)]:
            if self.grid[r0][c0] == Color.BLANK:
                continue
            if self.grid[r0][c0] == self.grid[r1][c1] == self.grid[r2][c2] == self.grid[r3][c3]:
                if self.grid[r0][c0] == Color.RED:
                    return float('inf')
                elif self.grid[r0][c0] == Color.BLACK:
                    return float('-inf')
                raise GameException(f'Invalid color: {self.grid[r0][c0]}')

        filled_spaces = sum(
            v != Color.BLANK
            for row in self.grid
            for v in row
        )
        return 0 if filled_spaces == cols * rows else None

class ShadowAgent(object):
    """Abstract class, extended by classes RandomAgent, FirstMoveAgent, MinimaxAgent.
    Do not make an instance of this class."""

    def __init__(self, color):
        """Agents use either RED or BLACK chips."""
        self.color = color

    @abstractmethod
    def move(self, game):
        """Abstract. Must be implemented by a class that extends Agent."""
        pass

class RandomShadowAgent(ShadowAgent):
    """Naive agent -- always performs a random move"""

    def move(self, game: ShadowGame):
        """Returns a random move"""
        return random_choice(game.possible_moves())

# Mask over MinimaxAgent & ShadowGame for use in benchmarking
MinimaxAgent = RandomShadowAgent
Game = ShadowGame