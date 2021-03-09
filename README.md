# Connect 4 Leaderboard

A simple connect four leaderboard that runs the benchmarks in a dockerized container for security and standardization.

## Screenshot
![Screenshot](./resources/screenshot.png)

## Base Code
```python
class Game(object):
    pass


class MinimaxAgent(object):
    """Smart agent -- uses minimax to determine the best move"""
    
    def __init__(self, color: str):
        """Agents use either RED (R) or BLACK (B) chips."""
        pass

    def move(self, game: Game) -> Game:
        """Returns the best move using minimax as a new game instance"""
        # YOU FILL THIS IN
        pass

```

## License 
[MIT License](./LICENSE)