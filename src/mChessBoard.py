import argparse
import time
from signal import signal, SIGINT
import sys
import RPi.GPIO as GPIO

from statemachine import StateMachine, State
from stockfish import Stockfish  # https://pypi.org/project/stockfish/ edited to fit for Minic
from config import *

from board import Board
import fsm
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

    # Parse arguments
    args = parser()

    config = Config()

    # Create a FSM object
    f_sm = BoardFsm()

    # Create a Board object
    board = Board(args, config)

    # Main loop
    while True:

        fsm.run(f_sm, args, board, config)
