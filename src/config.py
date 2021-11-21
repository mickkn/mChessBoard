"""
    This module contain mchessboard configurations.

    :author: Mick Kirkegaard.
"""

class Config():

    def __init__(self):

    
        """! @brief     Play defines """
        self.MCB_PLAY_DIFF_MAX = 8
        self.MCB_PLAY_DIFF_MIN = 0
        self.MCB_PLAY_AI_LED_TOGGLE_TIME = 0.5  # sec
        self.MCB_PLAY_CHECKMATE_LED_TOGGLE_TIME = 0.2  # sec

        """! @brief     Board defines """
        self.MCB_I2C_PORT_NUM = 1
        self.MCB_I2C_ROW_AB_ADDRESS = 0x23
        self.MCB_I2C_ROW_CD_ADDRESS = 0x22
        self.MCB_I2C_ROW_EF_ADDRESS = 0x21
        self.MCB_I2C_ROW_GH_ADDRESS = 0x20
        self.MCB_I2C_LEDS_ADDRESS = 0x24

        self.MCB_BUT_WHITE = 17  # Closest to WHITE side
        self.MCB_BUT_CONFIRM = 27  # Middle close to WHITE side
        self.MCB_BUT_BACK = 23  # Middle close to BLACK side
        self.MCB_BUT_BLACK = 22  # Closest to BLACK side
        self. MCB_BUT_DEBOUNCE = 200  # Button debounce
        self.MCB_FIELD_DEBOUNCE = 50  # Field debounce

        self.MCB_ROW_AB_IO = 6
        self.MCB_ROW_CD_IO = 13
        self.MCB_ROW_EF_IO = 19
        self.MCB_ROW_GH_IO = 26

        """! @brief     Stockfish default parameters """
        self.DEFAULT_STOCKFISH_PARAMS = {
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
        self.debug_msg = "    debug: "

        # Evaluation Engine Setup
        self.stockfish = None
        self.stockfish_param = {
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
        }

        # AI Engine setup
        self.ai = None
        self.ai_parameters = {
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
        }