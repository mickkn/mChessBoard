import argparse
import time
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

"""! @brief     Board fields and leds"""
pcf_row_ab = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_AB_ADDRESS)
pcf_row_cd = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_CD_ADDRESS)
pcf_row_ef = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_EF_ADDRESS)
pcf_row_gh = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_GH_ADDRESS)
pcf_leds = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_LEDS_ADDRESS)

"""! @brief     Other defines """

class Board:

    def __init__(self):

        self.a = [False, False, False, False, False, False, False, False]
        self.b = [False, False, False, False, False, False, False, False]
        self.c = [False, False, False, False, False, False, False, False]
        self.d = [False, False, False, False, False, False, False, False]
        self.e = [False, False, False, False, False, False, False, False]
        self.f = [False, False, False, False, False, False, False, False]
        self.g = [False, False, False, False, False, False, False, False]
        self.h = [False, False, False, False, False, False, False, False]

        self.leds_letters = [True, True, True, True, True, True, True, True]
        self.leds_digits = [True, True, True, True, True, True, True, True]

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

    def set_leds(self, led):

        print(led)

        # Get letter as integer and convert to array position 'a' == 97
        letter = ord(led[0]) - 97 + 8

        # Get digit as integer and convert to array position '1' == 49
        digit = ord(led[1]) - 49

        print(letter)
        print(digit)

        port = [True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True]
        port[letter] = False
        port[digit] = False

        output = [16]
        output[8:15] = port[8:15][::-1]
        output[0:7] = port[0:7][::-1]

        pcf_leds.port = output

    def display(self):

        self.read_fields()

        # Test print out
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
        board.set_leds("a1")
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

