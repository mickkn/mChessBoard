"""
    This module implements mchessboard finite state machine.

    :author: Mick Kirkegaard.
"""

from statemachine import StateMachine, State

from board import Board

class BoardFsm(StateMachine):

    """
    Finite State Machine Class
    """

    def __init__(self):

        # Flags & Variables
        self.initial_ = True
        self.first_entry_ = True
        self.prev_state_ = None
        self.current_state_ = None

        # Movement global variables and flags
        self.move_ai_ = ""                ### Move made by AI Engine
        self.move_human_ = ""             ### Move made by Human
        self.move_undo_ = ""              ### Move made by Undo
        self.move_promotion_ = ""         ### Move made by Promotion
        self.moves_ = []                  ### List of moves for engine
        self.play_difficulty_ = 1         ### Default difficulty

        self.mode_setting_ = 0            ### Default mode setting 0: Human vs AI, 1: Human vs. Human
        self.mode_human_color_ = 'white'  ### Default Human color

        # Initialize the states
        self.init_ = State('Init', initial=True)
        self.mode_ = State('Mode')
        self.human_color_ = State('Color')
        self.difficulty_ = State('Difficulty')
        self.setup_ = State('Setup')
        self.human_move_ = State("HumanMove")
        self.ai_move_ = State('AIMove')
        self.checkmate_ = State("Checkmate")
        self.pawn_promotion_ = State("PawnPromotion")
        self.undo_move_ = State('Undo')

        # Initialize all transitions allowed
        self.go_to_init_ = self.difficulty_.to(self.init_) | self.setup_.to(self.init_) | self.human_move_.to(self.init_) | self.ai_move_.to(self.init_) | self.checkmate_.to(self.init_) | self.pawn_promotion_.to(self.init_) | self.undo_move_.to(self.init_) | self.mode_.to(self.init_)
        self.go_to_mode_ = self.init_.to(self.mode_)
        self.go_to_human_color_ = self.mode_.to(self.human_color_)
        self.go_to_difficulty_ = self.human_color_.to(self.difficulty_)
        self.go_to_setup_ = self.difficulty_.to(self.setup_)
        self.go_to_ai_move_ = self.setup_.to(self.ai_move_) | self.human_move_.to(self.ai_move_) | self.pawn_promotion_.to(self.ai_move_)
        self.go_to_human_move_ = self.setup_.to(self.human_move_) | self.ai_move_.to(self.human_move_) | self.undo_move_.to(self.human_move_) | self.pawn_promotion_.to(self.human_move_)
        self.go_to_checkmate_ = self.human_move_.to(self.checkmate_) | self.ai_move_.to(self.checkmate_)
        self.go_to_pawn_promotion_ = self.human_move_.to(self.pawn_promotion_) | self.ai_move_.to(self.pawn_promotion_)
        self.go_to_undo_move_ = self.human_move_.to(self.undo_move_) | self.ai_move_.to(self.undo_move_)


def run(fsm: BoardFsm, board: Board):

    # Set flag if the state has changed
    first_entry = fsm.initial_ or (fsm.current_state_ != fsm.current_state)

    if first_entry:
        fsm.prev_state_ = fsm._current_state
        fsm.current_state_ = fsm.current_state    

    if fsm.is_init:

        """! @brief Init the chess board """

        if first_entry:

            print(f"STATE: {fsm.current_state.identifier}")
            
            fsm.move_ai_ = "" # Reset AI move instance
            fsm.move_human_ = "" # Reset Human move instance
            fsm.moves_ = [] # Reset moves list
            board.add_button_events() # Add button events (delays the setup init)
            board.startup_leds(0.05) # Run the LEDs in a startup sequence

        fsm.go_to_mode_() # Set next state

    elif fsm.is_mode_:

        if first_entry:

            print(f"STATE: {fsm.current_state.identifier}")

            mode_setting = 0 # Reset mode

            board.set_leds('4') # Set LED indicator
        
        if mode_setting == 1:
            
            if (GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE)):

                if args.debug: print(f"{debug_msg}human vs ai")
                mode_setting = 0    # Human vs AI
                board.set_leds('4') # Set LED indicator

            elif GPIO.event_detected(MCB_BUT_CONFIRM):

                fsm.go_to_difficulty() # Change state

        elif mode_setting == 0:

            if (GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE)):

                if args.debug: print(f"{debug_msg}human vs human")
                mode_setting = 1    # Human vs Human
                board.set_leds('5') # Set LED indicator

            elif GPIO.event_detected(MCB_BUT_CONFIRM):
                
                fsm.go_to_human_color() # Change state

    elif fsm.is_human_color:

        if first_entry:

            print(f"STATE: {fsm.current_state.identifier}")
            mode_human_color = 'white' # Reset color    
            board.set_leds('1234') # Set LED indicator to white
        
        if mode_human_color == 'white':
            
            if GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE):

                mode_human_color = 'black' # Human is black
                board.set_leds('5678') # Set LED indicator to black

            elif GPIO.event_detected(MCB_BUT_CONFIRM):

                fsm.go_to_difficulty() # Change state

        elif mode_human_color == 'black':
            
            if GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE):

                mode_human_color = 'white' # Human white
                board.set_leds('1234') # Set LED indicator to white

            elif GPIO.event_detected(MCB_BUT_CONFIRM):

                fsm.go_to_difficulty() # Change state

    elif fsm.is_difficulty:

        """! @brief Set the difficulty of the AI """

        if first_entry:

            print(f"STATE: {fsm.current_state.identifier}")

            board.set_difficulty_leds(play_difficulty) # Set LEDs to default difficulty
        
        if GPIO.event_detected(MCB_BUT_CONFIRM):

            if args.debug: print(f"{debug_msg}confirm ({play_difficulty})")

            board.set_leds("12345678abcdefgh") # Turn on all LEDs

            if play_difficulty == 0:    # Use level random mover on difficulty 0
                if args.debug: print(f"{debug_msg}using Level: {play_difficulty}")
                ai_parameters.update({"UCI_LimitStrength": "false"})
                ai_parameters.update({"Level": play_difficulty})
            else:   # Use a ELO rating
                if args.debug: print(f"{debug_msg}using ELO rating: {play_difficulty * 100 + 600}")
                ai_parameters.update({"UCI_LimitStrength": "true"})
                ai_parameters.update({"UCI_Elo": play_difficulty * 100 + 600})       # 700 to 2800 (limit here is 1500, enough for me)

            # Initiate ai engine
            ai = Stockfish(args.input, parameters=ai_parameters)
            if args.debug: print(f"{debug_msg} {ai.get_parameters()}")

            # Init. eval engine
            stockfish = Stockfish("/home/pi/mChessBoard/src/stockfish-12_linux_x32_armv6", parameters=DEFAULT_STOCKFISH_PARAMS)
            if args.debug: print(f"{debug_msg} {stockfish.get_parameters()}")

            board.set_leds("")
            
            fsm.go_to_setup()

        elif GPIO.event_detected(MCB_BUT_BLACK):

            # Increment difficulty
            if play_difficulty < MCB_PLAY_DIFF_MAX:
                play_difficulty = play_difficulty + 1
            if args.debug: print(f"{debug_msg}difficulty up: {play_difficulty}")
            board.set_difficulty_leds(play_difficulty)

        elif GPIO.event_detected(MCB_BUT_WHITE):

            # Decrement difficulty
            if play_difficulty > MCB_PLAY_DIFF_MIN:
                play_difficulty = play_difficulty - 1
            if args.debug: print(f"{debug_msg}difficulty down: {play_difficulty}")
            board.set_difficulty_leds(play_difficulty)

    elif fsm.is_setup:

        """! @brief     Setting up the board 
        
        @info   Turn on LEDs for columns which is correctly setup
        """

        if first_entry:

            print(f"STATE: {fsm.current_state.identifier}")

            board.add_button_events()   # Add button int. events
            board.add_field_events()    # Add field int. events
            board.set_setup_leds()      # Turn on initial setup LEDs

        # React on field events
        if GPIO.event_detected(MCB_ROW_AB_IO) or GPIO.event_detected(MCB_ROW_CD_IO) or \
            GPIO.event_detected(MCB_ROW_EF_IO) or GPIO.event_detected(MCB_ROW_GH_IO):
            board.set_setup_leds()

        # If board is setup correctly
        elif board.board_current == board.board_setup:
            
            if args.debug: print(f"{debug_msg}board is set up")
            
            board.set_leds("abcdefgh12345678") # Turn on all LEDs
            board.board_prev = board.board_current # Set previous board to current board
            board.board_history = [] # Reset undo history
            board.board_history.append(board.board_current)
            time.sleep(1) # Wait a sec
            board.set_leds("") # Turn off the LEDs
            
            fsm.go_to_human_move() # Change state

        elif GPIO.event_detected(MCB_BUT_BACK):

            fsm.go_to_difficulty() # Change state

    elif fsm.is_human_move:

        """! @brief     Handle Human moves 
        
        @info   Indicate movements and get confirm signals if auto confirm is disabled.
        """

        if first_entry:

            print(f"STATE: {fsm.current_state.identifier}")

            board.add_field_events() # Re-enable event from the fields
            board.add_button_events() # Re-enable event from the buttons
            human_move_field = "" # Reset human move field
            toggle = True # Reset toggle flag
            timer = time.time() # Start timer #TODO

        if (len(move_human) == 4) and (time.time() > (timer + MCB_PLAY_AI_LED_TOGGLE_TIME)):

            toggle = not toggle # Toggle, toggle flag
            timer = time.time() # Take a new timestamp
            board.set_move_led(toggle, move_human) # Toggle the move LEDs

        # Handle events on fields.
        if GPIO.event_detected(MCB_ROW_AB_IO) or GPIO.event_detected(MCB_ROW_CD_IO) or \
            GPIO.event_detected(MCB_ROW_EF_IO) or GPIO.event_detected(MCB_ROW_GH_IO):
            
            human_move_field = board.get_field_event() # Get the specific field event (single field change)
            if args.debug: print(f"{debug_msg}event - field changed: {human_move_field}")

            # If first event and not an empty event
            if len(move_human) == 0 and human_move_field != "":
                board.set_leds(human_move_field) # Set the single field led
                move_human = human_move_field # Setup first field in the move
            # Else if second event and not the same field
            elif len(move_human) == 2 and human_move_field != "" and human_move_field != move_human:
                
                move_human_opposite = human_move_field + move_human # Save an opposite representation
                move_human += human_move_field # Add the new field to the human move

                # Check for incorrectness (also check for pawn promotion)
                if not stockfish.is_move_correct(move_human) and not stockfish.is_move_correct(move_human+'q'):
                    move_human = ""
                    board.set_leds("")
                # Check for correctness opposite if fields are obtained in opposite direction (could be pawn promotion)
                elif stockfish.is_move_correct(move_human_opposite) or stockfish.is_move_correct(move_human_opposite+'q'):
                    move_human = move_human_opposite
            
            if args.debug: print(f"{debug_msg}human move: {move_human}")

        # If black or white is pressed to confirm move, or auto_confirm is active
        elif (GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE) or \
                args.auto_confirm) and len(move_human) == 4:

            if args.debug: print(f"{debug_msg}event - confirm human move: {move_human}")
            board.read_fields() # Read and update fields
            if board.is_move_done(move_human, moves):
                if stockfish.is_move_correct(move_human):
                    if args.debug: print(f"{debug_msg}stockfish - move correct")
                    board.set_move_done_leds(move_human) # Set the field LEDs
                    moves.append(move_human) # Add the move to the moves list
                    stockfish.set_position(moves) # Set position in Stockfish
                    ai.set_position(moves) # Set position in AI
                    move_human = "" # Reset human move
                    if args.debug: board.full_display(stockfish.get_board_visual())
                    if stockfish.get_evaluation() == {"type": "mate", "value": 0}: # Evaluate if there is a checkmate
                        fsm.go_to_checkmate() # Change state
                    board.board_history.append(board.board_current) # Add the current board to the undo history list
                
                # Check for pawn promotion
                elif stockfish.is_move_correct(move_human+'q'):
                    fsm.go_to_pawn_promotion()
            else:
                if args.debug: 
                    board.display()
                    print(f"{debug_msg}move not done")

        elif GPIO.event_detected(MCB_BUT_CONFIRM):
            print(f"{debug_msg}event - hint/ai move")
            board.set_leds("") # Turn off LEDs for indication
            board.remove_field_events()
            move_ai = ai.get_best_move()
            fsm.go_to_ai_move()

        elif GPIO.event_detected(MCB_BUT_BACK):
            if args.debug: print(f"{debug_msg}event - undo")
            if args.debug: board.full_display(stockfish.get_board_visual())
            fsm.go_to_undo_move()

    elif fsm.is_ai_move:

        """! @brief     Handle AI moves 
        
        @info   Indicate movements and get confirm signals.
        """

        if first_entry:
            print(f"STATE: {fsm.current_state.identifier}")
            board.add_field_events() # Re-enable event from the fields
            board.add_button_events() # Re-enable event from the buttons
            timer = time.time()
            toggle = True

        # Handle the led flash indicator timing
        if time.time() > timer + MCB_PLAY_AI_LED_TOGGLE_TIME:
            toggle = not toggle
            board.set_move_led(toggle, move_ai)
            timer = time.time()

        # Confirm AI/hint move
        if args.auto_confirm: board.read_fields()

        if GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE) or (args.auto_confirm and board.is_move_done(move_ai, moves)):

            if args.debug: print(f"{debug_msg}event - confirm ai move: {move_ai}")
            if len(move_ai) == 5:
                fsm.go_to_pawn_promotion()
            elif board.is_move_done(move_ai, moves):
                board.board_prev = board.board_current
                if stockfish.is_move_correct(move_ai):
                    board.set_move_done_leds(move_ai)
                    moves.append(move_ai)
                    stockfish.set_position(moves)
                    ai.set_position(moves)
                    move_ai = ""
                    if args.debug: board.full_display(stockfish.get_board_visual())
                    if stockfish.get_evaluation() == {"type": "mate", "value": 0}:
                        fsm.go_to_checkmate()
                    else:
                        fsm.go_to_human_move()
                    board.board_history.append(board.board_current)
            else:
                if args.debug: board.display()

        elif GPIO.event_detected(MCB_BUT_BACK):
            if args.debug: print(f"{debug_msg}event - undo")
            if args.debug: board.full_display(stockfish.get_board_visual())
            fsm.go_to_undo_move()

    elif fsm.is_pawn_promotion:

        """! @brief     Handle undo moves. 
        
        @info   Indicate movements and get confirm signals.
        """

        if first_entry:
            print(f"STATE: {fsm.current_state.identifier}")
            if prev_state.value == 'human_move':
                if args.debug: print(f"{debug_msg}from human move state: {move_human}")
                move_promotion = move_human
                move_human_flag = True
                promotion_loop = 0
            elif prev_state.value == 'ai_move':
                if args.debug: print(f"{debug_msg}from ai move state: {move_ai}")
                move_promotion = move_ai
                move_human_flag = False
                promotion_loop = -1
            else:
                fsm.go_to_human_move() # Change state
            timer = time.time()

        # Handle the led flash indicator timing
        if (time.time() > timer + MCB_PLAY_AI_LED_TOGGLE_TIME):
            toggle = not toggle
            move_promotion = board.set_promotion_menu_led(toggle, move_promotion, promotion_loop)
            timer = time.time()
        
        if GPIO.event_detected(MCB_BUT_BLACK) and move_human_flag:

            if promotion_loop < 3: promotion_loop += 1 # Increment promotion
            else: promotion_loop = 0
            if args.debug: print(f"{debug_msg}promotion : {promotion_loop}")

        elif GPIO.event_detected(MCB_BUT_WHITE) and move_human_flag:

            if promotion_loop > 0: promotion_loop -= 1 # Decrement promotion
            else: promotion_loop = 3
            if args.debug: print(f"{debug_msg}promotion : {promotion_loop}")

        elif GPIO.event_detected(MCB_BUT_CONFIRM):

            if args.debug: print(f"{debug_msg}q: 0, b: 1, k:2, r:3")
            if args.debug: print(f"{debug_msg}choice: {promotion_loop}")

            board.read_fields() # Read and update fields
            if board.is_move_done(move_promotion[:4], moves):
                if stockfish.is_move_correct(move_promotion):
                        if args.debug: print(f"{debug_msg}stockfish - move correct")
                        board.set_move_done_leds(move_promotion[:4]) # Set the field LEDs
                        moves.append(move_promotion) # Add the move to the moves list
                        stockfish.set_position(moves) # Set position in Stockfish
                        ai.set_position(moves) # Set position in AI
                        move_human = "" # Reset human move
                        move_ai = "" # Reset ai move
                        if args.debug: board.full_display(stockfish.get_board_visual())
                        if stockfish.get_evaluation() == {"type": "mate", "value": 0}: # Evaluate if there is a checkmate
                            fsm.go_to_checkmate() # Change state
                        else:
                            fsm.go_to_human_move() # Change state
                        board.board_history.append(board.board_current) # Add the current board to the undo history list
                        
            else:
                if args.debug: board.display()

        elif GPIO.event_detected(MCB_BUT_BACK):
            if args.debug: print(f"{debug_msg}event - undo")
            if args.debug: board.full_display(stockfish.get_board_visual())
            fsm.go_to_undo_move()


    elif fsm.is_undo_move:

        """! @brief     Handle undo moves. 
        
        @info   Indicate movements and get confirm signals.
        """

        if first_entry:
            print(f"STATE: {fsm.current_state.identifier}")
            timer = time.time()
            toggle = True
            move_human = ""
            move_ai = ""
            move_undo = ""

            # Check if any moves has been made
            if len(moves) > 0:
                if len(moves[-1]) >= 4:
                    # Determine the mode to undo, and to indicate with LED flashing.
                    move_undo = moves[-1][2] + moves[-1][3] + moves[-1][0] + moves[-1][1]
                else:
                    # Cancelling a non-finished move, 
                    # just set LEDs and change state.
                    board.set_move_done_leds(moves[-1])
                    fsm.go_to_human_move()
            else:
                # Cancelling unfinished first move, 
                # just turn off LEDs and change state.
                board.set_leds("") 
                fsm.go_to_human_move()

        # Handle the led flash indicator timing
        if (time.time() > timer + MCB_PLAY_AI_LED_TOGGLE_TIME) and (len(move_undo) == 4):
            toggle = not toggle
            board.set_move_led(toggle, move_undo)
            timer = time.time()
        
        # Confirm Undo move
        if GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE):
            if args.debug: print(f"{debug_msg}confirm undo move: {move_undo}")
            if board.is_undo_move_done(): # If the undo move is done
                del moves[-1] # Delete last move for the engines
                stockfish.set_position(moves) # Set the moved for eval engine
                ai.set_position(moves) # Set the moved for ai engine
                if len(moves) > 0: # Check if the deleted move was the last one.
                    board.set_move_done_leds(moves[-1])
                else:
                    board.set_leds("")
                if args.debug: board.full_display(stockfish.get_board_visual())
                fsm.go_to_human_move() # Change state
            else:
                if args.debug: board.display()

        elif GPIO.event_detected(MCB_BUT_BACK):
            if args.debug: print(f"{debug_msg}event - cancel undo")
            board.set_move_done_leds(moves[-1])
            fsm.go_to_human_move()

    # STATE: Checkmate
    elif fsm.is_checkmate:

        """! @brief     Handle checkmate. 
        
        @info   Flash the LEDs for indication and go to init when button is pressed.
        """

        if first_entry:
            print(f"STATE: {fsm.current_state.identifier}")
            timer = time.time()
            toggle = True

        if time.time() > timer + MCB_PLAY_CHECKMATE_LED_TOGGLE_TIME:
            if toggle:
                board.set_leds("12345678abcdefgh")
                toggle = False
            else:
                board.set_leds("")
                toggle = True
            timer = time.time()

        if GPIO.event_detected(MCB_BUT_WHITE) or \
            GPIO.event_detected(MCB_BUT_BLACK) or \
            GPIO.event_detected(MCB_BUT_CONFIRM) or \
            GPIO.event_detected(MCB_BUT_BACK):

            if args.debug: print(f"{debug_msg}go to init")
            board.remove_button_events()
            board.remove_field_events()
            fsm.go_to_init()

    # Reset (all buttons pressed)
    if not GPIO.input(MCB_BUT_WHITE) and \
        not GPIO.input(MCB_BUT_BLACK) and \
        not GPIO.input(MCB_BUT_CONFIRM) and \
        not GPIO.input(MCB_BUT_BACK):

        if args.debug: print(f"{debug_msg}resetting")
        board.set_leds("abcdefgh12345678")
        board.remove_button_events()
        board.remove_field_events()
        time.sleep(2)
        fsm.go_to_init()

    # Not initial anymore
    initial = False