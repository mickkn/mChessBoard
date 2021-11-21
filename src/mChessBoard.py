import argparse
import time
from signal import signal, SIGINT
import sys
import RPi.GPIO as GPIO

from statemachine import StateMachine, State
from stockfish import Stockfish  # https://pypi.org/project/stockfish/ edited to fit for Minic
from config import *

from board import Board
from fsm import BoardFsm

def parser():

    """
    Parser function to get all the arguments
    """

    # Construct the argument parse and return the arguments
    args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    args.add_argument("-i", "--input", type=str, default="/home/pi/mChessBoard/src/minic_3.04_linux_x32_armv6",
                        help="path to ai engine")
    args.add_argument("-d", "--debug", action='store_true',
                        help="debug printout")
    args.add_argument("-a", "--auto_confirm", action='store_true',
                        help="auto confirm movement of pieces")

    print('\n' + str(args.parse_args()) + '\n')

    return args.parse_args()


def signal_handler(sig, frame):

    """! @brief    Exit function """

    print(' SIGINT or CTRL-C detected. Exiting gracefully')
    GPIO.cleanup()
    board.set_leds("")
    sys.exit(0)


if __name__ == "__main__":

    """! @brief    Main function """

    # CTRL+C handler
    signal(SIGINT, signal_handler)

    # Create a FSM object
    fsm = BoardFsm()

    # Create a Board object
    board = Board()

    # Parse arguments
    args = parser()

    # Flags & Variables
    initial = True
    first_entry = True
    prev_state = None
    current_state = None

    # Movement global variables and flags
    move_ai = ""                ### Move made by AI Engine
    move_human = ""             ### Move made by Human
    move_undo = ""              ### Move made by Undo
    move_promotion = ""         ### Move made by Promotion
    moves = []                  ### List of moves for engine
    play_difficulty = 1         ### Default difficulty

    mode_setting = 0            ### Default mode setting 0: Human vs AI, 1: Human vs. Human
    mode_human_color = 'white'  ### Default Human color

    # Evaluation Engine Setup
    stockfish = None
    stockfish_param = {
        "Write Debug Log": "false",
        "Contempt": 0,
        "Min Split Depth": 0,
        "Threads": 1,
        "Ponder": "false",
        "Hash": 16,
        "MultiPV": 1,
        "Skill Level": 20,
        "Move Overhead": 30,
        "Minimum Thinking Time": 20,
        "Slow Mover": 80,
        "UCI_Chess960": "false",
    }

    # AI Engine setup
    ai = None
    ai_parameters = {
        "Write Debug Log": "false",
        "Contempt": 0,
        "Min Split Depth": 0,
        "Threads": 1,
        "Ponder": "false",
        "Hash": 16,
        "MultiPV": 1,
        "Skill Level": 20,
        "Move Overhead": 30,
        "Minimum Thinking Time": 20,
        "Slow Mover": 80,
        "UCI_Chess960": "false",
    }

    # Main loop
    while True:

        fsm.run(fsm, board)
