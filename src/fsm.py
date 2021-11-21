"""
    This module implements mchessboard finite state machine.

    :author: Mick Kirkegaard.
"""

from statemachine import StateMachine, State

from board import Board
from config import Config
from stockfish import Stockfish  # https://pypi.org/project/stockfish/ edited to fit for Minic
import time

import RPi.GPIO as GPIO

class BoardFsm(StateMachine):

    """
    Finite State Machine Class
    """

    # Flags & Variables
    initial_ = True
    first_entry_ = True
    prev_state_ = None
    current_state_ = None
    toggle = None

    # Movement global variables and flags
    move_ai_ = ""                ### Move made by AI Engine
    move_human_ = ""             ### Move made by Human
    move_undo_ = ""              ### Move made by Undo
    move_promotion_ = ""         ### Move made by Promotion
    moves_ = []                  ### List of moves for engine
    play_difficulty_ = 1         ### Default difficulty

    mode_setting_ = 0            ### Default mode setting 0: Human vs AI, 1: Human vs. Human
    mode_human_color_ = 'white'  ### Default Human color
    timer = None

    # Initialize the states
    init_ = State('Init', initial=True)
    mode_ = State('Mode')
    human_color_ = State('Color')
    difficulty_ = State('Difficulty')
    setup_ = State('Setup')
    human_move_ = State("HumanMove")
    ai_move_ = State('AIMove')
    checkmate_ = State("Checkmate")
    pawn_promotion_ = State("PawnPromotion")
    undo_move_ = State('Undo')

    # Initialize all transitions allowed
    go_to_init_ = difficulty_.to(init_) | setup_.to(init_) | human_move_.to(init_) | ai_move_.to(init_) | checkmate_.to(init_) | pawn_promotion_.to(init_) | undo_move_.to(init_) | mode_.to(init_)
    go_to_mode_ = init_.to(mode_)
    go_to_human_color_ = mode_.to(human_color_)
    go_to_difficulty_ = human_color_.to(difficulty_) | mode_.to(difficulty_)
    go_to_setup_ = difficulty_.to(setup_)
    go_to_ai_move_ = setup_.to(ai_move_) | human_move_.to(ai_move_) | pawn_promotion_.to(ai_move_)
    go_to_human_move_ = setup_.to(human_move_) | ai_move_.to(human_move_) | undo_move_.to(human_move_) | pawn_promotion_.to(human_move_)
    go_to_checkmate_ = human_move_.to(checkmate_) | ai_move_.to(checkmate_)
    go_to_pawn_promotion_ = human_move_.to(pawn_promotion_) | ai_move_.to(pawn_promotion_)
    go_to_undo_move_ = human_move_.to(undo_move_) | ai_move_.to(undo_move_)

    # Setup engines
    stockfish = None
    ai = None


def run(fsm: BoardFsm, args: list(), board: Board, cfg: Config):


    # Set flag if the state has changed
    fsm.first_entry_ = fsm.initial_ or (fsm.current_state_ != fsm.current_state)

    if fsm.first_entry_:
        fsm.prev_state_ = fsm.current_state_
        fsm.current_state_ = fsm.current_state

    if fsm.is_init_:

        """! @brief Init the chess board """

        if fsm.first_entry_:

            print(f"STATE: {fsm.current_state.identifier}")
            
            fsm.move_ai_ = "" # Reset AI move instance
            fsm.move_human_ = "" # Reset Human move instance
            fsm.moves_ = [] # Reset moves list
            board.add_button_events() # Add button events (delays the setup init)
            board.startup_leds(0.05) # Run the LEDs in a startup sequence

        fsm.go_to_mode_() # Set next state

    elif fsm.is_mode_:

        if fsm.first_entry_:

            print(f"STATE: {fsm.current_state.identifier}")

            fsm.mode_setting_ = 0 # Reset mode

            board.set_leds('4') # Set LED indicator
        
        if fsm.mode_setting_ == 1:
            
            if (GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(cfg.MCB_BUT_WHITE)):

                if args.debug: print(f"{cfg.debug_msg}human vs ai")
                fsm.mode_setting_ = 0    # Human vs AI
                board.set_leds('4') # Set LED indicator

            elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                fsm.go_to_difficulty_() # Change state

        elif fsm.mode_setting_ == 0:

            if (GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(cfg.MCB_BUT_WHITE)):

                if args.debug: print(f"{cfg.debug_msg}human vs human")
                fsm.mode_setting_ = 1    # Human vs Human
                board.set_leds('5') # Set LED indicator

            elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):
                
                fsm.go_to_human_color_() # Change state

    elif fsm.is_human_color_:

        if fsm.first_entry_:

            print(f"STATE: {fsm.current_state.identifier}")
            fsm.mode_human_color_ = 'white' # Reset color    
            board.set_leds('1234') # Set LED indicator to white
        
        if fsm.mode_human_color_ == 'white':
            
            if GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(cfg.MCB_BUT_WHITE):

                fsm.mode_human_color_ = 'black' # Human is black
                board.set_leds('5678') # Set LED indicator to black

            elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                fsm.go_to_difficulty_() # Change state

        elif fsm.mode_human_color_ == 'black':
            
            if GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(cfg.MCB_BUT_WHITE):

                fsm.mode_human_color_ = 'white' # Human white
                board.set_leds('1234') # Set LED indicator to white

            elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

                fsm.go_to_difficulty_() # Change state

    elif fsm.is_difficulty_:

        """! @brief Set the difficulty of the AI """

        if fsm.first_entry_:

            print(f"STATE: {fsm.current_state.identifier}")

            board.set_difficulty_leds(fsm.play_difficulty_) # Set LEDs to default difficulty
        
        if GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

            if args.debug: print(f"{cfg.debug_msg}confirm ({fsm.play_difficulty_})")

            board.set_leds("12345678abcdefgh") # Turn on all LEDs

            if fsm.play_difficulty_ == 0:    # Use level random mover on difficulty 0
                if args.debug: print(f"{cfg.debug_msg}using Level: {fsm.play_difficulty_}")
                cfg.ai_parameters.update({"UCI_LimitStrength": "false"})
                cfg.ai_parameters.update({"Level": fsm.play_difficulty_})
            else:   # Use a ELO rating
                if args.debug: print(f"{cfg.debug_msg}using ELO rating: {fsm.play_difficulty_ * 100 + 600}")
                cfg.ai_parameters.update({"UCI_LimitStrength": "true"})
                cfg.ai_parameters.update({"UCI_Elo": fsm.play_difficulty_ * 100 + 600})       # 700 to 2800 (limit here is 1500, enough for me)

            # Initiate ai engine
            fsm.ai = Stockfish(args.input, parameters=cfg.ai_parameters)
            if args.debug: print(f"{cfg.debug_msg} {fsm.ai.get_parameters()}")

            # Init. eval engine
            fsm.stockfish = Stockfish("/home/pi/mChessBoard/src/stockfish-12_linux_x32_armv6", parameters=cfg.DEFAULT_STOCKFISH_PARAMS)
            if args.debug: print(f"{cfg.debug_msg} {fsm.stockfish.get_parameters()}")

            board.set_leds("")
            
            fsm.go_to_setup_()

        elif GPIO.event_detected(cfg.MCB_BUT_BLACK):

            # Increment difficulty
            if fsm.play_difficulty_ < cfg.MCB_PLAY_DIFF_MAX:
                fsm.play_difficulty_ = fsm.play_difficulty_ + 1
            if args.debug: print(f"{cfg.debug_msg}difficulty up: {fsm.play_difficulty_}")
            board.set_difficulty_leds(fsm.play_difficulty_)

        elif GPIO.event_detected(cfg.MCB_BUT_WHITE):

            # Decrement difficulty
            if fsm.play_difficulty_ > cfg.MCB_PLAY_DIFF_MIN:
                fsm.play_difficulty_ = fsm.play_difficulty_ - 1
            if args.debug: print(f"{cfg.debug_msg}difficulty down: {fsm.play_difficulty_}")
            board.set_difficulty_leds(fsm.play_difficulty_)

    elif fsm.is_setup_:

        """! @brief     Setting up the board 
        
        @info   Turn on LEDs for columns which is correctly setup
        """

        if fsm.first_entry_:

            print(f"STATE: {fsm.current_state.identifier}")

            board.add_button_events()   # Add button int. events
            board.add_field_events()    # Add field int. events
            board.set_setup_leds()      # Turn on initial setup LEDs

        # React on field events
        if GPIO.event_detected(cfg.MCB_ROW_AB_IO) or GPIO.event_detected(cfg.MCB_ROW_CD_IO) or \
            GPIO.event_detected(cfg.MCB_ROW_EF_IO) or GPIO.event_detected(cfg.MCB_ROW_GH_IO):
            board.set_setup_leds()

        # If board is setup correctly
        elif board.board_current == board.board_setup:
            
            if args.debug: print(f"{cfg.debug_msg}board is set up")
            
            board.set_leds("abcdefgh12345678") # Turn on all LEDs
            board.board_prev = board.board_current # Set previous board to current board
            board.board_history = [] # Reset undo history
            board.board_history.append(board.board_current)
            time.sleep(1) # Wait a sec
            board.set_leds("") # Turn off the LEDs
            
            fsm.go_to_human_move_() # Change state

        elif GPIO.event_detected(cfg.MCB_BUT_BACK):

            fsm.go_to_difficulty_() # Change state

    elif fsm.is_human_move_:

        """! @brief     Handle Human moves 
        
        @info   Indicate movements and get confirm signals if auto confirm is disabled.
        """

        if fsm.first_entry_:

            print(f"STATE: {fsm.current_state.identifier}")

            board.add_field_events() # Re-enable event from the fields
            board.add_button_events() # Re-enable event from the buttons
            fsm.human_move_field_ = "" # Reset human move field
            fsm.toggle = True # Reset toggle flag
            fsm.timer = time.time() # Start timer #TODO

        if (len(fsm.move_human_) == 4) and (time.time() > (fsm.timer + cfg.MCB_PLAY_AI_LED_TOGGLE_TIME)):

            fsm.toggle = not fsm.toggle # Toggle, toggle flag
            fsm.timer = time.time() # Take a new timestamp
            board.set_move_led(fsm.toggle, fsm.move_human_) # Toggle the move LEDs

        # Handle events on fields.
        if GPIO.event_detected(cfg.MCB_ROW_AB_IO) or GPIO.event_detected(cfg.MCB_ROW_CD_IO) or \
            GPIO.event_detected(cfg.MCB_ROW_EF_IO) or GPIO.event_detected(cfg.MCB_ROW_GH_IO):
            
            human_move_field = board.get_field_event() # Get the specific field event (single field change)
            if args.debug: print(f"{cfg.debug_msg}event - field changed: {human_move_field}")

            # If first event and not an empty event
            if len(fsm.move_human_) == 0 and human_move_field != "":
                board.set_leds(human_move_field) # Set the single field led
                fsm.move_human_ = human_move_field # Setup first field in the move
            # Else if second event and not the same field
            elif len(fsm.move_human_) == 2 and human_move_field != "" and human_move_field != fsm.move_human_:
                
                move_human_opposite = human_move_field + fsm.move_human_ # Save an opposite representation
                fsm.move_human_ += human_move_field # Add the new field to the human move

                # Check for incorrectness (also check for pawn promotion)
                if not fsm.stockfish.is_move_correct(fsm.move_human_) and not fsm.stockfish.is_move_correct(fsm.move_human_+'q'):
                    fsm.move_human_ = ""
                    board.set_leds("")
                # Check for correctness opposite if fields are obtained in opposite direction (could be pawn promotion)
                elif fsm.stockfish.is_move_correct(move_human_opposite) or fsm.stockfish.is_move_correct(move_human_opposite+'q'):
                    fsm.move_human_ = move_human_opposite
            
            if args.debug: print(f"{cfg.debug_msg}human move: {fsm.move_human_}")

        # If black or white is pressed to confirm move, or auto_confirm is active
        elif (GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(cfg.MCB_BUT_WHITE) or \
                args.auto_confirm) and len(fsm.move_human_) == 4:

            if args.debug: print(f"{cfg.debug_msg}event - confirm human move: {fsm.move_human_}")
            board.read_fields() # Read and update fields
            if board.is_move_done(fsm.move_human_, fsm.moves_):
                if fsm.stockfish.is_move_correct(fsm.move_human_):
                    if args.debug: print(f"{cfg.debug_msg}stockfish - move correct")
                    board.set_move_done_leds(fsm.move_human_) # Set the field LEDs
                    fsm.moves_.append(fsm.move_human_) # Add the move to the moves list
                    fsm.stockfish.set_position(fsm.moves_) # Set position in Stockfish
                    fsm.ai.set_position(fsm.moves_) # Set position in AI
                    fsm.move_human_ = "" # Reset human move
                    if args.debug: board.full_display(fsm.stockfish.get_board_visual())
                    if fsm.stockfish.get_evaluation() == {"type": "mate", "value": 0}: # Evaluate if there is a checkmate
                        fsm.go_to_checkmate() # Change state
                    board.board_history.append(board.board_current) # Add the current board to the undo history list
                
                # Check for pawn promotion
                elif fsm.stockfish.is_move_correct(fsm.move_human_+'q'):
                    fsm.go_to_pawn_promotion()
            else:
                if args.debug: 
                    board.display()
                    print(f"{cfg.debug_msg}move not done")

        elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):
            print(f"{cfg.debug_msg}event - hint/ai move")
            board.set_leds("") # Turn off LEDs for indication
            board.remove_field_events()
            fsm.move_ai_ = fsm.ai.get_best_move()
            fsm.go_to_ai_move_()

        elif GPIO.event_detected(cfg.MCB_BUT_BACK):
            if args.debug: print(f"{cfg.debug_msg}event - undo")
            if args.debug: board.full_display(fsm.stockfish.get_board_visual())
            fsm.go_to_undo_move_()

    elif fsm.is_ai_move_:

        """! @brief     Handle AI moves 
        
        @info   Indicate movements and get confirm signals.
        """

        if fsm.first_entry_:
            print(f"STATE: {fsm.current_state.identifier}")
            board.add_field_events() # Re-enable event from the fields
            board.add_button_events() # Re-enable event from the buttons
            fsm.timer = time.time()
            fsm.toggle = True

        # Handle the led flash indicator timing
        if time.time() > fsm.timer + cfg.MCB_PLAY_AI_LED_TOGGLE_TIME:
            fsm.toggle = not fsm.toggle
            board.set_move_led(fsm.toggle, fsm.move_ai_)
            fsm.timer = time.time()

        # Confirm AI/hint move
        if args.auto_confirm: board.read_fields()

        if GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(cfg.MCB_BUT_WHITE) or (args.auto_confirm and board.is_move_done(fsm.move_ai_, fsm.moves_)):

            if args.debug: print(f"{cfg.debug_msg}event - confirm ai move: {fsm.move_ai_}")
            if len(fsm.move_ai_) == 5:
                fsm.go_to_pawn_promotion_()
            elif board.is_move_done(fsm.move_ai_, fsm.moves_):
                board.board_prev = board.board_current
                if fsm.stockfish.is_move_correct(fsm.move_ai_):
                    board.set_move_done_leds(fsm.move_ai_)
                    fsm.moves_.append(fsm.move_ai_)
                    fsm.stockfish.set_position(fsm.moves_)
                    fsm.ai.set_position(fsm.moves_)
                    fsm.move_ai_ = ""
                    if args.debug: board.full_display(fsm.stockfish.get_board_visual())
                    if fsm.stockfish.get_evaluation() == {"type": "mate", "value": 0}:
                        fsm.go_to_checkmate()
                    else:
                        fsm.go_to_human_move_()
                    board.board_history.append(board.board_current)
            else:
                if args.debug: board.display()

        elif GPIO.event_detected(cfg.MCB_BUT_BACK):
            if args.debug: print(f"{cfg.debug_msg}event - undo")
            if args.debug: board.full_display(fsm.stockfish.get_board_visual())
            fsm.go_to_undo_move_()

    elif fsm.is_pawn_promotion_:

        """! @brief     Handle undo moves. 
        
        @info   Indicate movements and get confirm signals.
        """

        if fsm.first_entry_:
            print(f"STATE: {fsm.current_state.identifier}")
            if fsm.prev_state_.value == 'human_move_':
                if args.debug: print(f"{cfg.debug_msg}from human move state: {fsm.move_human_}")
                fsm.move_promotion_ = fsm.move_human_
                move_human_flag = True
                promotion_loop = 0
            elif fsm.prev_state_.value == 'ai_move':
                if args.debug: print(f"{cfg.debug_msg}from ai move state: {fsm.move_ai_}")
                fsm.move_promotion_ = fsm.move_ai_
                move_human_flag = False
                promotion_loop = -1
            else:
                fsm.go_to_human_move_() # Change state
            fsm.timer = time.time()

        # Handle the led flash indicator timing
        if (time.time() > fsm.timer + cfg.MCB_PLAY_AI_LED_TOGGLE_TIME):
            fsm.toggle = not fsm.toggle
            fsm.move_promotion_ = board.set_promotion_menu_led(fsm.toggle, fsm.move_promotion_, promotion_loop)
            fsm.timer = time.time()
        
        if GPIO.event_detected(cfg.MCB_BUT_BLACK) and move_human_flag:

            if promotion_loop < 3: promotion_loop += 1 # Increment promotion
            else: promotion_loop = 0
            if args.debug: print(f"{cfg.debug_msg}promotion : {promotion_loop}")

        elif GPIO.event_detected(cfg.MCB_BUT_WHITE) and move_human_flag:

            if promotion_loop > 0: promotion_loop -= 1 # Decrement promotion
            else: promotion_loop = 3
            if args.debug: print(f"{cfg.debug_msg}promotion : {promotion_loop}")

        elif GPIO.event_detected(cfg.MCB_BUT_CONFIRM):

            if args.debug: print(f"{cfg.debug_msg}q: 0, b: 1, k:2, r:3")
            if args.debug: print(f"{cfg.debug_msg}choice: {promotion_loop}")

            board.read_fields() # Read and update fields
            if board.is_move_done(fsm.move_promotion_[:4], fsm.moves_):
                if fsm.stockfish.is_move_correct(fsm.move_promotion_):
                        if args.debug: print(f"{cfg.debug_msg}stockfish - move correct")
                        board.set_move_done_leds(fsm.move_promotion_[:4]) # Set the field LEDs
                        fsm.moves_.append(fsm.move_promotion_) # Add the move to the moves list
                        fsm.stockfish.set_position(fsm.moves_) # Set position in Stockfish
                        fsm.ai.set_position(fsm.moves_) # Set position in AI
                        fsm.move_human_ = "" # Reset human move
                        fsm.move_ai_ = "" # Reset ai move
                        if args.debug: board.full_display(fsm.stockfish.get_board_visual())
                        if fsm.stockfish.get_evaluation() == {"type": "mate", "value": 0}: # Evaluate if there is a checkmate
                            fsm.go_to_checkmate() # Change state
                        else:
                            fsm.go_to_human_move_() # Change state
                        board.board_history.append(board.board_current) # Add the current board to the undo history list
                        
            else:
                if args.debug: board.display()

        elif GPIO.event_detected(cfg.MCB_BUT_BACK):
            if args.debug: print(f"{cfg.debug_msg}event - undo")
            if args.debug: board.full_display(fsm.stockfish.get_board_visual())
            fsm.go_to_undo_move_()


    elif fsm.is_undo_move_:

        """! @brief     Handle undo moves. 
        
        @info   Indicate movements and get confirm signals.
        """

        if fsm.first_entry_:
            print(f"STATE: {fsm.current_state.identifier}")
            fsm.timer = time.time()
            fsm.toggle = True
            fsm.move_human_ = ""
            fsm.move_ai_ = ""
            fsm.move_undo_ = ""

            # Check if any moves has been made
            if len(fsm.moves_) > 0:
                if len(fsm.moves_[-1]) >= 4:
                    # Determine the mode to undo, and to indicate with LED flashing.
                    fsm.move_undo_ = fsm.moves_[-1][2] + fsm.moves_[-1][3] + fsm.moves_[-1][0] + fsm.moves_[-1][1]
                else:
                    # Cancelling a non-finished move, 
                    # just set LEDs and change state.
                    board.set_move_done_leds(fsm.moves_[-1])
                    fsm.go_to_human_move_()
            else:
                # Cancelling unfinished first move, 
                # just turn off LEDs and change state.
                board.set_leds("") 
                fsm.go_to_human_move_()

        # Handle the led flash indicator timing
        if (time.time() > fsm.timer + cfg.MCB_PLAY_AI_LED_TOGGLE_TIME) and (len(fsm.move_undo_) == 4):
            fsm.toggle = not fsm.toggle
            board.set_move_led(fsm.toggle, fsm.move_undo_)
            fsm.timer = time.time()
        
        # Confirm Undo move
        if GPIO.event_detected(cfg.MCB_BUT_BLACK) or GPIO.event_detected(cfg.MCB_BUT_WHITE):
            if args.debug: print(f"{cfg.debug_msg}confirm undo move: {fsm.move_undo_}")
            if board.is_undo_move_done(): # If the undo move is done
                del fsm.moves_[-1] # Delete last move for the engines
                fsm.stockfish.set_position(fsm.moves_) # Set the moved for eval engine
                fsm.ai.set_position(fsm.moves_) # Set the moved for ai engine
                if len(fsm.moves_) > 0: # Check if the deleted move was the last one.
                    board.set_move_done_leds(fsm.moves_[-1])
                else:
                    board.set_leds("")
                if args.debug: board.full_display(fsm.stockfish.get_board_visual())
                fsm.go_to_human_move_() # Change state
            else:
                if args.debug: board.display()

        elif GPIO.event_detected(cfg.MCB_BUT_BACK):
            if args.debug: print(f"{cfg.debug_msg}event - cancel undo")
            board.set_move_done_leds(fsm.moves_[-1])
            fsm.go_to_human_move_()

    # STATE: Checkmate
    elif fsm.is_checkmate:

        """! @brief     Handle checkmate. 
        
        @info   Flash the LEDs for indication and go to init when button is pressed.
        """

        if fsm.first_entry_:
            print(f"STATE: {fsm.current_state.identifier}")
            fsm.timer = time.time()
            toggle = True

        if time.time() > fsm.timer + cfg.MCB_PLAY_CHECKMATE_LED_TOGGLE_TIME:
            if toggle:
                board.set_leds("12345678abcdefgh")
                toggle = False
            else:
                board.set_leds("")
                toggle = True
            fsm.timer = time.time()

        if GPIO.event_detected(cfg.MCB_BUT_WHITE) or \
            GPIO.event_detected(cfg.MCB_BUT_BLACK) or \
            GPIO.event_detected(cfg.MCB_BUT_CONFIRM) or \
            GPIO.event_detected(cfg.MCB_BUT_BACK):

            if args.debug: print(f"{cfg.debug_msg}go to init")
            board.remove_button_events()
            board.remove_field_events()
            fsm.go_to_init_()

    # Reset (all buttons pressed)
    if not GPIO.input(cfg.MCB_BUT_WHITE) and \
        not GPIO.input(cfg.MCB_BUT_BLACK) and \
        not GPIO.input(cfg.MCB_BUT_CONFIRM) and \
        not GPIO.input(cfg.MCB_BUT_BACK):

        if args.debug: print(f"{cfg.debug_msg}resetting")
        board.set_leds("abcdefgh12345678")
        board.remove_button_events()
        board.remove_field_events()
        time.sleep(2)
        fsm.go_to_init_()

    # Not initial anymore
    fsm.initial_ = False
