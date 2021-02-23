import argparse
import time
from signal import signal, SIGINT
import sys
import threading
import RPi.GPIO as GPIO

from statemachine import StateMachine, State
from stockfish import Stockfish     # https://pypi.org/project/stockfish/
from pcf8575 import PCF8575         # https://pypi.org/project/pcf8575/

APPTITLE    = "mChessBoard"
AUTHOR      = "by Mick Kirkegaard"
VERSION     = "v1.0.0"
DATE        = "Jan 01 2021 19:01"

"""! @brief     Play defines """
MCB_PLAY_DIFF_MAX = 8
MCB_PLAY_DIFF_MIN = 1
MCB_PLAY_AI_LED_TOGGLE_TIME = 0.5 # sec

"""! @brief     Board defines """
MCB_I2C_PORT_NUM = 1
MCB_I2C_ROW_AB_ADDRESS = 0x23
MCB_I2C_ROW_CD_ADDRESS = 0x22
MCB_I2C_ROW_EF_ADDRESS = 0x21
MCB_I2C_ROW_GH_ADDRESS = 0x20
MCB_I2C_LEDS_ADDRESS   = 0x24

MCB_BUT_WHITE       = 17        # Closest to WHITE side
MCB_BUT_CONFIRM     = 27        # Middle close to WHITE side
MCB_BUT_BACK        = 23        # Middle close to BLACK side
MCB_BUT_BLACK       = 22        # Closest to BLACK side
MCB_BUT_DEBOUNCE    = 250       # Button debounce
MCB_FIELD_DEBOUNCE  = 100       # Field debounce

"""! @brief     Board fields and leds"""
pcf_row_ab = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_AB_ADDRESS)
pcf_row_cd = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_CD_ADDRESS)
pcf_row_ef = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_EF_ADDRESS)
pcf_row_gh = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_GH_ADDRESS)
pcf_leds   = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_LEDS_ADDRESS)

MCB_ROW_AB_IO = 6
MCB_ROW_CD_IO = 13
MCB_ROW_EF_IO = 19
MCB_ROW_GH_IO = 26

"""! @brief     Other defines """

DEBUG = True

"""! @brief     Global variables """

ai_move_toggle_timer = True

def parser():

    """! @brief     Parser function to get all the arguments """

    # Description string
    description = "Description: " + APPTITLE + " " + VERSION + " " + DATE + " " + AUTHOR
    
    # Construct the argument parse and return the arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=description)
    
    parser.add_argument("-i", "--input", type=str, default="/home/pi/mChessBoard/src/stockfish-rpiz",
                        help="path to stockfish executable")
    parser.add_argument('--version', action='version', version=APPTITLE + " " + VERSION + " " + DATE + " " + AUTHOR)
    
    print('\n' + str(parser.parse_args()) + '\n')

    return parser.parse_args()

class ChessBoard(StateMachine):

    def __init__(self):

        # Initialize all fields to False
        self.a = [False, False, False, False, False, False, False, False]
        self.b = [False, False, False, False, False, False, False, False]
        self.c = [False, False, False, False, False, False, False, False]
        self.d = [False, False, False, False, False, False, False, False]
        self.e = [False, False, False, False, False, False, False, False]
        self.f = [False, False, False, False, False, False, False, False]
        self.g = [False, False, False, False, False, False, False, False]
        self.h = [False, False, False, False, False, False, False, False]

        self.board = [self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h]

        self.a_prev = [False, False, False, False, False, False, False, False]
        self.b_prev = [False, False, False, False, False, False, False, False]
        self.c_prev = [False, False, False, False, False, False, False, False]
        self.d_prev = [False, False, False, False, False, False, False, False]
        self.e_prev = [False, False, False, False, False, False, False, False]
        self.f_prev = [False, False, False, False, False, False, False, False]
        self.g_prev = [False, False, False, False, False, False, False, False]
        self.h_prev = [False, False, False, False, False, False, False, False]

        self.board_prev = [self.a_prev, self.b_prev, self.c_prev, self.d_prev, self.e_prev, self.f_prev, self.g_prev, self.h_prev]

        # Set all inputs high on init
        pcf_row_ab.port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]
        pcf_row_cd.port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]
        pcf_row_ef.port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]
        pcf_row_gh.port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]

        # Set GPIO mode
        GPIO.setmode(GPIO.BCM)

        # Init field interrupts
        GPIO.setup(MCB_ROW_AB_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(MCB_ROW_CD_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(MCB_ROW_EF_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(MCB_ROW_GH_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Init buttons
        GPIO.setup(MCB_BUT_WHITE, GPIO.IN)
        GPIO.setup(MCB_BUT_CONFIRM, GPIO.IN)
        GPIO.setup(MCB_BUT_BACK, GPIO.IN)
        GPIO.setup(MCB_BUT_BLACK, GPIO.IN)

    def add_button_events(self):
        GPIO.add_event_detect(MCB_BUT_WHITE, GPIO.FALLING, bouncetime=MCB_BUT_DEBOUNCE)
        GPIO.add_event_detect(MCB_BUT_CONFIRM, GPIO.FALLING, bouncetime=MCB_BUT_DEBOUNCE)
        GPIO.add_event_detect(MCB_BUT_BACK, GPIO.FALLING, bouncetime=MCB_BUT_DEBOUNCE)
        GPIO.add_event_detect(MCB_BUT_BLACK, GPIO.FALLING, bouncetime=MCB_BUT_DEBOUNCE)

    def remove_button_events(self):
        GPIO.remove_event_detect(MCB_BUT_WHITE)
        GPIO.remove_event_detect(MCB_BUT_CONFIRM)
        GPIO.remove_event_detect(MCB_BUT_BACK)
        GPIO.remove_event_detect(MCB_BUT_BLACK)

    def add_field_events(self):
        GPIO.add_event_detect(MCB_ROW_AB_IO, GPIO.FALLING, bouncetime=MCB_FIELD_DEBOUNCE)
        GPIO.add_event_detect(MCB_ROW_CD_IO, GPIO.FALLING, bouncetime=MCB_FIELD_DEBOUNCE)
        GPIO.add_event_detect(MCB_ROW_EF_IO, GPIO.FALLING, bouncetime=MCB_FIELD_DEBOUNCE)
        GPIO.add_event_detect(MCB_ROW_GH_IO, GPIO.FALLING, bouncetime=MCB_FIELD_DEBOUNCE)

    def remove_field_events(self):
        GPIO.remove_event_detect(MCB_ROW_AB_IO)
        GPIO.remove_event_detect(MCB_ROW_CD_IO)
        GPIO.remove_event_detect(MCB_ROW_EF_IO)
        GPIO.remove_event_detect(MCB_ROW_GH_IO)

    def is_setup_done(self):
        
        if  (self.a == [False, False, True, True, True, True, False, False]) and \
            (self.b == [False, False, True, True, True, True, False, False]) and \
            (self.c == [False, False, True, True, True, True, False, False]) and \
            (self.d == [False, False, True, True, True, True, False, False]) and \
            (self.e == [False, False, True, True, True, True, False, False]) and \
            (self.f == [False, False, True, True, True, True, False, False]) and \
            (self.g == [False, False, True, True, True, True, False, False]) and \
            (self.h == [False, False, True, True, True, True, False, False]):
            return True
        else:
            return False

    def startup_leds(self):

        delay = 0.07

        def dance_out():
            self.set_leds("a1")
            time.sleep(delay)
            self.set_leds("a1b2")
            time.sleep(delay)
            self.set_leds("a1b2c3")
            time.sleep(delay)
            self.set_leds("a1b2c3d4")
            time.sleep(delay)
            self.set_leds("a1b2c3d4e5")
            time.sleep(delay)
            self.set_leds("a1b2c3d4e5f6")
            time.sleep(delay)
            self.set_leds("a1b2c3d4e5f6g7")
            time.sleep(delay)
            self.set_leds("a1b2c3d4e5f6g7h8")
            time.sleep(delay)
            time.sleep(delay)

        def dance_in():
            self.set_leds("a1b2c3d4e5f6g7")
            time.sleep(delay)
            self.set_leds("a1b2c3d4e5f6")
            time.sleep(delay)
            self.set_leds("a1b2c3d4e5f6")
            time.sleep(delay)
            self.set_leds("a1b2c3d4e5")
            time.sleep(delay)
            self.set_leds("a1b2c3d4")
            time.sleep(delay)
            self.set_leds("a1b2c3")
            time.sleep(delay)
            self.set_leds("a1b2")
            time.sleep(delay)
            self.set_leds("a1")
            time.sleep(delay)
            self.set_leds("")
            time.sleep(delay)

        dance_out()
        dance_in()
        dance_out()
        dance_in()

    def read_fields(self):

        # Read the PCF8575 boards (this is done with the assumption that a1 = p00 etc. reason for reversion)
        self.a = [i for i in pcf_row_ab.port][8:][::-1]
        self.b = [i for i in pcf_row_ab.port][:8][::-1]
        self.c = [i for i in pcf_row_cd.port][8:][::-1]
        self.d = [i for i in pcf_row_cd.port][:8][::-1]
        self.e = [i for i in pcf_row_ef.port][8:][::-1]
        self.f = [i for i in pcf_row_ef.port][:8][::-1]
        self.g = [i for i in pcf_row_gh.port][8:][::-1]
        self.h = [i for i in pcf_row_gh.port][:8][::-1]

        self.board = [self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h]

    def get_lifted_field(self):

        self.read_fields()

    def get_placed_field(self):

        self.read_fields()

    def hint_ai_move(self, toggle:bool, move:str):

        if toggle:
            self.set_leds(move[0] + move[1])
        else:
            self.set_leds(move[0] + move[1] + move[2] + move[3])
    
    def hint_ai_move_done(self, move:str):

        self.set_leds(move[2] + move[3])

    def castling(self, move:str):
        
        """! @brief     Check move for castling """

        if move == "e1g1" or move == "e1c1" or move == "e8g8" or move == "e8c8":
            return True
        else: 
            return False

    def is_ai_move_done(self, move:str):

        if self.castling(move):

            # Check all 4 castling combinations and confirm the move by returning True
            if (move[2] + move[3]) == "g1":
                if self.board[ord("e")-97][ord("1")-49] == True and \
                   self.board[ord("f")-97][ord("1")-49] == False and \
                   self.board[ord("g")-97][ord("1")-49] == False and \
                   self.board[ord("h")-97][ord("1")-49] == True:
                   return True
            elif (move[2] + move[3]) == "c1":
                if self.board[ord("e")-97][ord("1")-49] == True and \
                   self.board[ord("d")-97][ord("1")-49] == False and \
                   self.board[ord("c")-97][ord("1")-49] == False and \
                   self.board[ord("a")-97][ord("1")-49] == True:
                   return True
            elif (move[2] + move[3]) == "g8":
                if self.board[ord("e")-97][ord("8")-49] == True and \
                   self.board[ord("f")-97][ord("8")-49] == False and \
                   self.board[ord("g")-97][ord("8")-49] == False and \
                   self.board[ord("h")-97][ord("8")-49] == True:
                   return True
            elif (move[2] + move[3]) == "c8":
                if self.board[ord("e")-97][ord("8")-49] == True and \
                   self.board[ord("d")-97][ord("8")-49] == False and \
                   self.board[ord("c")-97][ord("8")-49] == False and \
                   self.board[ord("a")-97][ord("8")-49] == True:
                   return True
            else:
                return False
        else:
            if self.board[ord(move[0]) - 97][ord(move[1]) - 49] == True and self.board[ord(move[2]) - 97][ord(move[3]) - 49] == False:
                return True
            else:
                return False

    def set_leds(self, led:str):

        # Turn off all leds
        port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]

        for char in led:

            if ord('a') <= ord(char) <= ord('h'):
                pin = abs(ord(char) - 97 - 15)
                port[pin] = False
            if ord('A') <= ord(char) <= ord('H'):
                pin = abs(ord(char) - 65 - 15)
                port[pin] = False
            elif ord('1') <= ord(char) <= ord('8'):
                pin = abs(ord(char) - 49 - 7)
                port[pin] = False

        pcf_leds.port = port

    def set_difficulty(self, difficulty):

        led_string = ""

        for i in range(difficulty):
            led_string = led_string + str(i+1)
        
        return led_string

    def display(self):

        # Read all fields
        self.read_fields()

        # Display status of all fields.
        print(f"  a   b   c   d   e   f   g   h    ")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[7] else 'p'} | {' ' if self.b[7] else 'p'} | {' ' if self.c[7] else 'p'} | {' ' if self.d[7] else 'p'} | {' ' if self.e[7] else 'p'} | {' ' if self.f[7] else 'p'} | {' ' if self.g[7] else 'p'} | {' ' if self.h[7] else 'p'} | 8")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[6] else 'p'} | {' ' if self.b[6] else 'p'} | {' ' if self.c[6] else 'p'} | {' ' if self.d[6] else 'p'} | {' ' if self.e[6] else 'p'} | {' ' if self.f[6] else 'p'} | {' ' if self.g[6] else 'p'} | {' ' if self.h[6] else 'p'} | 7")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[5] else 'p'} | {' ' if self.b[5] else 'p'} | {' ' if self.c[5] else 'p'} | {' ' if self.d[5] else 'p'} | {' ' if self.e[5] else 'p'} | {' ' if self.f[5] else 'p'} | {' ' if self.g[5] else 'p'} | {' ' if self.h[5] else 'p'} | 6")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[4] else 'p'} | {' ' if self.b[4] else 'p'} | {' ' if self.c[4] else 'p'} | {' ' if self.d[4] else 'p'} | {' ' if self.e[4] else 'p'} | {' ' if self.f[4] else 'p'} | {' ' if self.g[4] else 'p'} | {' ' if self.h[4] else 'p'} | 5")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[3] else 'p'} | {' ' if self.b[3] else 'p'} | {' ' if self.c[3] else 'p'} | {' ' if self.d[3] else 'p'} | {' ' if self.e[3] else 'p'} | {' ' if self.f[3] else 'p'} | {' ' if self.g[3] else 'p'} | {' ' if self.h[3] else 'p'} | 4")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[2] else 'p'} | {' ' if self.b[2] else 'p'} | {' ' if self.c[2] else 'p'} | {' ' if self.d[2] else 'p'} | {' ' if self.e[2] else 'p'} | {' ' if self.f[2] else 'p'} | {' ' if self.g[2] else 'p'} | {' ' if self.h[2] else 'p'} | 3")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[1] else 'p'} | {' ' if self.b[1] else 'p'} | {' ' if self.c[1] else 'p'} | {' ' if self.d[1] else 'p'} | {' ' if self.e[1] else 'p'} | {' ' if self.f[1] else 'p'} | {' ' if self.g[1] else 'p'} | {' ' if self.h[1] else 'p'} | 2")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[0] else 'p'} | {' ' if self.b[0] else 'p'} | {' ' if self.c[0] else 'p'} | {' ' if self.d[0] else 'p'} | {' ' if self.e[0] else 'p'} | {' ' if self.f[0] else 'p'} | {' ' if self.g[0] else 'p'} | {' ' if self.h[0] else 'p'} | 1")
        print(f"+---+---+---+---+---+---+---+---+  ")


    def menu():

        print("Menu")



class ChessBoardFsm(StateMachine):

    init = State('Init', initial=True)
    difficulty = State('Difficulty')
    setup = State('Setup')
    human_move = State("HumanMove")
    ai_move = State('AIMove')
    undo_move = State('Undo')

    go_to_init = difficulty.to(init) | setup.to(init) | human_move.to(init) | ai_move.to(init)
    go_to_difficulty = init.to(difficulty) | setup.to(difficulty)
    go_to_setup = difficulty.to(setup)
    go_to_ai_move = setup.to(ai_move) | human_move.to(ai_move)
    go_to_human_move = setup.to(human_move) | ai_move.to(human_move)
    go_to_undo_move = human_move.to(undo_move) | ai_move.to(undo_move)

def signal_handler(sig, frame):

    """! @brief    Exit function"""

    print(' SIGINT or CTRL-C detected. Exiting gracefully')
    GPIO.cleanup()
    board.set_leds("")
    ~stockfish
    sys.exit(0)

if __name__ == "__main__":

    # CTRL+C handler
    signal(SIGINT, signal_handler)

    # Create a FSM object
    fsm = ChessBoardFsm()

    # Create a Board object
    board = ChessBoard()

    # Flags & Variables
    initial = True
    first_entry = True
    current_state = None

    move_hint_ai = False
    move_stockfish = ""
    moves = []

    play_difficulty = 3

    stockfish = None

    while True:

        # Set flag if the state has changed
        first_entry = initial or (current_state != fsm.current_state.value)

        # Set the current state
        current_state = fsm.current_state.value

        # STATE: Init the board
        if fsm.is_init:
            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                board.startup_leds()
                board.add_button_events()
                move_hint_ai = False
                move_stockfish = ""
                moves = []

            # Set next state
            fsm.go_to_difficulty()

        # STATE: Difficulty of the AI
        elif fsm.is_difficulty:

            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                board.set_leds(board.set_difficulty(play_difficulty))

            if GPIO.event_detected(MCB_BUT_BLACK):
                
                # Increment difficulty
                if play_difficulty < MCB_PLAY_DIFF_MAX:
                    play_difficulty = play_difficulty + 1
                if DEBUG: print("Difficulty Up")
                board.set_leds(board.set_difficulty(play_difficulty))
            
            if GPIO.event_detected(MCB_BUT_WHITE):

                # Decrement difficulty
                print("Difficulty Down")
                if play_difficulty > MCB_PLAY_DIFF_MIN:
                    play_difficulty = play_difficulty - 1
                board.set_leds(board.set_difficulty(play_difficulty))

            if GPIO.event_detected(MCB_BUT_CONFIRM):
                print(f"Confirm {play_difficulty}")
                board.set_leds("")
                fsm.go_to_setup()
            
            if GPIO.event_detected(MCB_BUT_BACK):
                print("Back")
                fsm.go_to_versus()

        # STATE: Setup
        elif fsm.is_setup:
            
            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                board.read_fields()
                board.display()
                board.add_field_events()

            correct_setup = [False, False, True, True, True, True, False, False]
            setup_leds = ""

            setup_leds = setup_leds + "a" if board.a == correct_setup else setup_leds + ""
            setup_leds = setup_leds + "b" if board.b == correct_setup else setup_leds + ""
            setup_leds = setup_leds + "c" if board.c == correct_setup else setup_leds + ""
            setup_leds = setup_leds + "d" if board.d == correct_setup else setup_leds + ""
            setup_leds = setup_leds + "e" if board.e == correct_setup else setup_leds + ""
            setup_leds = setup_leds + "f" if board.f == correct_setup else setup_leds + ""
            setup_leds = setup_leds + "g" if board.g == correct_setup else setup_leds + ""
            setup_leds = setup_leds + "h" if board.h == correct_setup else setup_leds + ""

            board.set_leds(setup_leds)

            if GPIO.event_detected(MCB_ROW_AB_IO) or GPIO.event_detected(MCB_ROW_CD_IO) or GPIO.event_detected(MCB_ROW_EF_IO) or GPIO.event_detected(MCB_ROW_GH_IO):
                board.read_fields()
                board.display()

            if GPIO.event_detected(MCB_BUT_WHITE):
                print(setup_leds)
                print(f"board.a: {board.a} {board.a == correct_setup}")
                print(f"board.b: {board.b} {board.b == correct_setup}")
                print(f"board.c: {board.c} {board.c == correct_setup}")
                print(f"board.d: {board.d} {board.d == correct_setup}")
                print(f"board.e: {board.e} {board.e == correct_setup}")
                print(f"board.f: {board.f} {board.f == correct_setup}")
                print(f"board.g: {board.g} {board.g == correct_setup}")
                print(f"board.h: {board.h} {board.h == correct_setup}")
                print()

            if GPIO.event_detected(MCB_BUT_CONFIRM) and board.is_setup_done():
                print("Confirm")
                board.set_leds("abcdefgh12345678")
                stockfish = Stockfish("/home/pi/mChessBoard/src/stockfish-rpiz",
                        parameters={
                        "Write Debug Log": "true",
                        "Contempt": 0,
                        "Min Split Depth": 0,
                        "Threads": 2,
                        "Ponder": "false",
                        "Hash": 16,
                        "MultiPV": 1,
                        "Skill Level": play_difficulty,
                        "Move Overhead": 30,
                        "Minimum Thinking Time": 20,
                        "Slow Mover": 80,
                        "UCI_Chess960": "false",
                        }
                        )
                board.set_leds("")

                fsm.go_to_human_move()
            
            if GPIO.event_detected(MCB_BUT_BACK):
                print("Back")
                fsm.go_to_difficulty()

        # STATE: Human Move
        elif fsm.is_human_move:

            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                print(stockfish.get_board_visual())
                #print(board.board)
            
            if GPIO.event_detected(MCB_ROW_AB_IO):
                if DEBUG: print("Event: MCB_ROW_AB_IO")
                board.read_fields()

            if GPIO.event_detected(MCB_ROW_CD_IO):
                if DEBUG: print("Event: MCB_ROW_AB_IO")
                board.read_fields()

            if GPIO.event_detected(MCB_ROW_EF_IO):
                if DEBUG: print("Event: MCB_ROW_AB_IO")
                board.read_fields()

            if GPIO.event_detected(MCB_ROW_GH_IO):
                if DEBUG: print("Event: MCB_ROW_AB_IO")
                board.read_fields()

            if GPIO.event_detected(MCB_BUT_CONFIRM):
                print("Event: Hint or AI move")
                move_stockfish = stockfish.get_best_move()
                if DEBUG: print(move_stockfish[-1])
                if DEBUG: print(moves)
                fsm.go_to_ai_move()

        # STATE: AI Move
        elif fsm.is_ai_move:

            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                timer = time.time()
                toggle = True

            # Show AI move
            board.hint_ai_move(toggle, move_stockfish)

            # Handle the led flash indicator timing
            if time.time() > timer + MCB_PLAY_AI_LED_TOGGLE_TIME:
                toggle = not toggle
                timer = time.time()

            # Confirm AI/hint move
            if GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE):
                print("Confirm AI move")
                board.hint_ai_move_done(move_stockfish)
                if DEBUG: board.display()
                if board.is_ai_move_done(move_stockfish):
                    if stockfish.is_move_correct(move_stockfish):
                        moves.append(move_stockfish)
                        stockfish.set_position(moves)
                        move_stockfish = ""
                        fsm.go_to_human_move()

        # Reset
        if not GPIO.input(MCB_BUT_WHITE) and not GPIO.input(MCB_BUT_BLACK) and not GPIO.input(MCB_BUT_CONFIRM) and not GPIO.input(MCB_BUT_BACK):
            print("Resetting")
            board.remove_button_events()
            board.remove_field_events()
            fsm.go_to_init()

        # Not initial anymore
        initial = False
