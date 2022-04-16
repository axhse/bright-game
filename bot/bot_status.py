
class BotStatus:
    def __init__(self, is_paused: bool = None, active_game_count: int = None, log_count: int = None):
        self.is_paused = is_paused
        self.active_game_count = active_game_count
        self.log_count = log_count
