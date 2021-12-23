import argparse
import sys
import RPi.GPIO as GPIO
import state_machine
import state_machine_impl
import board
from signal import signal, SIGINT


def parser():

    """
    Parser function to get all the arguments
    """

    # Construct the argument parse and return the arguments
    args = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    args.add_argument(
        "-i",
        "--input",
        type=str,
        default="/home/pi/mChessBoard/src/minic_3.04_linux_x32_armv6",
        help="path to ai engine",
    )
    args.add_argument("-d", "--debug", action="store_true", help="debug printout")
    args.add_argument(
        "-a",
        "--auto_confirm",
        action="store_true",
        help="auto confirm movement of pieces",
    )

    print("\n" + str(args.parse_args()) + "\n")

    return args.parse_args()


def signal_handler(sig, frame):

    """! @brief    Exit function"""

    print(" SIGINT or CTRL-C detected. Exiting gracefully")
    GPIO.cleanup()
    sys.exit(0)


if __name__ == "__main__":

    """! @brief    Main function"""

    print("Starting up...")

    # CTRL+C handler
    signal(SIGINT, signal_handler)

    # Parse arguments
    args = parser()

    # Create a FSM object
    statemachine = state_machine_impl.BoardFsm(args)

    # Create a Board object
    chess_board = board.Board(args)

    while True:
        if state_machine.run(statemachine, args, chess_board) is not None:
            break
    