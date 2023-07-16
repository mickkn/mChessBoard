"""
  :File:        config.py

  :Details:     Package that contains a configuration class for a flask app which
                uses configuration variables defined in the environment file .env.

  :Copyright:   Copyright (c) 2023 Mick Kirkegaard. All rights reserved.

  :Date:        28-05-2023
  :Author:      Mick Kirkegaard, Circle Consult ApS.
"""

import os

class Config(object):

    #: Key used for encryption, has to be set to access the session dictionary.
    SECRET_KEY = os.environ.get("SECRET_KEY") or "topsecretshit"

    #: Cookie session name to distinguish between sites on same host.
    SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME") or "session"

    # Play settings.
    MCB_PLAY_MAX_DIFFICULTY = os.environ.get("MCB_PLAY_MAX_DIFFICULTY") or 8
    MCB_PLAY_DIFF_MIN = os.environ.get("MCB_PLAY_DIFF_MIN") or 0
    MCB_PLAY_AI_LED_TOGGLE_TIME = os.environ.get("MCB_PLAY_AI_LED_TOGGLE_TIME") or 0.5  # sec
    MCB_PLAY_CHECKMATE_LED_TOGGLE_TIME = os.environ.get("MCB_PLAY_CHECKMATE_LED_TOGGLE_TIME") or 0.2  # sec

    # Board settings.
    MCB_I2C_PORT_NUM = os.environ.get("MCB_I2C_PORT_NUM") or 1
    MCB_I2C_ROW_AB_ADDRESS = os.environ.get("MCB_I2C_ROW_AB_ADDRESS") or 0x23
    MCB_I2C_ROW_CD_ADDRESS = os.environ.get("MCB_I2C_ROW_CD_ADDRESS") or 0x22
    MCB_I2C_ROW_EF_ADDRESS = os.environ.get("MCB_I2C_ROW_EF_ADDRESS") or 0x21
    MCB_I2C_ROW_GH_ADDRESS = os.environ.get("MCB_I2C_ROW_GH_ADDRESS") or 0x20
    MCB_I2C_LEDS_ADDRESS = os.environ.get("MCB_I2C_LEDS_ADDRESS") or 0x24

    MCB_BUT_WHITE = os.environ.get("MCB_BUT_WHITE") or 17  # Closest to WHITE side
    MCB_BUT_CONFIRM = os.environ.get("MCB_BUT_CONFIRM") or 27  # Middle close to WHITE side
    MCB_BUT_BACK = os.environ.get("MCB_BUT_BACK") or 23  # Middle close to BLACK side
    MCB_BUT_BLACK = os.environ.get("MCB_BUT_BLACK") or 22  # Closest to BLACK side
    MCB_BUT_DEBOUNCE = os.environ.get("MCB_BUT_DEBOUNCE") or 200  # Button debounce
    MCB_ALL_BUT = os.environ.get("MCB_ALL_BUT") or [MCB_BUT_WHITE, MCB_BUT_CONFIRM, MCB_BUT_BACK, MCB_BUT_BLACK]

    MCB_ROW_AB_IO = os.environ.get("MCB_ROW_AB_IO") or 6
    MCB_ROW_CD_IO = os.environ.get("MCB_ROW_CD_IO") or 13
    MCB_ROW_EF_IO = os.environ.get("MCB_ROW_EF_IO") or 19
    MCB_ROW_GH_IO = os.environ.get("MCB_ROW_GH_IO") or 26
    MCB_ALL_FIELDS = os.environ.get("MCB_ALL_FIELDS") or [MCB_ROW_AB_IO, MCB_ROW_CD_IO, MCB_ROW_EF_IO, MCB_ROW_GH_IO]
    MCB_FIELD_DEBOUNCE = os.environ.get("MCB_FIELD_DEBOUNCE") or 50  # Field debounce

    # Stockfish default parameters.
    DEFAULT_STOCKFISH_PARAMS = os.environ.get("DEFAULT_STOCKFISH_PARAMS") or {
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
