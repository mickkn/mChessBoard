"""
    This module implements mchessboard finite state machine.

    :author: Mick Kirkegaard.
"""

from statemachine import StateMachine, State

from board import Board
from stockfish import (
    Stockfish,
)  # https://pypi.org/project/stockfish/ edited to fit for Minic
import time
import config as cfg
import RPi.GPIO as GPIO
import socketio


class BoardFsm(StateMachine):

    """Finite State Machine Class
    
    """

    # Flags & Variables
    initial = True
    first_entry = True
    prev_state = None
    curr_state = None
    toggle = None

    # Movement global variables and flags
    move_ai = ""  ### Move made by AI Engine
    move_human = ""  ### Move made by Human
    move_undo = ""  ### Move made by Undo
    move_promotion = ""  ### Move made by Promotion
    moves = []  ### List of moves for engine
    play_difficulty = 1  ### Default difficulty

    human_vs_ai = True  ### Default mode setting 0: Human vs AI, 1: Human vs. Human
    human_is_white = True
    timer = None

    # Initialize the states
    init_state = State("Init", initial=True)
    mode_state = State("Mode")
    human_color_state = State("Color")
    difficulty_state = State("Difficulty")
    setup_state = State("Setup")
    human_move_state = State("HumanMove")
    ai_move_state = State("AIMove")
    checkmate_state = State("Checkmate")
    pawn_promotion_state = State("PawnPromotion")
    undo_move_state = State("Undo")

    # Initialize all transitions allowed
    go_to_init_state = (
        mode_state.to(init_state)
        | human_color_state.to(init_state)
        | difficulty_state.to(init_state)
        | setup_state.to(init_state)
        | ai_move_state.to(init_state)
        | human_move_state.to(init_state)
        | checkmate_state.to(init_state)
        | pawn_promotion_state.to(init_state)
        | undo_move_state.to(init_state)
    )
    go_to_mode_state = (
        init_state.to(mode_state)
        | human_color_state.to(mode_state)
    )
    go_to_human_color_state = (
        mode_state.to(human_color_state)
        | difficulty_state.to(human_color_state)
    )
    go_to_difficulty_state = (
        human_color_state.to(difficulty_state) 
    )
    go_to_setup_state = (
        difficulty_state.to(setup_state)
        | mode_state.to(setup_state)
    )
    go_to_ai_move_state = (
        setup_state.to(ai_move_state)
        | human_move_state.to(ai_move_state)
        | pawn_promotion_state.to(ai_move_state)
    )
    go_to_human_move_state = (
        setup_state.to(human_move_state)
        | ai_move_state.to(human_move_state)
        | undo_move_state.to(human_move_state)
        | pawn_promotion_state.to(human_move_state)
    )
    go_to_checkmate_state = (
        human_move_state.to(checkmate_state) 
        | ai_move_state.to(checkmate_state)
    )
    go_to_pawn_promotion_state = (
        human_move_state.to(pawn_promotion_state) 
        | ai_move_state.to(pawn_promotion_state)
    )
    go_to_undo_move_state = (
        human_move_state.to(undo_move_state) 
        | ai_move_state.to(undo_move_state)
    )

    ai_parameters = cfg.DEFAULT_STOCKFISH_PARAMS

    engine = None
    engine_eval = None  # Needed because Minic can't evaluate
    sio = socketio.Client(logger=True, engineio_logger=True)