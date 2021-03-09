from abc import abstractmethod

class Game(object):
    @abstractmethod
    def __init__(self, grid):
        pass

    @abstractmethod
    def possible_moves(self):
        pass

    @abstractmethod
    def neighbor(self, col, color):
        pass

    @abstractmethod
    def winning_state(self):
        pass

class Agent(object):
    @abstractmethod
    def __init__(self, color):
        self.color = color
        pass

    @abstractmethod
    def move(self, game):
        """Abstract. Must be implemented by a class that extends Agent."""
        pass

class MinimaxAgent(Agent):
    @abstractmethod
    def move(self, game):
        pass

