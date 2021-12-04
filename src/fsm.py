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
from flask_socketio import send, emit

class BoardFsm(StateMachine):

    """
    Finite State Machine Class
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
    moves_fen = None
    moves_fen_prev = None
    play_difficulty = 1  ### Default difficulty

    mode_setting = 0  ### Default mode setting 0: Human vs AI, 1: Human vs. Human
    mode_human_color = "white"  ### Default Human color
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
        difficulty_state.to(init_state)
        | setup_state.to(init_state)
        | human_move_state.to(init_state)
        | ai_move_state.to(init_state)
        | checkmate_state.to(init_state)
        | pawn_promotion_state.to(init_state)
        | undo_move_state.to(init_state)
        | mode_state.to(init_state)
    )
    go_to_mode_state = init_state.to(mode_state)
    go_to_human_color_state = mode_state.to(human_color_state)
    go_to_difficulty_state = human_color_state.to(difficulty_state) | mode_state.to(
        difficulty_state
    )
    go_to_setup_state = difficulty_state.to(setup_state)
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
    go_to_checkmate_state = human_move_state.to(checkmate_state) | ai_move_state.to(
        checkmate_state
    )
    go_to_pawn_promotion_state = human_move_state.to(
        pawn_promotion_state
    ) | ai_move_state.to(pawn_promotion_state)
    go_to_undo_move_state = human_move_state.to(undo_move_state) | ai_move_state.to(
        undo_move_state
    )


def run(_fsm: BoardFsm, _args: list(), _board: Board):

    while True:
        # Set flag if the state has changed
        _fsm.first_entry = _fsm.initial or (_fsm.curr_state != _fsm.current_state)
        
        _fsm.moves_fen_prev = _fsm.moves_fen
        _fsm.moves_fen = None

        if _fsm.first_entry:
            _fsm.prev_state = _fsm.curr_state
            _fsm.curr_state = _fsm.current_state

        if _fsm.is_init_state:

            """! @brief Init the chess board"""

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                _fsm.move_ai = ""  # Reset AI move instance
                _fsm.move_human = ""  # Reset Human move instance
                _fsm.moves = []  # Reset moves list
                _board.add_button_events()  # Add button events (delays the setup init)
                _board.startup_leds(0.05)  # Run the LEDs in a startup sequence

            _fsm.go_to_mode_state()  # Set next state

        elif _fsm.is_mode_state:

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                _fsm.mode_setting = 0  # Reset mode

                _board.set_leds("4")  # Set LED indicator

            if _fsm.mode_setting == 1:

                if GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(
                    cfg.MCB_BUT_WHITE
                ):

                    if _args.debug:
                        print(f"{cfg.MCB_DEBUG_MSG}human vs ai")
                    _fsm.mode_setting = 0  # Human vs AI
                    _board.set_leds("4")  # Set LED indicator

                elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                    _fsm.go_to_difficulty_state()  # Change state

            elif _fsm.mode_setting == 0:

                if GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(
                    cfg.MCB_BUT_WHITE
                ):

                    if _args.debug:
                        print(f"{cfg.MCB_DEBUG_MSG}human vs human")
                    _fsm.mode_setting = 1  # Human vs Human
                    _board.set_leds("5")  # Set LED indicator

                elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                    _fsm.go_to_human_color_state()  # Change state

        elif _fsm.is_human_color_state:

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")
                _fsm.mode_human_color = "white"  # Reset color
                _board.set_leds("1234")  # Set LED indicator to white

            if _fsm.mode_human_color == "white":

                if GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(
                    cfg.MCB_BUT_WHITE
                ):

                    _fsm.mode_human_color = "black"  # Human is black
                    _board.set_leds("5678")  # Set LED indicator to black
                    print(f"{cfg.MCB_DEBUG_MSG}human is black")

                elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                    _fsm.go_to_difficulty_state()  # Change state

            elif _fsm.mode_human_color == "black":

                if GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(
                    cfg.MCB_BUT_WHITE
                ):

                    _fsm.mode_human_color = "white"  # Human white
                    _board.set_leds("1234")  # Set LED indicator to white
                    print(f"{cfg.MCB_DEBUG_MSG}human is white")

                elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                    _fsm.go_to_difficulty_state()  # Change state

        elif _fsm.is_difficulty_state:

            """! @brief Set the difficulty of the AI"""

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                _board.set_difficulty_leds(
                    _fsm.play_difficulty
                )  # Set LEDs to default difficulty

            if GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}confirm ({_fsm.play_difficulty})")

                _board.set_leds("12345678abcdefgh")  # Turn on all LEDs

                if _fsm.play_difficulty == 0:  # Use level random mover on difficulty 0
                    if _args.debug:
                        print(f"{cfg.MCB_DEBUG_MSG}using Level: {_fsm.play_difficulty}")
                    cfg.ai_parameters.update({"UCI_LimitStrength": "false"})
                    cfg.ai_parameters.update({"Level": _fsm.play_difficulty})
                else:  # Use a ELO rating
                    if _args.debug:
                        print(
                            f"{cfg.MCB_DEBUG_MSG}using ELO rating: {_fsm.play_difficulty * 100 + 600}"
                        )
                    cfg.ai_parameters.update({"UCI_LimitStrength": "true"})
                    cfg.ai_parameters.update(
                        {"UCI_Elo": _fsm.play_difficulty * 100 + 600}
                    )  # 700 to 2800 (limit here is 1500, enough for me)

                # Initiate ai engine
                _fsm.ai = Stockfish(_args.input, parameters=cfg.ai_parameters)
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG} {_fsm.ai.get_parameters()}")

                # Init. eval engine
                _fsm.stockfish = Stockfish(
                "/home/pi/mChessBoard/src/stockfish-12_linux_x32_armv6",
                parameters=cfg.DEFAULT_STOCKFISH_PARAMS,
                )
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG} {_fsm.stockfish.get_parameters()}")

                _board.set_leds("")

                _fsm.go_to_setup_state()

            elif GPIO.event_detected(cfg.MCB_BUT_BLACK):

                # Increment difficulty
                if _fsm.play_difficulty < cfg.MCB_PLAY_MAX_DIFFICULTY:
                    _fsm.play_difficulty = _fsm.play_difficulty + 1
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}difficulty up: {_fsm.play_difficulty}")
                _board.set_difficulty_leds(_fsm.play_difficulty)

            elif GPIO.event_detected(cfg.MCB_BUT_WHITE):

                # Decrement difficulty
                if _fsm.play_difficulty > cfg.MCB_PLAY_DIFF_MIN:
                    _fsm.play_difficulty = _fsm.play_difficulty - 1
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}difficulty down: {_fsm.play_difficulty}")
                _board.set_difficulty_leds(_fsm.play_difficulty)

        elif _fsm.is_setup_state:

            """! @brief     Setting up the _board

            @info   Turn on LEDs for columns which is correctly setup
            """

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                _board.add_button_events()  # Add button int. events
                _board.add_field_events()  # Add field int. events
                _board.set_setup_leds()  # Turn on initial setup LEDs

            # React on field events
            if (
                GPIO.event_detected(cfg.MCB_ROW_AB_IO)
                or GPIO.event_detected(cfg.MCB_ROW_CD_IO)
                or GPIO.event_detected(cfg.MCB_ROW_EF_IO)
                or GPIO.event_detected(cfg.MCB_ROW_GH_IO)
            ):
                _board.set_setup_leds()

            # If board is setup correctly
            elif _board.board_current == _board.board_setup:

                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}_board is set up")

                _board.set_leds("abcdefgh12345678")  # Turn on all LEDs
                _board.board_prev = (
                    _board.board_current
                )  # Set previous board to current board
                _board.board_history = []  # Reset undo history
                _board.board_history.append(_board.board_current)
                time.sleep(1)  # Wait a sec
                _board.set_leds("")  # Turn off the LEDs

                _fsm.go_to_human_move_state()  # Change state

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):

                _fsm.go_to_difficulty_state()  # Change state

        elif _fsm.is_human_move_state:

            """! @brief     Handle Human moves

            @info   Indicate movements and get confirm signals if auto confirm is disabled.
            """

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                _board.add_field_events()  # Re-enable event from the fields
                _board.add_button_events()  # Re-enable event from the buttons
                _fsm.human_move_field_ = ""  # Reset human move field
                _fsm.toggle = True  # Reset toggle flag
                _fsm.timer = time.time()  # Start timer #TODO

            if (len(_fsm.move_human) == 4) and (
                time.time() > (_fsm.timer + cfg.MCB_PLAY_AI_LED_TOGGLE_TIME)
            ):

                _fsm.toggle = not _fsm.toggle  # Toggle, toggle flag
                _fsm.timer = time.time()  # Take a new timestamp
                _board.set_move_led(_fsm.toggle, _fsm.move_human)  # Toggle the move LEDs

            # Handle events on fields.
            if (
                GPIO.event_detected(cfg.MCB_ROW_AB_IO)
                or GPIO.event_detected(cfg.MCB_ROW_CD_IO)
                or GPIO.event_detected(cfg.MCB_ROW_EF_IO)
                or GPIO.event_detected(cfg.MCB_ROW_GH_IO)
            ):

                human_move_field = (
                    _board.get_field_event()
                )  # Get the specific field event (single field change)
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}event - field changed: {human_move_field}")

                # If first event and not an empty event
                if len(_fsm.move_human) == 0 and human_move_field != "":
                    _board.set_leds(human_move_field)  # Set the single field led
                    _fsm.move_human = human_move_field  # Setup first field in the move
                # Else if second event and not the same field
                elif (
                    len(_fsm.move_human) == 2
                    and human_move_field != ""
                    and human_move_field != _fsm.move_human
                ):

                    move_human_opposite = (
                        human_move_field + _fsm.move_human
                    )  # Save an opposite representation
                    _fsm.move_human += (
                        human_move_field  # Add the new field to the human move
                    )

                    # Check for incorrectness (also check for pawn promotion)
                    if not _fsm.stockfish.is_move_correct(
                        _fsm.move_human
                    ) and not _fsm.stockfish.is_move_correct(_fsm.move_human + "q"):
                        _fsm.move_human = ""
                        _board.set_leds("")
                    # Check for correctness opposite if fields are obtained in opposite direction (could be pawn promotion)
                    elif _fsm.stockfish.is_move_correct(
                        move_human_opposite
                    ) or _fsm.stockfish.is_move_correct(move_human_opposite + "q"):
                        _fsm.move_human = move_human_opposite

                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}human move: {_fsm.move_human}")

            # If black or white is pressed to confirm move, or auto_confirm is active
            elif (
                GPIO.event_detected(cfg.MCB_BUT_BLACK)
                or GPIO.event_detected(cfg.MCB_BUT_WHITE)
                or _args.auto_confirm
            ) and len(_fsm.move_human) == 4:

                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}event - confirm human move: {_fsm.move_human}")
                _board.read_fields()  # Read and update fields
                if _board.is_move_done(_fsm.move_human, _fsm.moves):
                    if _fsm.stockfish.is_move_correct(_fsm.move_human):
                        if _args.debug:
                            print(f"{cfg.MCB_DEBUG_MSG}stockfish - move correct")
                        _board.set_move_done_leds(_fsm.move_human)  # Set the field LEDs
                        _fsm.moves.append(_fsm.move_human)  # Add the move to the moves list
                        _fsm.stockfish.set_position(_fsm.moves)  # Set position in Stockfish
                        _fsm.moves_fen = _fsm.stockfish.get_fen_position() # Set the position in fen
                        _fsm.ai.set_position(_fsm.moves)  # Set position in AI
                        _fsm.move_human = ""  # Reset human move
                        if _args.debug:
                            _board.full_display(_fsm.stockfish.get_board_visual())
                        if _fsm.stockfish.get_evaluation() == {
                            "type": "mate",
                            "value": 0,
                        }:  # Evaluate if there is a checkmate
                            _fsm.go_to_checkmate()  # Change state
                        _board.board_history.append(
                            _board.board_current
                        )  # Add the current _board to the undo history list

                    # Check for pawn promotion
                    elif _fsm.stockfish.is_move_correct(_fsm.move_human + "q"):
                        _fsm.go_to_pawn_promotion()
                else:
                    if _args.debug:
                        _board.display()
                        print(f"{cfg.MCB_DEBUG_MSG}move not done")

            elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):
                print(f"{cfg.MCB_DEBUG_MSG}event - hint/ai move")
                _board.set_leds("")  # Turn off LEDs for indication
                _board.remove_field_events()
                _fsm.move_ai = _fsm.ai.get_best_move()
                _fsm.go_to_ai_move_state()

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}event - undo")
                if _args.debug:
                    _board.full_display(_fsm.stockfish.get_board_visual())
                _fsm.go_to_undo_move_state()

        elif _fsm.is_ai_move_state:

            """! @brief     Handle AI moves

            @info   Indicate movements and get confirm signals.
            """

            if _fsm.first_entry:
                print(f"STATE: {_fsm.current_state.identifier}")
                _board.add_field_events()  # Re-enable event from the fields
                _board.add_button_events()  # Re-enable event from the buttons
                _fsm.timer = time.time()
                _fsm.toggle = True

            # Handle the led flash indicator timing
            if time.time() > _fsm.timer + cfg.MCB_PLAY_AI_LED_TOGGLE_TIME:
                _fsm.toggle = not _fsm.toggle
                _board.set_move_led(_fsm.toggle, _fsm.move_ai)
                _fsm.timer = time.time()

            # Confirm AI/hint move
            if _args.auto_confirm:
                _board.read_fields()

            if (
                GPIO.event_detected(cfg.MCB_BUT_BLACK)
                or GPIO.event_detected(cfg.MCB_BUT_WHITE)
                or (_args.auto_confirm and _board.is_move_done(_fsm.move_ai, _fsm.moves))
            ):

                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}event - confirm ai move: {_fsm.move_ai}")
                if len(_fsm.move_ai) == 5:
                    _fsm.go_to_pawn_promotion_state()
                elif _board.is_move_done(_fsm.move_ai, _fsm.moves):
                    _board.board_prev = _board.board_current
                    if _fsm.stockfish.is_move_correct(_fsm.move_ai):
                        _board.set_move_done_leds(_fsm.move_ai)
                        _fsm.moves.append(_fsm.move_ai)
                        _fsm.stockfish.set_position(_fsm.moves)
                        _fsm.ai.set_position(_fsm.moves)
                        _fsm.move_ai = ""
                        if _args.debug:
                            _board.full_display(_fsm.stockfish.get_board_visual())
                        if _fsm.stockfish.get_evaluation() == {"type": "mate", "value": 0}:
                            _fsm.go_to_checkmate()
                        else:
                            _fsm.go_to_human_move_state()
                        _board.board_history.append(_board.board_current)
                else:
                    if _args.debug:
                        _board.display()

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}event - undo")
                if _args.debug:
                    _board.full_display(_fsm.stockfish.get_board_visual())
                _fsm.go_to_undo_move_state()

        elif _fsm.is_pawn_promotion_state:

            """! @brief     Handle undo moves.

            @info   Indicate movements and get confirm signals.
            """

            if _fsm.first_entry:
                print(f"STATE: {_fsm.current_state.identifier}")
                if _fsm.prev_state.value == "human_move_state":
                    if _args.debug:
                        print(f"{cfg.MCB_DEBUG_MSG}from human move state: {_fsm.move_human}")
                    _fsm.move_promotion = _fsm.move_human
                    move_human_flag = True
                    promotion_loop = 0
                elif _fsm.prev_state.value == "ai_move":
                    if _args.debug:
                        print(f"{cfg.MCB_DEBUG_MSG}from ai move state: {_fsm.move_ai}")
                    _fsm.move_promotion = _fsm.move_ai
                    move_human_flag = False
                    promotion_loop = -1
                else:
                    _fsm.go_to_human_move_state()  # Change state
                _fsm.timer = time.time()

            # Handle the led flash indicator timing
            if time.time() > _fsm.timer + cfg.MCB_PLAY_AI_LED_TOGGLE_TIME:
                _fsm.toggle = not _fsm.toggle
                _fsm.move_promotion = _board.set_promotion_menu_led(
                    _fsm.toggle, _fsm.move_promotion, promotion_loop
                )
                _fsm.timer = time.time()

            if GPIO.event_detected(cfg.MCB_BUT_BLACK) and move_human_flag:

                if promotion_loop < 3:
                    promotion_loop += 1  # Increment promotion
                else:
                    promotion_loop = 0
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}promotion : {promotion_loop}")

            elif GPIO.event_detected(cfg.MCB_BUT_WHITE) and move_human_flag:

                if promotion_loop > 0:
                    promotion_loop -= 1  # Decrement promotion
                else:
                    promotion_loop = 3
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}promotion : {promotion_loop}")

            elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}q: 0, b: 1, k:2, r:3")
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}choice: {promotion_loop}")

                _board.read_fields()  # Read and update fields
                if _board.is_move_done(_fsm.move_promotion[:4], _fsm.moves):
                    if _fsm.stockfish.is_move_correct(_fsm.move_promotion):
                        if _args.debug:
                            print(f"{cfg.MCB_DEBUG_MSG}stockfish - move correct")
                        _board.set_move_done_leds(
                            _fsm.move_promotion[:4]
                        )  # Set the field LEDs
                        _fsm.moves.append(
                            _fsm.move_promotion
                        )  # Add the move to the moves list
                        _fsm.stockfish.set_position(_fsm.moves)  # Set position in Stockfish
                        _fsm.ai.set_position(_fsm.moves)  # Set position in AI
                        _fsm.move_human = ""  # Reset human move
                        _fsm.move_ai = ""  # Reset ai move
                        if _args.debug:
                            _board.full_display(_fsm.stockfish.get_board_visual())
                        if _fsm.stockfish.get_evaluation() == {
                            "type": "mate",
                            "value": 0,
                        }:  # Evaluate if there is a checkmate
                            _fsm.go_to_checkmate()  # Change state
                        else:
                            _fsm.go_to_human_move_state()  # Change state
                        _board.board_history.append(
                            _board.board_current
                        )  # Add the current _board to the undo history list

                else:
                    if _args.debug:
                        _board.display()

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}event - undo")
                if _args.debug:
                    _board.full_display(_fsm.stockfish.get_board_visual())
                _fsm.go_to_undo_move_state()

        elif _fsm.is_undo_move_state:

            """! @brief     Handle undo moves.

            @info   Indicate movements and get confirm signals.
            """

            if _fsm.first_entry:
                print(f"STATE: {_fsm.current_state.identifier}")
                _fsm.timer = time.time()
                _fsm.toggle = True
                _fsm.move_human = ""
                _fsm.move_ai = ""
                _fsm.move_undo = ""

                # Check if any moves has been made
                if len(_fsm.moves) > 0:
                    if len(_fsm.moves[-1]) >= 4:
                        # Determine the mode to undo, and to indicate with LED flashing.
                        _fsm.move_undo = (
                            _fsm.moves[-1][2]
                            + _fsm.moves[-1][3]
                            + _fsm.moves[-1][0]
                            + _fsm.moves[-1][1]
                        )
                    else:
                        # Cancelling a non-finished move,
                        # just set LEDs and change state.
                        _board.set_move_done_leds(_fsm.moves[-1])
                        _fsm.go_to_human_move_state()
                else:
                    # Cancelling unfinished first move,
                    # just turn off LEDs and change state.
                    _board.set_leds("")
                    _fsm.go_to_human_move_state()

            # Handle the led flash indicator timing
            if (time.time() > _fsm.timer + cfg.MCB_PLAY_AI_LED_TOGGLE_TIME) and (
                len(_fsm.move_undo) == 4
            ):
                _fsm.toggle = not _fsm.toggle
                _board.set_move_led(_fsm.toggle, _fsm.move_undo)
                _fsm.timer = time.time()

            # Confirm Undo move
            if GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(
                cfg.MCB_BUT_WHITE
            ):
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}confirm undo move: {_fsm.move_undo}")
                if _board.is_undo_move_done():  # If the undo move is done
                    del _fsm.moves[-1]  # Delete last move for the engines
                    _fsm.stockfish.set_position(_fsm.moves)  # Set the moved for eval engine
                    _fsm.ai.set_position(_fsm.moves)  # Set the moved for ai engine
                    if len(_fsm.moves) > 0:  # Check if the deleted move was the last one.
                        _board.set_move_done_leds(_fsm.moves[-1])
                    else:
                        _board.set_leds("")
                    if _args.debug:
                        _board.full_display(_fsm.stockfish.get_board_visual())
                    _fsm.go_to_human_move_state()  # Change state
                else:
                    if _args.debug:
                        _board.display()

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):
                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}event - cancel undo")
                _board.set_move_done_leds(_fsm.moves[-1])
                _fsm.go_to_human_move_state()

        # STATE: Checkmate
        elif _fsm.is_checkmate:

            """! @brief     Handle checkmate.

            @info   Flash the LEDs for indication and go to init when button is pressed.
            """

            if _fsm.first_entry:
                print(f"STATE: {_fsm.current_state.identifier}")
                _fsm.timer = time.time()
                _fsm.toggle = True

            if time.time() > _fsm.timer + cfg.MCB_PLAY_CHECKMATE_LED_TOGGLE_TIME:
                if _fsm.toggle:
                    _board.set_leds("12345678abcdefgh")
                    _fsm.toggle = False
                else:
                    _board.set_leds("")
                    _fsm.toggle = True
                _fsm.timer = time.time()

            if (
                GPIO.event_detected(cfg.MCB_BUT_WHITE)
                or GPIO.event_detected(cfg.MCB_BUT_BLACK)
                or GPIO.event_detected(cfg.MCB_BUT_CONFIRM)
                or GPIO.event_detected(cfg.MCB_BUT_BACK)
            ):

                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}go to init")
                _board.remove_button_events()
                _board.remove_field_events()
                _fsm.go_to_init_state()

        # Reset (all buttons pressed)
        if (
            not GPIO.input(cfg.MCB_BUT_WHITE)
            and not GPIO.input(cfg.MCB_BUT_BLACK)
            and not GPIO.input(cfg.MCB_BUT_CONFIRM)
            and not GPIO.input(cfg.MCB_BUT_BACK)
        ):

            if _args.debug:
                print(f"{cfg.MCB_DEBUG_MSG}resetting")
            _board.set_leds("abcdefgh12345678")
            _board.remove_button_events()
            _board.remove_field_events()
            time.sleep(2)
            _fsm.go_to_init_state()

        # Not initial anymore
        _fsm.initial = False

        if _fsm.moves_fen != _fsm.moves_fen_prev:
            return _fsm.moves_fen