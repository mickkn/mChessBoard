import argparse
import time
from signal import signal, SIGINT
import sys
import RPi.GPIO as GPIO

from statemachine import StateMachine, State
from stockfish import Stockfish  # https://pypi.org/project/stockfish/
from pcf8575 import PCF8575  # https://pypi.org/project/pcf8575/

APP_TITLE = "mChessBoard"
AUTHOR = "by Mick Kirkegaard"
VERSION = "v1.0.0"
DATE = "Jan 01 2021 19:01"

"""! @brief     Play defines """
MCB_PLAY_DIFF_MAX = 8
MCB_PLAY_DIFF_MIN = 0
MCB_PLAY_AI_LED_TOGGLE_TIME = 0.5  # sec
MCB_PLAY_CHECKMATE_LED_TOGGLE_TIME = 0.2  # sec

"""! @brief     Board defines """
MCB_I2C_PORT_NUM = 1
MCB_I2C_ROW_AB_ADDRESS = 0x23
MCB_I2C_ROW_CD_ADDRESS = 0x22
MCB_I2C_ROW_EF_ADDRESS = 0x21
MCB_I2C_ROW_GH_ADDRESS = 0x20
MCB_I2C_LEDS_ADDRESS = 0x24

MCB_BUT_WHITE = 17  # Closest to WHITE side
MCB_BUT_CONFIRM = 27  # Middle close to WHITE side
MCB_BUT_BACK = 23  # Middle close to BLACK side
MCB_BUT_BLACK = 22  # Closest to BLACK side
MCB_BUT_DEBOUNCE = 150  # Button debounce
MCB_FIELD_DEBOUNCE = 50  # Field debounce

"""! @brief     Board fields and leds"""
pcf_row_ab = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_AB_ADDRESS)
pcf_row_cd = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_CD_ADDRESS)
pcf_row_ef = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_EF_ADDRESS)
pcf_row_gh = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_GH_ADDRESS)
pcf_leds = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_LEDS_ADDRESS)

MCB_ROW_AB_IO = 6
MCB_ROW_CD_IO = 13
MCB_ROW_EF_IO = 19
MCB_ROW_GH_IO = 26

"""! @brief     Global variables """


def parser():
    """! @brief     Parser function to get all the arguments """

    # Description string
    description = "Description: " + APP_TITLE + " " + VERSION + " " + DATE + " " + AUTHOR

    # Construct the argument parse and return the arguments
    args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=description)

    args.add_argument("-i", "--input", type=str, default="/home/pi/mChessBoard/src/minic_3.04_linux_x32_armv6",
                        help="path to ai engine")
    args.add_argument("-d", "--debug", action='store_true',
                        help="debug printout")
    args.add_argument("-a", "--auto_confirm", action='store_true',
                        help="auto confirm movement of pieces")
    args.add_argument('--version', action='version', version=APP_TITLE + " " + VERSION + " " + DATE + " " + AUTHOR)

    print('\n' + str(args.parse_args()) + '\n')

    return args.parse_args()


class ChessBoard(StateMachine):

    def __init__(self):

        """! Init the board """
        
        # Initialize all fields to False
        default = [False] * 8
        self.a = self.b = self.c = self.d = self.e = self.f = self.g = self.h = default
        
        # Declare board 2D lists
        self.board_current = [self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h]
        self.board_prev = self.board_current
        self.board_undo = [self.board_current]

        # Default board setup (False == Place piece)
        self.setup = [False, False, True, True, True, True, False, False]
        self.board_setup = [self.setup] * 8

        # Set all inputs high on init
        pcf_row_ab.port = pcf_row_cd.port = pcf_row_ef.port = pcf_row_gh.port = [True] * 16

        # Setup GPIO pin mode
        GPIO.setmode(GPIO.BCM)

        # Init buttons pin mode
        GPIO.setup(MCB_BUT_WHITE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(MCB_BUT_CONFIRM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(MCB_BUT_BACK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(MCB_BUT_BLACK, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Init fields pin mode
        GPIO.setup(MCB_ROW_AB_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(MCB_ROW_CD_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(MCB_ROW_EF_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(MCB_ROW_GH_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def add_button_events(self):

        """! Add events to all buttons """
        
        # Remove the events before adding them again
        self.remove_button_events()

        # Small delay
        time.sleep(0.5)

        # Add button events
        GPIO.add_event_detect(MCB_BUT_WHITE, GPIO.FALLING, bouncetime=MCB_BUT_DEBOUNCE)
        GPIO.add_event_detect(MCB_BUT_CONFIRM, GPIO.FALLING, bouncetime=MCB_BUT_DEBOUNCE)
        GPIO.add_event_detect(MCB_BUT_BACK, GPIO.FALLING, bouncetime=MCB_BUT_DEBOUNCE)
        GPIO.add_event_detect(MCB_BUT_BLACK, GPIO.FALLING, bouncetime=MCB_BUT_DEBOUNCE)

    def remove_button_events(self):

        """! Remove events from all buttons """

        GPIO.remove_event_detect(MCB_BUT_WHITE)
        GPIO.remove_event_detect(MCB_BUT_CONFIRM)
        GPIO.remove_event_detect(MCB_BUT_BACK)
        GPIO.remove_event_detect(MCB_BUT_BLACK)

    def add_field_events(self):

        """! Add events to all chess fields """

        # Remove the events before adding them again
        self.remove_field_events()

        # Add field events
        GPIO.add_event_detect(MCB_ROW_AB_IO, GPIO.FALLING, bouncetime=MCB_FIELD_DEBOUNCE)
        GPIO.add_event_detect(MCB_ROW_CD_IO, GPIO.FALLING, bouncetime=MCB_FIELD_DEBOUNCE)
        GPIO.add_event_detect(MCB_ROW_EF_IO, GPIO.FALLING, bouncetime=MCB_FIELD_DEBOUNCE)
        GPIO.add_event_detect(MCB_ROW_GH_IO, GPIO.FALLING, bouncetime=MCB_FIELD_DEBOUNCE)

    def remove_field_events(self):

        """! Remove events from all chess fields """

        GPIO.remove_event_detect(MCB_ROW_AB_IO)
        GPIO.remove_event_detect(MCB_ROW_CD_IO)
        GPIO.remove_event_detect(MCB_ROW_EF_IO)
        GPIO.remove_event_detect(MCB_ROW_GH_IO)

    def startup_leds(self, delay):

        def dance_out():
            self.set_leds("45")
            time.sleep(delay)
            self.set_leds("3456")
            time.sleep(delay)
            self.set_leds("234567")
            time.sleep(delay)
            self.set_leds("12345678")
            time.sleep(delay)
            self.set_leds("12345678a")
            time.sleep(delay)
            self.set_leds("12345678ab")
            time.sleep(delay)
            self.set_leds("12345678abc")
            time.sleep(delay)
            self.set_leds("12345678abcd")
            time.sleep(delay)
            self.set_leds("12345678abcde")
            time.sleep(delay)
            self.set_leds("12345678abcdef")
            time.sleep(delay)
            self.set_leds("12345678abcdefg")
            time.sleep(delay)
            self.set_leds("12345678abcdefgh")
            time.sleep(delay)
            time.sleep(delay)

        def dance_in():
            self.set_leds("12345678abcdefg")
            time.sleep(delay)
            self.set_leds("12345678abcdef")
            time.sleep(delay)
            self.set_leds("12345678abcde")
            time.sleep(delay)
            self.set_leds("12345678abcd")
            time.sleep(delay)
            self.set_leds("12345678abc")
            time.sleep(delay)
            self.set_leds("12345678ab")
            time.sleep(delay)
            self.set_leds("12345678a")
            time.sleep(delay)
            self.set_leds("12345678")
            time.sleep(delay)
            self.set_leds("234567")
            time.sleep(delay)
            self.set_leds("3456")
            time.sleep(delay)
            self.set_leds("45")
            time.sleep(delay)
            self.set_leds("")
            time.sleep(delay)

        dance_out()
        dance_in()
        dance_out()
        dance_in()

    def read_fields(self):

        """! Read all the chess fields """

        # Read the PCF8575 boards (this is done with the assumption that a1 = p00 etc. reason for reversion)
        self.a = [i for i in pcf_row_ab.port][8:][::-1]
        self.b = [i for i in pcf_row_ab.port][:8][::-1]
        self.c = [i for i in pcf_row_cd.port][8:][::-1]
        self.d = [i for i in pcf_row_cd.port][:8][::-1]
        self.e = [i for i in pcf_row_ef.port][8:][::-1]
        self.f = [i for i in pcf_row_ef.port][:8][::-1]
        self.g = [i for i in pcf_row_gh.port][8:][::-1]
        self.h = [i for i in pcf_row_gh.port][:8][::-1]

        # Update current board
        self.board_current = [self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h]

    def get_field_event(self):

        """! Determine what happends on the field
        
        @return changed field value
        """

        # Read the fields
        self.read_fields()

        # Init return value
        field_value = ""

        # Determine what field changed based on board vs prev board
        for letter in range(8):
            for digit in range(8):
                #if args.debug: print(f"self.board_current[letter][digit]: {self.board_current[letter][digit]}")
                #if args.debug: print(f"self.board_prev[letter][digit]: {self.board_prev[letter][digit]}")
                if self.board_current[letter][digit] != self.board_prev[letter][digit]:
                    # Safe the last analysed changed field
                    field_value = chr(letter + 97) + chr(digit + 49)
                    if args.debug: print(f"Field changed: {field_value} [{self.board_current[letter][digit]}]")

        if field_value != "":
            board.board_prev = board.board_current

        return field_value

    def set_move_led(self, toggle: bool, move: str):

        """! Indicate the given move with leds """

        if toggle:
            self.set_leds(move[0] + move[1])
        else:
            self.set_leds(move[0] + move[1] + move[2] + move[3])

    def set_move_done_leds(self, move: str):

        """! Set leds when move is done """

        if len(move) == 4:
            self.set_leds(move[2] + move[3])

    def is_castling(self, move: str, moves: list):

        """! @brief     Check move for castling 
        
        @param move     The current move to check
        @param moves    List of moves done so far to determine if a King has been moved
        @return         True if castling
        """

        black = True
        white = True

        # If any king has moved in the past, it is not a castle, this is in a 
        # scenario where a piece moves e.g. e1g1 and is not the king, 
        # then it is not a castle
        for m in moves:
            if (m[0] + m[1]) == "e1":
                white = False
            if (m[0] + m[1]) == "e8":
                black = False

        # Determine a castle move and return
        if (move == "e1g1" or move == "e1c1" and white) or (move == "e8g8" or move == "e8c8" and black):
            return True
        
        # Else just return False
        return False

    def is_undo_move_done(self):

        """! Function to determ if the undo move is done
        
        @param move     The current move to check
        @param moves    List of moves done so far, for castling check
        """

        # Read board
        self.read_fields()

        # Check if it match the last move in history
        if self.board_prev == self.board_undo[-1]:
            if args.debug: print("self.board_current == self.board_undo[-1]")
            
            # Update undo history
            del self.board_undo[-1]

            # Update prev status
            if len(self.board_undo) > 0:
                self.board_prev = self.board_undo[-1]
            else:
                self.board_prev = self.board_current
            
            return True

        for i in range(8):
            if args.debug: print(f"self.board_current : {self.board_current[i]}")
            if args.debug: print(f"self.board_undo[-1]: {self.board_undo[-1][i]}")

        return False
                


    def is_move_done(self, move: str, moves: list):

        """! Function to determ if a move is done
        
        @param move     The current move to check
        @param moves    List of moves done so far, for castling check
        """

        # A move can only be "done" if the there is 4 chars
        if len(move) == 4:

            # Check if the move is a castling
            if self.is_castling(move, moves):

                # Check for all 4 castling combinations and confirm the move by returning True
                if (move[2] + move[3]) == "g1":
                    if self.board_current[ord("e") - 97][ord("1") - 49] and \
                       not self.board_current[ord("f") - 97][ord("1") - 49] and \
                       not self.board_current[ord("g") - 97][ord("1") - 49] and \
                       self.board_current[ord("h") - 97][ord("1") - 49]:
                        return True
                elif (move[2] + move[3]) == "c1":
                    if self.board_current[ord("e") - 97][ord("1") - 49] and \
                       not self.board_current[ord("d") - 97][ord("1") - 49] and \
                       not self.board_current[ord("c") - 97][ord("1") - 49] and \
                       self.board_current[ord("a") - 97][ord("1") - 49]:
                        return True
                elif (move[2] + move[3]) == "g8":
                    if self.board_current[ord("e") - 97][ord("8") - 49] and \
                       not self.board_current[ord("f") - 97][ord("8") - 49] and \
                       not self.board_current[ord("g") - 97][ord("8") - 49] and \
                       self.board_current[ord("h") - 97][ord("8") - 49]:
                        return True
                elif (move[2] + move[3]) == "c8":
                    if self.board_current[ord("e") - 97][ord("8") - 49] and \
                       not self.board_current[ord("d") - 97][ord("8") - 49] and \
                       not self.board_current[ord("c") - 97][ord("8") - 49] and \
                       self.board_current[ord("a") - 97][ord("8") - 49]:
                        return True
            else:
                if self.board_current[ord(move[0]) - 97][ord(move[1]) - 49] == True and \
                   self.board_current[ord(move[2]) - 97][ord(move[3]) - 49] == False:
                    return True

        return False

    def set_setup_leds(self):

        """! Setup/missing piece led indicators """

        # Read all fields
        self.read_fields()

        # Declare a string for holding the chars to indicate which a-h rows are missing a piece
        setup_leds = ""
        setup_leds = setup_leds + "a" if board.a == board.setup else setup_leds.replace("a", "")
        setup_leds = setup_leds + "b" if board.b == board.setup else setup_leds.replace("b", "")
        setup_leds = setup_leds + "c" if board.c == board.setup else setup_leds.replace("c", "")
        setup_leds = setup_leds + "d" if board.d == board.setup else setup_leds.replace("d", "")
        setup_leds = setup_leds + "e" if board.e == board.setup else setup_leds.replace("e", "")
        setup_leds = setup_leds + "f" if board.f == board.setup else setup_leds.replace("f", "")
        setup_leds = setup_leds + "g" if board.g == board.setup else setup_leds.replace("g", "")
        setup_leds = setup_leds + "h" if board.h == board.setup else setup_leds.replace("h", "")
        board.set_leds(setup_leds)

    def set_leds(self, led: str):

        """! Led indicators 
        
        @param led      The chars to light up
        """

        # Set all leds to off
        port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]

        # If char(s) are given, setup the port
        if len(led) > 0:
            for char in led:

                # ASCII to decimal-index convertion
                if ord('a') <= ord(char) <= ord('h'):
                    pin = abs(ord(char) - 97 - 15)
                    port[pin] = False
                if ord('A') <= ord(char) <= ord('H'):
                    pin = abs(ord(char) - 65 - 15)
                    port[pin] = False
                elif ord('1') <= ord(char) <= ord('8'):
                    pin = abs(ord(char) - 49 - 7)
                    port[pin] = False

        # Finally set the leds
        pcf_leds.port = port

    def set_difficulty_leds(self, difficulty: int):

        """! Difficulty led indicator 
        
        @param difficulty   Difficulty number
        """

        led_string = ""

        for i in range(difficulty):
            led_string = led_string + str(i + 1)

        self.set_leds(led_string)

    def display(self):

        """! Debug function to display the state of the fields in terminal """

        # Read all fields
        self.read_fields()

        # Display status of all fields.
        print(f"  a   b   c   d   e   f   g   h    ")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[7] else 'x'} | {' ' if self.b[7] else 'x'} | {' ' if self.c[7] else 'x'} | {' ' if self.d[7] else 'x'} | {' ' if self.e[7] else 'x'} | {' ' if self.f[7] else 'x'} | {' ' if self.g[7] else 'x'} | {' ' if self.h[7] else 'x'} | 8")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[6] else 'x'} | {' ' if self.b[6] else 'x'} | {' ' if self.c[6] else 'x'} | {' ' if self.d[6] else 'x'} | {' ' if self.e[6] else 'x'} | {' ' if self.f[6] else 'x'} | {' ' if self.g[6] else 'x'} | {' ' if self.h[6] else 'x'} | 7")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[5] else 'x'} | {' ' if self.b[5] else 'x'} | {' ' if self.c[5] else 'x'} | {' ' if self.d[5] else 'x'} | {' ' if self.e[5] else 'x'} | {' ' if self.f[5] else 'x'} | {' ' if self.g[5] else 'x'} | {' ' if self.h[5] else 'x'} | 6")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[4] else 'x'} | {' ' if self.b[4] else 'x'} | {' ' if self.c[4] else 'x'} | {' ' if self.d[4] else 'x'} | {' ' if self.e[4] else 'x'} | {' ' if self.f[4] else 'x'} | {' ' if self.g[4] else 'x'} | {' ' if self.h[4] else 'x'} | 5")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[3] else 'x'} | {' ' if self.b[3] else 'x'} | {' ' if self.c[3] else 'x'} | {' ' if self.d[3] else 'x'} | {' ' if self.e[3] else 'x'} | {' ' if self.f[3] else 'x'} | {' ' if self.g[3] else 'x'} | {' ' if self.h[3] else 'x'} | 4")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[2] else 'x'} | {' ' if self.b[2] else 'x'} | {' ' if self.c[2] else 'x'} | {' ' if self.d[2] else 'x'} | {' ' if self.e[2] else 'x'} | {' ' if self.f[2] else 'x'} | {' ' if self.g[2] else 'x'} | {' ' if self.h[2] else 'x'} | 3")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[1] else 'x'} | {' ' if self.b[1] else 'x'} | {' ' if self.c[1] else 'x'} | {' ' if self.d[1] else 'x'} | {' ' if self.e[1] else 'x'} | {' ' if self.f[1] else 'x'} | {' ' if self.g[1] else 'x'} | {' ' if self.h[1] else 'x'} | 2")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {' ' if self.a[0] else 'x'} | {' ' if self.b[0] else 'x'} | {' ' if self.c[0] else 'x'} | {' ' if self.d[0] else 'x'} | {' ' if self.e[0] else 'x'} | {' ' if self.f[0] else 'x'} | {' ' if self.g[0] else 'x'} | {' ' if self.h[0] else 'x'} | 1")
        print(f"+---+---+---+---+---+---+---+---+  ")

    def full_display(self, sf):

        """! Debug function to display the state of the fields in terminal """

        # Read all fields
        self.read_fields()

        sf = sf.replace('\r', "").replace("\n", "")

        # Display status of all fields.
        #print(f"  a   b   c   d   e   f   g   h    ")
        print(f"          SENSOR BOARD                         STOCKFISH BOARD")
        print(f"+---+---+---+---+---+---+---+---+     {sf[0:33]}")
        print(f"| {' ' if self.a[7] else 'x'} | {' ' if self.b[7] else 'x'} | {' ' if self.c[7] else 'x'} | {' ' if self.d[7] else 'x'} | {' ' if self.e[7] else 'x'} | {' ' if self.f[7] else 'x'} | {' ' if self.g[7] else 'x'} | {' ' if self.h[7] else 'x'} | 8   {sf[33:68]}")
        print(f"+---+---+---+---+---+---+---+---+     {sf[68:101]}")
        print(f"| {' ' if self.a[6] else 'x'} | {' ' if self.b[6] else 'x'} | {' ' if self.c[6] else 'x'} | {' ' if self.d[6] else 'x'} | {' ' if self.e[6] else 'x'} | {' ' if self.f[6] else 'x'} | {' ' if self.g[6] else 'x'} | {' ' if self.h[6] else 'x'} | 7   {sf[101:136]}")
        print(f"+---+---+---+---+---+---+---+---+     {sf[136:169]}")
        print(f"| {' ' if self.a[5] else 'x'} | {' ' if self.b[5] else 'x'} | {' ' if self.c[5] else 'x'} | {' ' if self.d[5] else 'x'} | {' ' if self.e[5] else 'x'} | {' ' if self.f[5] else 'x'} | {' ' if self.g[5] else 'x'} | {' ' if self.h[5] else 'x'} | 6   {sf[169:204]}")
        print(f"+---+---+---+---+---+---+---+---+     {sf[204:237]}")
        print(f"| {' ' if self.a[4] else 'x'} | {' ' if self.b[4] else 'x'} | {' ' if self.c[4] else 'x'} | {' ' if self.d[4] else 'x'} | {' ' if self.e[4] else 'x'} | {' ' if self.f[4] else 'x'} | {' ' if self.g[4] else 'x'} | {' ' if self.h[4] else 'x'} | 5   {sf[237:272]}")
        print(f"+---+---+---+---+---+---+---+---+     {sf[272:305]}")
        print(f"| {' ' if self.a[3] else 'x'} | {' ' if self.b[3] else 'x'} | {' ' if self.c[3] else 'x'} | {' ' if self.d[3] else 'x'} | {' ' if self.e[3] else 'x'} | {' ' if self.f[3] else 'x'} | {' ' if self.g[3] else 'x'} | {' ' if self.h[3] else 'x'} | 4   {sf[305:340]}")
        print(f"+---+---+---+---+---+---+---+---+     {sf[340:373]}")
        print(f"| {' ' if self.a[2] else 'x'} | {' ' if self.b[2] else 'x'} | {' ' if self.c[2] else 'x'} | {' ' if self.d[2] else 'x'} | {' ' if self.e[2] else 'x'} | {' ' if self.f[2] else 'x'} | {' ' if self.g[2] else 'x'} | {' ' if self.h[2] else 'x'} | 3   {sf[373:408]}")
        print(f"+---+---+---+---+---+---+---+---+     {sf[408:441]}")
        print(f"| {' ' if self.a[1] else 'x'} | {' ' if self.b[1] else 'x'} | {' ' if self.c[1] else 'x'} | {' ' if self.d[1] else 'x'} | {' ' if self.e[1] else 'x'} | {' ' if self.f[1] else 'x'} | {' ' if self.g[1] else 'x'} | {' ' if self.h[1] else 'x'} | 2   {sf[441:476]}")
        print(f"+---+---+---+---+---+---+---+---+     {sf[476:509]}")
        print(f"| {' ' if self.a[0] else 'x'} | {' ' if self.b[0] else 'x'} | {' ' if self.c[0] else 'x'} | {' ' if self.d[0] else 'x'} | {' ' if self.e[0] else 'x'} | {' ' if self.f[0] else 'x'} | {' ' if self.g[0] else 'x'} | {' ' if self.h[0] else 'x'} | 1   {sf[509:544]}")
        print(f"+---+---+---+---+---+---+---+---+     {sf[544:577]}")

class ChessBoardFsm(StateMachine):

    # Initialize the states
    init = State('Init', initial=True)
    difficulty = State('Difficulty')
    setup = State('Setup')
    human_move = State("HumanMove")
    ai_move = State('AIMove')
    checkmate = State("Checkmate")
    pawn_promotion = State("PawnPromotion")
    undo_move = State('Undo')

    # Initialize all transitions allowed
    go_to_init = difficulty.to(init) | setup.to(init) | human_move.to(init) | ai_move.to(init) | checkmate.to(init) | undo_move.to(init)
    go_to_difficulty = init.to(difficulty) | setup.to(difficulty)
    go_to_setup = difficulty.to(setup) | init.to(setup)
    go_to_ai_move = setup.to(ai_move) | human_move.to(ai_move) | pawn_promotion.to(ai_move)
    go_to_human_move = setup.to(human_move) | ai_move.to(human_move) | undo_move.to(human_move) | pawn_promotion.to(human_move)
    go_to_checkmate = human_move.to(checkmate) | ai_move.to(checkmate)
    go_to_pawn_promotion = human_move.to(pawn_promotion) | ai_move.to(pawn_promotion)
    go_to_undo_move = human_move.to(undo_move) | ai_move.to(undo_move)

def signal_handler(sig, frame):

    """! @brief    Exit function"""

    print(' SIGINT or CTRL-C detected. Exiting gracefully')
    GPIO.cleanup()
    board.set_leds("")
    sys.exit(0)

if __name__ == "__main__":

    """! @brief    Main function """

    # CTRL+C handler
    signal(SIGINT, signal_handler)

    # Create a FSM object
    fsm = ChessBoardFsm()

    # Create a Board object
    board = ChessBoard()

    # Parse arguments
    args = parser()

    

    # Flags & Variables
    initial = True
    first_entry = True
    prev_state = None
    current_state = None

    # Movement global variables and flags
    move_ai = ""           ### Move made by Engine
    move_human = ""         ### Move made by Human
    move_undo = ""          ### Move made by Undo
    moves = []              ### List of moves for engine
    play_difficulty = 1     ### Default difficulty

    # Evaluation Engine Setup
    stockfish = None
    stockfish_param = {}

    # AI Engine setup
    ai = None
    ai_parameters = {}

    # Main loop
    while True:

        # Set flag if the state has changed
        first_entry = initial or (current_state != fsm.current_state)

        if first_entry:
            prev_state = current_state
            current_state = fsm.current_state    

        # STATE: Init the board
        if fsm.is_init:
            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                # Reset AI move instance
                move_ai = ""
                # Reset Human move instance
                move_human = ""
                # Reset moves list
                moves = []
                # Add button events (delays the setup init)
                board.add_button_events()
                # Let the LED's dance
                board.startup_leds(0.05)
                # Reset undo history
                board.board_undo = []

            # Set next state
            fsm.go_to_difficulty()

        # STATE: Difficulty of AI
        elif fsm.is_difficulty:

            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                # Set LED's to default difficulty
                board.set_difficulty_leds(play_difficulty)
            
            elif GPIO.event_detected(MCB_BUT_CONFIRM):

                print(f"Confirm {play_difficulty}")

                board.set_leds("12345678abcdefgh")

                if "stockfish" in args.input:

                    print("Using Stockfish Engine")
                    
                    if play_difficulty <= 2:
                        if args.debug: print(f"Using Skill Level: {play_difficulty}")
                        ai_parameters.update({"UCI_LimitStrength": "false"})
                        ai_parameters.update({"Skill Level": play_difficulty})
                    else:
                        if args.debug: print(f"Using ELO rating: {play_difficulty * 50 + 1250}")
                        ai_parameters.update({"UCI_LimitStrength": "true"})
                        ai_parameters.update({"UCI_Elo": play_difficulty * 50 + 1200})       # 1350 to 2850 (limit here is 1600, enough for me)
                    
                    # Initiate stockfish engine
                    #uci = Stockfish(args.input, parameters=uci_parameters)
                    #uci.set_depth(1)
                    #if args.debug: print(uci.get_parameters())
                    
                    
                
                elif "minic" in args.input:
                    
                    print("Using Minic Engine")

                    if play_difficulty == 0:
                        if args.debug: print(f"Using Level: {play_difficulty}")
                        ai_parameters.update({"UCI_LimitStrength": "false"})
                        ai_parameters.update({"Level": play_difficulty})
                    else:
                        if args.debug: print(f"Using ELO rating: {play_difficulty * 100 + 400}")
                        ai_parameters.update({"UCI_LimitStrength": "true"})
                        ai_parameters.update({"UCI_Elo": play_difficulty * 100 + 400})       # 500 to 2800 (limit here is 1300, enough for me)

                    # Initiate ai engine
                    ai = Stockfish(args.input, parameters=ai_parameters)
                    if args.debug: print(ai.get_parameters())

                    # Init. eval engine
                    stockfish = Stockfish("/home/pi/mChessBoard/src/stockfish-12_linux_x32_armv6", parameters=ai_parameters)

                else:

                    print("Unknown engine")

                board.set_leds("")
                
                fsm.go_to_setup()

            elif GPIO.event_detected(MCB_BUT_BLACK):

                # Increment difficulty
                if play_difficulty < MCB_PLAY_DIFF_MAX:
                    play_difficulty = play_difficulty + 1
                if args.debug: print(f"Difficulty Up: {play_difficulty}")
                board.set_difficulty_leds(play_difficulty)

            elif GPIO.event_detected(MCB_BUT_WHITE):

                # Decrement difficulty
                if play_difficulty > MCB_PLAY_DIFF_MIN:
                    play_difficulty = play_difficulty - 1
                if args.debug: print(f"Difficulty Down: {play_difficulty}")
                board.set_difficulty_leds(play_difficulty)

        # STATE: Setup
        elif fsm.is_setup:

            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                board.add_button_events()
                board.add_field_events()
                board.set_setup_leds()

            elif GPIO.event_detected(MCB_ROW_AB_IO) or \
                 GPIO.event_detected(MCB_ROW_CD_IO) or \
                 GPIO.event_detected(MCB_ROW_EF_IO) or \
                 GPIO.event_detected(MCB_ROW_GH_IO):
                board.set_setup_leds()

            elif board.board_current == board.board_setup:
                print("Board is set up")
                # Setup board
                board.set_leds("abcdefgh12345678")
                board.board_prev = board.board_current
                time.sleep(1)
                board.set_leds("")
                board.remove_field_events()
                fsm.go_to_human_move()

            elif GPIO.event_detected(MCB_BUT_BACK):
                print("Back")
                fsm.go_to_difficulty()

        # STATE: Human Move
        elif fsm.is_human_move:

            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                board.add_field_events()
                human_move_field = ""
                toggle = False
                timer = time.time()

            if len(move_human) == 4:
                board.set_move_led(toggle, move_human)
                # Handle the led flash indicator timing
                if time.time() > timer + MCB_PLAY_AI_LED_TOGGLE_TIME:
                    toggle = not toggle
                    timer = time.time()

            # Handle move on board
            if GPIO.event_detected(MCB_ROW_AB_IO) or \
               GPIO.event_detected(MCB_ROW_CD_IO) or \
               GPIO.event_detected(MCB_ROW_EF_IO) or \
               GPIO.event_detected(MCB_ROW_GH_IO):
                
                # Get the field event
                human_move_field = board.get_field_event()
                if args.debug: print(f"Event: Field changed {human_move_field}")

                # If first event and not an empty event
                if len(move_human) == 0 and human_move_field != "":
                    # Set the single field led
                    board.set_leds(human_move_field)
                    move_human = human_move_field
                # Else if second event and not the same field
                elif len(move_human) == 2 and human_move_field != "" and human_move_field != move_human:
                    # Save a opposite representation
                    move_human_opposite = human_move_field + move_human
                    # Add the new field to the human move
                    move_human += human_move_field
                    # Take a time stamp
                    timer = time.time()
                    # Check for correctness (could be pawn promotion)
                    if stockfish.is_move_correct(move_human) or ai.is_move_correct(move_human+'q'):
                        move_human = move_human
                    # Check for correctness opposite if fields are obtained in opposite direction (could be pawn promotion)
                    elif stockfish.is_move_correct(move_human_opposite) or stockfish.is_move_correct(move_human_opposite+'q'):
                        move_human = move_human_opposite
                    else:
                        move_human = ""
                        board.set_leds("")
                
                if args.debug: print(f"humanmove: {move_human}")

            # If black or white is pressed
            elif (GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE) or args.auto_confirm) and len(move_human) == 4:
                print(f"Event: Confirm human move: {move_human}")
                board.read_fields()
                if board.is_move_done(move_human, moves):
                    if stockfish.is_move_correct(move_human):
                        moves.append(move_human)
                        stockfish.set_position(moves)
                        ai.set_position(moves)
                        board.set_move_done_leds(move_human)
                        move_human = ""
                        if args.debug: board.full_display(stockfish.get_board_visual())
                        if stockfish.get_evaluation() == {"type": "mate", "value": 0}:
                            fsm.go_to_checkmate()
                        board.board_undo.append(board.board_current)
                        
                    elif stockfish.is_move_correct(move_human+'q'):
                        fsm.go_to_pawn_promotion()
                else:
                    # Something is wrong reset move
                    #move_human = ""
                    if args.debug: board.display()

            # Is confirm pressed?
            elif GPIO.event_detected(MCB_BUT_CONFIRM):
                print("Event: Hint or AI move")
                board.remove_field_events()
                move_ai = ai.get_best_move()
                fsm.go_to_ai_move()

            elif GPIO.event_detected(MCB_BUT_BACK):
                print("Event: Undo")
                if args.debug: board.full_display(stockfish.get_board_visual())
                fsm.go_to_undo_move()

        # STATE: AI Move
        elif fsm.is_ai_move:

            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                timer = time.time()
                toggle = True

            # Handle the led flash indicator timing
            if time.time() > timer + MCB_PLAY_AI_LED_TOGGLE_TIME:
                toggle = not toggle
                board.set_move_led(toggle, move_ai)
                timer = time.time()

            # Confirm AI/hint move
            if GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE):
                print(f"Confirm AI move: {move_ai}")
                board.read_fields()
                if board.is_move_done(move_ai, moves):
                    board.board_prev = board.board_current
                    if stockfish.is_move_correct(move_ai):
                        moves.append(move_ai)
                        stockfish.set_position(moves)
                        ai.set_position(moves)
                        board.set_move_done_leds(move_ai)
                        move_ai = ""
                        if args.debug: board.full_display(stockfish.get_board_visual())
                        if stockfish.get_evaluation() == {"type": "mate", "value": 0}:
                            fsm.go_to_checkmate()
                        else:
                            fsm.go_to_human_move()
                        board.board_undo.append(board.board_current)
                else:
                    if args.debug: board.display()

            elif GPIO.event_detected(MCB_BUT_BACK):
                print("Event: Undo")
                fsm.go_to_undo_move()

        elif fsm.is_pawn_promotion:

            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                print(prev_state)
                if prev_state.value == 'human_move':
                    print("From Human")
                elif prev_state.value == 'ai_move':
                    print("From AI")
                
            

            # Handle human (Human makes a choice)

            # Handle AI (AI shows what piece is chosen)

        # STATE: Undo move
        elif fsm.is_undo_move:

            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
                timer = time.time()
                toggle = True
                if len(moves) > 0:
                    if len(moves[-1]) == 4:
                        move_undo = moves[-1][2] + moves[-1][3] + moves[-1][0] + moves[-1][1]
                    else:
                        board.set_move_done_leds(moves[-1])
                        move_human = ""
                        move_ai = ""
                        fsm.go_to_human_move()
                else:
                    board.set_leds("")
                    move_human = ""
                    move_ai = ""
                    fsm.go_to_human_move()

            # Handle the led flash indicator timing
            if time.time() > timer + MCB_PLAY_AI_LED_TOGGLE_TIME and len(move_undo) == 4:
                toggle = not toggle
                board.set_move_led(toggle, move_undo)
                timer = time.time()
          
            # Confirm Undo move
            if GPIO.event_detected(MCB_BUT_BLACK) or GPIO.event_detected(MCB_BUT_WHITE):
                print(f"Confirm Undo move: {move_undo}")
                if board.is_undo_move_done():
                    move_undo = ""
                    del moves[-1]
                    stockfish.set_position(moves)
                    ai.set_position(moves)
                    if len(moves) > 0: 
                        board.set_move_done_leds(moves[-1])
                    else:
                        board.set_leds("")
                    if args.debug: board.full_display(stockfish.get_board_visual())
                    fsm.go_to_human_move()
                else:
                    if args.debug: board.display()

            elif GPIO.event_detected(MCB_BUT_BACK):
                print("Event: Cancel Undo")
                fsm.go_to_human_move()

        # STATE: Checkmate
        elif fsm.is_checkmate:

            if first_entry:
                print(f"State: {fsm.current_state.identifier}")
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

                print("Go to init")
                board.remove_button_events()
                board.remove_field_events()
                fsm.go_to_init()

        # Reset (all buttons pressed)
        if not GPIO.input(MCB_BUT_WHITE) and \
           not GPIO.input(MCB_BUT_BLACK) and \
           not GPIO.input(MCB_BUT_CONFIRM) and \
           not GPIO.input(MCB_BUT_BACK):

            print("Resetting")
            board.set_leds("abcdefgh12345678")
            board.remove_button_events()
            board.remove_field_events()
            time.sleep(2)
            fsm.go_to_init()

        # Not initial anymore
        initial = False
