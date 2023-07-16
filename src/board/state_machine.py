"""
    This module implements mchessboard finite state machine.

    :author: Mick Kirkegaard.
"""

from board.board import Board
from web.application.libs.stockfish import (
    Stockfish,
)  # https://pypi.org/project/stockfish/ edited to fit for Minic
import time
from web.application import config as cfg
import RPi.GPIO as GPIO
import state_machine_impl


def debug_msg(enabled: bool, msg: str) -> None:

    """Debug message handler

        Function to make the FSM less messy

    Args
        enabled: Print if true
        msg: Message to display
    """

    if enabled:
        print(f"    debug: {msg}")


def run(_fsm: state_machine_impl.BoardFsm, _args: list(), _board: Board):

    while True:

        # Set first entry flag if the state has changed
        _fsm.first_entry = _fsm.initial or (_fsm.curr_state != _fsm.current_state)

        # Set prev state to current state and local
        # current state to real current state
        if _fsm.first_entry:
            _fsm.prev_state = _fsm.curr_state
            _fsm.curr_state = _fsm.current_state

        if _fsm.is_init_state:

            """INIT STATE
            Initialise engines and reset varibles
            """

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                # Init. AI and EVAL engine
                debug_msg(_args.debug, "setting up engines")
                if _fsm.engine is None:
                    _fsm.engine = Stockfish(_args.input)
                debug_msg(_args.debug, f"{_fsm.engine.get_parameters()}")
                if _fsm.engine_eval is None:
                    _fsm.engine_eval = Stockfish(
                        "/home/pi/mChessBoard/src/stockfish-12_linux_x32_armv6"
                    )
                debug_msg(_args.debug, f"{_fsm.engine_eval.get_parameters()}")
                # Reset AI move instance
                _fsm.move_ai = ""
                # Reset Human move instance
                _fsm.move_human = ""
                # Reset moves list
                _fsm.moves = []
                # Reset all event handlers (more like reset)
                _board.remove_button_events()
                _board.remove_field_events()
                time.sleep(1)
                _board.add_button_events()
                _board.add_field_events()
                # Disconnect possible sockets, so it can connect later
                _fsm.sio.disconnect()
                # Run the LEDs in a startup sequence
                _board.startup_leds(0.05)

            # Set next state, to mode selection
            _fsm.go_to_mode_state()

        elif _fsm.is_mode_state:

            """MODE STATE
            Let the user chose either
            AI vs Human or
            Human vs Human
            """
                
            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                # Set LED indicator
                _board.set_leds("4")
                # Set defaault mode that fit with led '4'
                _fsm.human_vs_ai = True

            if _fsm.human_vs_ai:

                if GPIO.event_detected(cfg.MCB_BUT_BLACK) \
                    or GPIO.event_detected(cfg.MCB_BUT_WHITE):

                    debug_msg(_args.debug, "human vs human")
                    # Human vs AI
                    _fsm.human_vs_ai = False
                    # Set LED indicator
                    _board.set_leds("5")

                elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                    # Change state
                    _fsm.go_to_human_color_state()

            else:

                if GPIO.event_detected(cfg.MCB_BUT_BLACK) \
                    or GPIO.event_detected(cfg.MCB_BUT_WHITE):

                    debug_msg(_args.debug, "human vs ai")
                    # Human vs Human
                    _fsm.human_vs_ai = True
                    # Set LED indicator
                    _board.set_leds("4")

                elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                    # Change state
                    _fsm.go_to_setup_state()

        elif _fsm.is_human_color_state:

            """HUMAN COLOR STATE
            Pick side on AI vs Human
            """

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                # Reset color
                _fsm.human_is_white = True
                # Set LED indicator to white
                _board.set_leds("12")

            if _fsm.human_is_white:

                if GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(
                    cfg.MCB_BUT_WHITE
                ):

                    # Change human to black
                    _fsm.human_is_white = False 
                    # Set LED indicator to black
                    _board.set_leds("78")
                    debug_msg(_args.debug, "human is black")

                elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                    # Change state
                    _fsm.go_to_difficulty_state()  

            elif not _fsm.human_is_white:

                if GPIO.event_detected(cfg.MCB_BUT_BLACK) \
                    or GPIO.event_detected(cfg.MCB_BUT_WHITE):

                    # Change human to white
                    _fsm.human_is_white = True
                    # Set LED indicator to white 
                    _board.set_leds("12")
                    debug_msg(_args.debug, "human is white")

                elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                    # Change state
                    _fsm.go_to_difficulty_state()  

            if GPIO.event_detected(cfg.MCB_BUT_BACK):

                # Change state
                _fsm.go_to_mode_state()

        elif _fsm.is_difficulty_state:

            """DIFFICULTY STATE
            Set the difficulty of the AI
            """

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                # Set LEDs to default difficulty
                _board.set_difficulty_leds(_fsm.play_difficulty)  

            if GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                debug_msg(_args.debug, "confirm ({_fsm.play_difficulty})")

                # Turn on all LEDs
                _board.set_leds("12345678abcdefgh")
                # Wait a sec  
                time.sleep(1)  

                # Use level random mover on difficulty 0
                if _fsm.play_difficulty == 0:  
                    debug_msg(_args.debug, f"using Level: {_fsm.play_difficulty}")
                    _fsm.engine.set_skill_level(0)
                else:  # Use a ELO rating
                    debug_msg(_args.debug, f"using ELO rating: {_fsm.play_difficulty * 100 + 600}")
                    _fsm.engine.set_elo_rating(_fsm.play_difficulty * 100 + 600)

                debug_msg(_args.debug, f"{_fsm.engine.get_parameters()}")

                # Turn off LEDs
                _board.set_leds("")

                # Change state
                _fsm.go_to_setup_state()

            elif GPIO.event_detected(cfg.MCB_BUT_BLACK):

                # Increment difficulty
                if _fsm.play_difficulty < cfg.MCB_PLAY_MAX_DIFFICULTY:
                    _fsm.play_difficulty = _fsm.play_difficulty + 1
                
                debug_msg(_args.debug, f"difficulty up: {_fsm.play_difficulty}")
                
                # Set LEDs
                _board.set_difficulty_leds(_fsm.play_difficulty)

            elif GPIO.event_detected(cfg.MCB_BUT_WHITE):

                # Decrement difficulty
                if _fsm.play_difficulty > cfg.MCB_PLAY_DIFF_MIN:
                    _fsm.play_difficulty = _fsm.play_difficulty - 1
                
                debug_msg(_args.debug, f"difficulty down: {_fsm.play_difficulty}")
                
                # Set LEDs
                _board.set_difficulty_leds(_fsm.play_difficulty)

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):

                # Change state
                _fsm.go_to_human_color_state()

        elif _fsm.is_setup_state:

            """SETUP STATE
            Turn on LEDs for columns which is correctly setup
            """

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                # Turn on initial setup LEDs
                _board.set_setup_leds()

            # React on field events
            if (
                GPIO.event_detected(cfg.MCB_ROW_AB_IO)
                or GPIO.event_detected(cfg.MCB_ROW_CD_IO)
                or GPIO.event_detected(cfg.MCB_ROW_EF_IO)
                or GPIO.event_detected(cfg.MCB_ROW_GH_IO)
            ):
                # Update setup LEDs
                _board.set_setup_leds()

            # If board is setup correctly
            elif _board.board_current == _board.board_setup:

                debug_msg(_args.debug, "board is set up")

                # Turn on all LEDs
                _board.set_leds("abcdefgh12345678")
                # Set previous board to current board
                _board.board_prev = (_board.board_current)
                # Reset undo history 
                _board.board_history = []  
                _board.board_history.append(_board.board_current)
                # Wait a sec
                time.sleep(1)
                # Turn off the LEDs
                _board.set_leds("")
                
                try:
                    # Connect to webserver if it is running
                    _fsm.sio.connect("http://localhost", wait_timeout=10)
                    # Emit stat position to webserver
                    _fsm.sio.emit(
                        "move_event", {"data": str(_fsm.engine_eval.get_fen_position())}
                    )
                except:
                    print("Connection failed")
                
                # Change state
                _fsm.go_to_human_move_state()  

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):

                # Change state
                if _fsm.human_vs_ai:
                    _fsm.go_to_difficulty_state()
                else:
                    _fsm.go_to_mode_state()

        elif _fsm.is_human_move_state:

            """HUMAN MOVE STATE
            Indicate movements and get confirm signals 
            if auto confirm is disabled.
            """

            if _fsm.first_entry:

                print(f"STATE: {_fsm.current_state.identifier}")

                # Reset human move field
                _fsm.human_move_field_ = ""
                # Reset toggle flag
                _fsm.toggle = True  
                # Start timer #TODO
                _fsm.timer = time.time()  

            if (len(_fsm.move_human) == 4) and (
                time.time() > (_fsm.timer + cfg.MCB_PLAY_AI_LED_TOGGLE_TIME)
            ):
                
                # Toggle, toggle flag
                _fsm.toggle = not _fsm.toggle  
                # Take a new timestamp
                _fsm.timer = time.time()  
                # Toggle the move LEDs
                _board.set_move_led(_fsm.toggle, _fsm.move_human)  

            # Handle events on fields.
            if (
                GPIO.event_detected(cfg.MCB_ROW_AB_IO)
                or GPIO.event_detected(cfg.MCB_ROW_CD_IO)
                or GPIO.event_detected(cfg.MCB_ROW_EF_IO)
                or GPIO.event_detected(cfg.MCB_ROW_GH_IO)
            ):

                # Get the specific field event (single field change)
                human_move_field = _board.get_field_event()
                debug_msg(_args.debug, f"event - field changed: {human_move_field}")

                # If first event and not an empty event
                if len(_fsm.move_human) == 0 and human_move_field != "":
                    # Set the single field led
                    _board.set_leds(human_move_field)
                    # Setup first field in the move
                    _fsm.move_human = human_move_field  
                # Else if second event and not the same field
                elif (
                    len(_fsm.move_human) == 2
                    and human_move_field != ""
                    and human_move_field != _fsm.move_human
                ):

                    # Save an opposite representation
                    move_human_opposite = human_move_field + _fsm.move_human
                    # Add the new field to the human move
                    _fsm.move_human += human_move_field

                    # Check for incorrectness (also check for pawn promotion)
                    if not _fsm.engine_eval.is_move_correct(
                        _fsm.move_human
                    ) and not _fsm.engine_eval.is_move_correct(_fsm.move_human + "q"):
                        _fsm.move_human = ""
                        _board.set_leds("")
                    # Check for correctness opposite if fields are obtained in opposite direction (could be pawn promotion)
                    elif _fsm.engine_eval.is_move_correct(
                        move_human_opposite
                    ) or _fsm.engine_eval.is_move_correct(move_human_opposite + "q"):
                        _fsm.move_human = move_human_opposite

                debug_msg(_args.debug, f"human move: {_fsm.move_human}")

            # If black or white is pressed to confirm move, or auto_confirm is active
            elif (
                GPIO.event_detected(cfg.MCB_BUT_BLACK)
                or GPIO.event_detected(cfg.MCB_BUT_WHITE)
                or _args.auto_confirm
            ) and len(_fsm.move_human) == 4:

                debug_msg(_args.debug, f"event - confirm human move: {_fsm.move_human}")
                # Read and update fields
                _board.read_fields()  
                if _board.is_move_done(_fsm.move_human, _fsm.moves):
                    if _fsm.engine_eval.is_move_correct(_fsm.move_human):
                        debug_msg(_args.debug, f"stockfish - move correct")
                        _board.set_move_done_leds(_fsm.move_human)  # Set the field LEDs
                        _fsm.moves.append(
                            _fsm.move_human
                        )  # Add the move to the moves list
                        # Set position in AI
                        _fsm.engine.set_position(_fsm.moves)  
                        # Set position in Eval
                        _fsm.engine_eval.set_position(_fsm.moves) 
                        try:
                            _fsm.sio.emit(
                                "move_event",
                                {"data": str(_fsm.engine_eval.get_fen_position())},
                            )
                        except:
                            print("Emitting failed")
                         
                        _fsm.move_human = ""  # Reset human move
                        if _args.debug:
                            _board.full_display(_fsm.engine_eval.get_board_visual())
                        if _fsm.engine_eval.get_evaluation() == {
                            "type": "mate",
                            "value": 0,
                        }:  # Evaluate if there is a checkmate
                            _fsm.go_to_checkmate_state()  # Change state

                        # Add the current _board to the undo history list
                        _board.board_history.append(_board.board_current)
                        # If game mode is human vs AI, automatic move to AI turn
                        print(_fsm.human_vs_ai)
                        if _fsm.human_vs_ai:
                            debug_msg(_args.debug, "auto - ai move")
                            # Turn off LEDs for indication
                            _board.set_leds("")  
                            _fsm.move_ai = _fsm.engine.get_best_move()
                            _fsm.go_to_ai_move_state()

                    # Check for pawn promotion
                    elif _fsm.engine_eval.is_move_correct(_fsm.move_human + "q"):
                        _fsm.go_to_pawn_promotion_state()
                else:
                    debug_msg(_args.debug, "move not done")

            # If confirm is pressed, the AI shows best move
            elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):
                debug_msg(_args.debug, "event - hint/ai move")
                # Turn off LEDs for indication
                _board.set_leds("")
                _fsm.move_ai = _fsm.engine.get_best_move()
                _fsm.go_to_ai_move_state()

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):
                debug_msg(_args.debug, "event - undo")
                if _args.debug:
                    _board.full_display(_fsm.engine_eval.get_board_visual())
                _fsm.go_to_undo_move_state()

        elif _fsm.is_ai_move_state:

            """! @brief     Handle AI moves

            @info   Indicate movements and get confirm signals.
            """

            if _fsm.first_entry:
                print(f"STATE: {_fsm.current_state.identifier}")
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
                or (
                    _args.auto_confirm and _board.is_move_done(_fsm.move_ai, _fsm.moves)
                )
            ):

                debug_msg(_args.debug, f"event - confirm ai move: {_fsm.move_ai}")
                if len(_fsm.move_ai) == 5:
                    _fsm.go_to_pawn_promotion_state()
                elif _board.is_move_done(_fsm.move_ai, _fsm.moves):
                    _board.board_prev = _board.board_current
                    if _fsm.engine_eval.is_move_correct(_fsm.move_ai):
                        _board.set_move_done_leds(_fsm.move_ai)
                        _fsm.moves.append(_fsm.move_ai)
                        _fsm.engine.set_position(_fsm.moves)
                        _fsm.engine_eval.set_position(_fsm.moves)
                        try:
                            _fsm.sio.emit(
                                "move_event",
                                {"data": str(_fsm.engine_eval.get_fen_position())},
                            )
                        except:
                            print("Emitting failed")
                        _fsm.move_ai = ""
                        if _args.debug:
                            _board.full_display(_fsm.engine_eval.get_board_visual())
                        if _fsm.engine_eval.get_evaluation() == {
                            "type": "mate",
                            "value": 0,
                        }:
                            _fsm.go_to_checkmate_state()
                        else:
                            _fsm.go_to_human_move_state()
                        _board.board_history.append(_board.board_current)
                else:
                    if _args.debug:
                        _board.display()

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):
                debug_msg(_args.debug, "event - undo")
                if _args.debug:
                    _board.full_display(_fsm.engine_eval.get_board_visual())
                _fsm.go_to_undo_move_state()

        elif _fsm.is_pawn_promotion_state:

            """! @brief     Handle undo moves.

            @info   Indicate movements and get confirm signals.
            """

            if _fsm.first_entry:
                print(f"STATE: {_fsm.current_state.identifier}")
                if _fsm.prev_state.value == "human_move_state":
                    debug_msg(_args.debug, f"from human move state: {_fsm.move_human}")
                    _fsm.move_promotion = _fsm.move_human
                    move_human_flag = True
                    promotion_loop = 0
                elif _fsm.prev_state.value == "ai_move":
                    debug_msg(_args.debug, f"from ai move state: {_fsm.move_ai}")
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
                debug_msg(_args.debug, f"promotion : {promotion_loop}")

            elif GPIO.event_detected(cfg.MCB_BUT_WHITE) and move_human_flag:

                if promotion_loop > 0:
                    promotion_loop -= 1  # Decrement promotion
                else:
                    promotion_loop = 3
                debug_msg(_args.debug, f"promotion : {promotion_loop}")

            elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                if _args.debug:
                    print(f"{cfg.MCB_DEBUG_MSG}q: 0, b: 1, k:2, r:3")
                debug_msg(_args.debug, f"choice: {promotion_loop}")

                _board.read_fields()  # Read and update fields
                if _board.is_move_done(_fsm.move_promotion[:4], _fsm.moves):
                    if _fsm.engine_eval.is_move_correct(_fsm.move_promotion):
                        debug_msg(_args.debug, f"stockfish - move correct")
                        _board.set_move_done_leds(
                            _fsm.move_promotion[:4]
                        )  # Set the field LEDs
                        _fsm.moves.append(
                            _fsm.move_promotion
                        )  # Add the move to the moves list
                        _fsm.engine.set_position(_fsm.moves)  # Set position in AI
                        _fsm.engine_eval.set_position(
                            _fsm.moves
                        )  # Set position in Eval
                        _fsm.move_human = ""  # Reset human move
                        _fsm.move_ai = ""  # Reset ai move
                        if _args.debug:
                            _board.full_display(_fsm.engine_eval.get_board_visual())
                        if _fsm.engine_eval.get_evaluation() == {
                            "type": "mate",
                            "value": 0,
                        }:  # Evaluate if there is a checkmate
                            _fsm.go_to_checkmate_state()  # Change state
                        else:
                            _fsm.go_to_human_move_state()  # Change state
                        _board.board_history.append(
                            _board.board_current
                        )  # Add the current _board to the undo history list

                else:
                    if _args.debug:
                        _board.display()

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):
                debug_msg(_args.debug, f"event - undo")
                if _args.debug:
                    _board.full_display(_fsm.engine_eval.get_board_visual())
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
                debug_msg(_args.debug, f"confirm undo move: {_fsm.move_undo}")
                if _board.is_undo_move_done():  # If the undo move is done
                    del _fsm.moves[-1]  # Delete last move for the engines
                    _fsm.engine.set_position(_fsm.moves)  # Set the moved for ai engine
                    _fsm.engine_eval.set_position(
                        _fsm.moves
                    )  # Set the moved for eval engine
                    if (
                        len(_fsm.moves) > 0
                    ):  # Check if the deleted move was the last one.
                        _board.set_move_done_leds(_fsm.moves[-1])
                    else:
                        _board.set_leds("")
                    if _args.debug:
                        _board.full_display(_fsm.engine_eval.get_board_visual())
                    _fsm.go_to_human_move_state()  # Change state
                else:
                    if _args.debug:
                        _board.display()

            elif GPIO.event_detected(cfg.MCB_BUT_BACK):
                debug_msg(_args.debug, "event - cancel undo")
                _board.set_move_done_leds(_fsm.moves[-1])
                _fsm.go_to_human_move_state()

        # STATE: Checkmate
        elif _fsm.is_checkmate_state:

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

                debug_msg(_args.debug, "go to init")
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
            time.sleep(2)
            _fsm.go_to_init_state()

        # Not initial anymore
        _fsm.initial = False
