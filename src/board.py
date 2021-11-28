"""
    This module implements mchessboard hardware layer.

    :author: Mick Kirkegaard.
"""

from pcf8575 import PCF8575  # https://pypi.org/project/pcf8575/
import RPi.GPIO as GPIO
import config as cfg
import time


class Board():

    def __init__(self, args: []):

        """
        Init. board fields and led drivers
        """

        self.args = args

        self.pcf_row_ab = PCF8575(cfg.MCB_I2C_PORT_NUM, cfg.MCB_I2C_ROW_AB_ADDRESS)
        self.pcf_row_cd = PCF8575(cfg.MCB_I2C_PORT_NUM, cfg.MCB_I2C_ROW_CD_ADDRESS)
        self.pcf_row_ef = PCF8575(cfg.MCB_I2C_PORT_NUM, cfg.MCB_I2C_ROW_EF_ADDRESS)
        self.pcf_row_gh = PCF8575(cfg.MCB_I2C_PORT_NUM, cfg.MCB_I2C_ROW_GH_ADDRESS)
        self.pcf_leds = PCF8575(cfg.MCB_I2C_PORT_NUM, cfg.MCB_I2C_LEDS_ADDRESS)
        
        # Initialize all fields to False
        default = [False] * 8
        self.a = self.b = self.c = self.d = self.e = self.f = self.g = self.h = default
        
        # Declare board 2D lists #TODO REDO THIS WITH FEN
        self.board_current = [self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h]
        self.board_prev = self.board_current
        self.board_history = [self.board_current]

        #self.fen_board_current = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        #self.fen_board_prev = self.fen_board_current
        #self.fen_board_history = [self.fen_board_current]

        # Default board setup (False == Place piece)
        self.setup = [False, False, True, True, True, True, False, False]
        self.board_setup = [self.setup] * 8

        # Event history
        self.events = []

        # Set all inputs high on init
        self.pcf_row_ab.port = self.pcf_row_cd.port = self.pcf_row_ef.port = self.pcf_row_gh.port = [True] * 16

        # Setup GPIO pin mode
        GPIO.setmode(GPIO.BCM)

        # Init buttons pin mode
        GPIO.setup(cfg.MCB_BUT_WHITE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(cfg.MCB_BUT_CONFIRM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(cfg.MCB_BUT_BACK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(cfg.MCB_BUT_BLACK, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Init fields pin mode
        GPIO.setup(cfg.MCB_ROW_AB_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(cfg.MCB_ROW_CD_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(cfg.MCB_ROW_EF_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(cfg.MCB_ROW_GH_IO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def _button_callback(self, channel):
        
        """! Event callback to save events """

        if self.args.debug: print(f"{cfg.MCB_DEBUG_MSG}event: {channel}")

    def event_detected(self, channel):

        """! My own event detected method, since the GPIO.RPi sucks """

        if channel in self.events:
            self.events.remove(channel)
            return True

        return False

    def add_button_events(self):

        """! Add events to all buttons """
        
        # Remove the events before adding them again
        self.remove_button_events()

        if self.args.debug: print(f"{cfg.MCB_DEBUG_MSG}add button events")

        # Add button events
        GPIO.add_event_detect(cfg.MCB_BUT_WHITE, GPIO.FALLING, callback=self._button_callback, bouncetime=cfg.MCB_BUT_DEBOUNCE)
        GPIO.add_event_detect(cfg.MCB_BUT_CONFIRM, GPIO.FALLING, callback=self._button_callback, bouncetime=cfg.MCB_BUT_DEBOUNCE)
        GPIO.add_event_detect(cfg.MCB_BUT_BACK, GPIO.FALLING, callback=self._button_callback, bouncetime=cfg.MCB_BUT_DEBOUNCE)
        GPIO.add_event_detect(cfg.MCB_BUT_BLACK, GPIO.FALLING, callback=self._button_callback, bouncetime=cfg.MCB_BUT_DEBOUNCE)

    def remove_button_events(self):

        """! Remove events from all buttons """

        if self.args.debug: print(f"{cfg.MCB_DEBUG_MSG}remove button events")

        GPIO.remove_event_detect(cfg.MCB_BUT_WHITE)
        GPIO.remove_event_detect(cfg.MCB_BUT_CONFIRM)
        GPIO.remove_event_detect(cfg.MCB_BUT_BACK)
        GPIO.remove_event_detect(cfg.MCB_BUT_BLACK)


    def add_field_events(self):

        """! Add events to all chess fields """

        # Remove the events before adding them again
        self.remove_field_events()

        if self.args.debug: print(f"{cfg.MCB_DEBUG_MSG}add field events")

        # Add field events
        GPIO.add_event_detect(cfg.MCB_ROW_AB_IO, GPIO.FALLING, bouncetime=cfg.MCB_FIELD_DEBOUNCE)
        GPIO.add_event_detect(cfg.MCB_ROW_CD_IO, GPIO.FALLING, bouncetime=cfg.MCB_FIELD_DEBOUNCE)
        GPIO.add_event_detect(cfg.MCB_ROW_EF_IO, GPIO.FALLING, bouncetime=cfg.MCB_FIELD_DEBOUNCE)
        GPIO.add_event_detect(cfg.MCB_ROW_GH_IO, GPIO.FALLING, bouncetime=cfg.MCB_FIELD_DEBOUNCE)


    def remove_field_events(self):

        """! Remove events from all chess fields """

        if self.args.debug: print(f"{cfg.MCB_DEBUG_MSG}remove field events")

        GPIO.remove_event_detect(cfg.MCB_ROW_AB_IO)
        GPIO.remove_event_detect(cfg.MCB_ROW_CD_IO)
        GPIO.remove_event_detect(cfg.MCB_ROW_EF_IO)
        GPIO.remove_event_detect(cfg.MCB_ROW_GH_IO)


    def startup_leds(self, delay):

        """! Flash the LED's in a startup sequence 
        
        @param  delay    The time delay in the sequence.
        """

        ## LED sequence
        led_sequence = ["",
                        "45", 
                        "3456", 
                        "234567", 
                        "12345678",
                        "12345678a",
                        "12345678ab",
                        "12345678abc",
                        "12345678abcd",
                        "12345678abcde",
                        "12345678abcdef",
                        "12345678abcdefg",
                        "12345678abcdefgh"]

        ## Makes the sequence of leds
        for _ in range(2):

            ## Leds moving out
            for i in led_sequence:

                self.set_leds(i)
                time.sleep(delay)
            
            time.sleep(delay)

            ## Leds moving in
            for i in range(len(led_sequence)-1,-1,-1):

                self.set_leds(led_sequence[i])
                time.sleep(delay)
            
            time.sleep(delay)


    def read_fields(self):

        """! Read all the chess fields and save the current value """

        # Read the PCF8575 boards (this is done with the assumption that a1 = p00 etc. reason for reversion)
        self.a = [i for i in self.pcf_row_ab.port][8:][::-1]
        self.b = [i for i in self.pcf_row_ab.port][:8][::-1]
        self.c = [i for i in self.pcf_row_cd.port][8:][::-1]
        self.d = [i for i in self.pcf_row_cd.port][:8][::-1]
        self.e = [i for i in self.pcf_row_ef.port][8:][::-1]
        self.f = [i for i in self.pcf_row_ef.port][:8][::-1]
        self.g = [i for i in self.pcf_row_gh.port][8:][::-1]
        self.h = [i for i in self.pcf_row_gh.port][:8][::-1]

        # Update current board
        self.board_current = [self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h]


    def get_field_event(self):

        """! Determine what happens on the field
        
        @return Changed field value
        """

        # Read the fields
        self.read_fields()

        # Init return value
        field_value = ""

        # Determine what field changed based on board vs prev board
        for letter in range(8):
            for digit in range(8):
                if self.board_current[letter][digit] != self.board_prev[letter][digit]:
                    # Safe the last analysed changed field
                    field_value = chr(letter + 97) + chr(digit + 49)
                    if self.args.debug: print(f"{cfg.MCB_DEBUG_MSG}field changed: {field_value} -> [{self.board_current[letter][digit]}]")

        if field_value != "":
            self.board_prev = self.board_current

        return field_value


    def set_promotion_menu_led(self, toggle_led: bool, move: str, looper):

        """! Indicate the promotion piece with LEDs 
        
        @param  toggle_led  Boolean toggle flag
        @param  move        The move to determine

        @return             Move with promotion surfix for engine e.g. 'g7g8q'
        """

        leds = 'abcd'   # The led fields to use

        if looper == 0: promotion = 'q' # queen promotion
        elif looper == 1: promotion = 'b' # bishop promotion
        elif looper == 2: promotion = 'n' # knight promotion
        elif looper == 3: promotion = 'r' # rook promotion
        else: promotion = move[4]   # get the promotion from ai move

        if promotion == 'q': field = 'd' # light on d field
        elif promotion == 'b': field = 'c' # light on c field
        elif promotion == 'n': field = 'b' # light on b field
        elif promotion == 'r': field = 'a' # light on a field

        if toggle_led: self.set_leds(leds) # light all leds
        else: self.set_leds(leds.replace(field, "")) # flash with selection
            
        if len(move) == 4:
            return move + promotion
        else:
            return_mode = move[:4] + promotion
            return return_mode


    def set_move_led(self, toggle_led: bool, move: str):

        """! Indicate the given move with leds 
        
        @param  toggle_led  Boolean toggle flag
        @param  move        The move to determine what led to toggle
        """

        if toggle_led:
            self.set_leds(move[0] + move[1])
        else:
            self.set_leds(move[0] + move[1] + move[2] + move[3])


    def set_move_done_leds(self, move: str):

        """! Set LEDs for field when move is done

        @param  move        The current field to turn on
        """

        if len(move) == 4:
            self.set_leds(move[2] + move[3])


    def is_castling(self, move: str, all_moves: list):

        """! @brief     Check move for castling 
        
        @param move         The current move to check
        @param all_moves    List of moves done so far to determine if a King has been moved
        @return             True if castling
        """

        # Can king castle flag
        black = True
        white = True

        # If any king has moved in the past, it is not a castle, this is in a 
        # scenario where a piece moves e.g. e1g1 and is not the king, 
        # then it is not a castle
        for m in all_moves:
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

        """! Function to determ if the undo move is done """

        # Read board
        self.read_fields()

        # Setup current undo board, if undo on first move
        current_undo = self.board_history[-2]

        # Check if current board match board we are going to.
        if (self.board_current == current_undo):
                    
            # Update undo history
            del self.board_history[-1]

            # Update prev status
            self.board_prev = self.board_history[-1]
            
            # Finally return true
            return True

        if self.args.debug: 
            for i in range(8):
                print(f"{cfg.MCB_DEBUG_MSG}current_undo          : {current_undo[i]}")
                print(f"{cfg.MCB_DEBUG_MSG}self.board_current    : {self.board_current[i]}")
                #print(f"{MCB_DEBUG_MSG}self.board_prev       : {self.board_prev[i]}")
                #print(f"{MCB_DEBUG_MSG}self.board_history[-1]: {self.board_history[-1][i]}")
                print(cfg.MCB_DEBUG_MSG)

        return False
                

    def is_move_done(self, move: str, moves: list):

        """! Function to determ if a move is done
        
        @param move     The current move to check.
        @param moves    List of moves done so far, for castling check.

        @return True    If move is done.
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
        setup_leds = setup_leds + "a" if self.a == self.setup else setup_leds.replace("a", "")
        setup_leds = setup_leds + "b" if self.b == self.setup else setup_leds.replace("b", "")
        setup_leds = setup_leds + "c" if self.c == self.setup else setup_leds.replace("c", "")
        setup_leds = setup_leds + "d" if self.d == self.setup else setup_leds.replace("d", "")
        setup_leds = setup_leds + "e" if self.e == self.setup else setup_leds.replace("e", "")
        setup_leds = setup_leds + "f" if self.f == self.setup else setup_leds.replace("f", "")
        setup_leds = setup_leds + "g" if self.g == self.setup else setup_leds.replace("g", "")
        setup_leds = setup_leds + "h" if self.h == self.setup else setup_leds.replace("h", "")
        self.set_leds(setup_leds)


    def set_leds(self, led: str):

        """! Led indicators 
        
        @param  led     The chars to light up
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
        self.pcf_leds.port = port


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
