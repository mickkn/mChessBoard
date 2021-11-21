"""
    This module contain mchessboard configurations.

    :author: Mick Kirkegaard.
"""

class Config():

    def __init__(self):

        """! @brief     Stockfish default parameters """
        print("Config")

DEFAULT_STOCKFISH_PARAMS = {
    "Write Debug Log": "false",
    "Contempt": 0,
    "Min Split Depth": 0,
    "Threads": 1,
    "Ponder": "false",
    "Hash": 16,
    "MultiPV": 1,
    "Skill Level": 20,
    "Move Overhead": 30,
    "Minimum Thinking Time": 20,
    "Slow Mover": 80,
    "UCI_Chess960": "false",
    'UCI_LimitStrength': 'false',
}


"""! @brief     Global variables """
debug_msg = "    debug: "