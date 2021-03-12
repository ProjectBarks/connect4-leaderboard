# Connect 4 Leaderboard

A simple connect four leaderboard that runs the benchmarks in a dockerized container for security and standardization.

## Screenshot
![Screenshot](./resources/screenshot.png)

## Setup & Running
### Installation
1. Install docker for your specific system
1. Install postgres
1. Update `.env` with relevant changes.
1. Pull the relevant docker image intended or use the same image listed in `.env`
1. Activate and create a virtual environment
1. Install requiurements `pip install -r requirements.txt`

### Execution
1. Running the server: `./run-server.sh`
1. Running the tournament cron job `./run-tournament.sh`

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