import argparse
import time
import RPi.GPIO as GPIO
from stockfish import Stockfish     # https://pypi.org/project/stockfish/
from pcf8575 import PCF8575         # https://pypi.org/project/pcf8575/

APPTITLE = "mChessBoard"
AUTHOR = "by Mick Kirkegaard"
VERSION = "v1.0.0"
DATE = "Jan 01 2021 19:01"

"""! @brief     Board defines """
MCB_I2C_PORT_NUM = 1
MCB_I2C_ROW_AB_ADDRESS = 0x23
MCB_I2C_ROW_CD_ADDRESS = 0x22
MCB_I2C_ROW_EF_ADDRESS = 0x21
MCB_I2C_ROW_GH_ADDRESS = 0x20
MCB_I2C_LEDS_ADDRESS = 0x24

MCB_BUT_WHITE_CLOSE = 17    # Closest to WHITE side
MCB_BUT_WHITE_MID = 27      # Middle close to WHITE side
MCB_BUT_BLACK_MID = 22      # Middle close to BLACK side
MCB_BUT_BLACK_CLOSE = 23    # Closest to BLACK side

"""! @brief     Board fields and leds"""
pcf_row_ab = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_AB_ADDRESS)
pcf_row_cd = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_CD_ADDRESS)
pcf_row_ef = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_EF_ADDRESS)
pcf_row_gh = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_GH_ADDRESS)
pcf_leds = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_LEDS_ADDRESS)

"""! @brief     Other defines """

class Board:

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

        # Set all inputs high on init
        pcf_row_ab.port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]
        pcf_row_cd.port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]
        pcf_row_ef.port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]
        pcf_row_gh.port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]

        # Init buttons
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MCB_BUT_WHITE_CLOSE, GPIO.IN)
        GPIO.setup(MCB_BUT_WHITE_MID, GPIO.IN)
        GPIO.setup(MCB_BUT_BLACK_MID, GPIO.IN)
        GPIO.setup(MCB_BUT_BLACK_CLOSE, GPIO.IN)

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

    def display(self):

        # Read all fields
        self.read_fields()

        # Display status of all fields.
        print(f"  a   b   c   d   e   f   g   h    ")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {'p' if self.a[7] else '-'} | {'p' if self.b[7] else '-'} | {'p' if self.c[7] else '-'} | {'p' if self.d[7] else '-'} | {'p' if self.e[7] else '-'} | {'p' if self.f[7] else '-'} | {'p' if self.g[7] else '-'} | {'p' if self.h[7] else '-'} | 8")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {'p' if self.a[6] else '-'} | {'p' if self.b[6] else '-'} | {'p' if self.c[6] else '-'} | {'p' if self.d[6] else '-'} | {'p' if self.e[6] else '-'} | {'p' if self.f[6] else '-'} | {'p' if self.g[6] else '-'} | {'p' if self.h[6] else '-'} | 7")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {'p' if self.a[5] else '-'} | {'p' if self.b[5] else '-'} | {'p' if self.c[5] else '-'} | {'p' if self.d[5] else '-'} | {'p' if self.e[5] else '-'} | {'p' if self.f[5] else '-'} | {'p' if self.g[5] else '-'} | {'p' if self.h[5] else '-'} | 6")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {'p' if self.a[4] else '-'} | {'p' if self.b[4] else '-'} | {'p' if self.c[4] else '-'} | {'p' if self.d[4] else '-'} | {'p' if self.e[4] else '-'} | {'p' if self.f[4] else '-'} | {'p' if self.g[4] else '-'} | {'p' if self.h[4] else '-'} | 5")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {'p' if self.a[3] else '-'} | {'p' if self.b[3] else '-'} | {'p' if self.c[3] else '-'} | {'p' if self.d[3] else '-'} | {'p' if self.e[3] else '-'} | {'p' if self.f[3] else '-'} | {'p' if self.g[3] else '-'} | {'p' if self.h[3] else '-'} | 4")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {'p' if self.a[2] else '-'} | {'p' if self.b[2] else '-'} | {'p' if self.c[2] else '-'} | {'p' if self.d[2] else '-'} | {'p' if self.e[2] else '-'} | {'p' if self.f[2] else '-'} | {'p' if self.g[2] else '-'} | {'p' if self.h[2] else '-'} | 3")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {'p' if self.a[1] else '-'} | {'p' if self.b[1] else '-'} | {'p' if self.c[1] else '-'} | {'p' if self.d[1] else '-'} | {'p' if self.e[1] else '-'} | {'p' if self.f[1] else '-'} | {'p' if self.g[1] else '-'} | {'p' if self.h[1] else '-'} | 2")
        print(f"+---+---+---+---+---+---+---+---+  ")
        print(f"| {'p' if self.a[0] else '-'} | {'p' if self.b[0] else '-'} | {'p' if self.c[0] else '-'} | {'p' if self.d[0] else '-'} | {'p' if self.e[0] else '-'} | {'p' if self.f[0] else '-'} | {'p' if self.g[0] else '-'} | {'p' if self.h[0] else '-'} | 1")
        print(f"+---+---+---+---+---+---+---+---+  ")


def menu():

    print("Menu")


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


if __name__ == '__main__':

    """! @brief Main function """

    board = Board()
    #board.read()
    #print(len(board.a))
    #print(board.a[7])
    while(1):
        board.display()
        time.sleep(0.5)
    exit(0)

    # Get the arguments
    args = parser()

    try:
        stockfish = Stockfish(args.input,
                            parameters={
                            "Write Debug Log": "true",
                            "Contempt": 0,
                            "Min Split Depth": 0,
                            "Threads": 2,
                            "Ponder": "false",
                            "Hash": 16,
                            "MultiPV": 1,
                            "Skill Level": 20,
                            "Move Overhead": 30,
                            "Minimum Thinking Time": 20,
                            "Slow Mover": 80,
                            "UCI_Chess960": "false",
                                }
                            )
    except:
        print("Failed to init stockfish")

    print(stockfish.get_parameters())

    moves = []

    while True:
        # Print out board
        stockfish.set_position(moves)
        print("  a   b   c   d   e   f   g   h")
        print(stockfish.get_board_visual())


        # Wait for user input
        move = input('Make a move: ')
        if stockfish.is_move_correct(move):
            print("Move is correct!")
            moves.append(move)
            stockfish.set_position(moves)
            print(stockfish.get_board_visual())
        elif move == 'q':
            print("Quitting program")
            break
        else:
            print("Move is not valid")

        # Wait for computer input
        computer_move = stockfish.get_best_move_time(1000)

        #print(f"Computer move: {computer_move}")
        moves.append(computer_move)

