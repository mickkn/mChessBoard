import argparse
import time
import threading
import sys
import RPi.GPIO as GPIO
import time
import collections
import json
from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from signal import signal, SIGINT
from statemachine import StateMachine, State
from stockfish import (
    Stockfish,
)  # https://pypi.org/project/stockfish/ edited to fit for Minic

from board import Board
from fsm import BoardFsm, run


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
    global chess_board
    chess_board.set_leds("")
    global board_thread
    board_thread.join()
    sys.exit(0)


async_mode = None
app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.event
def move_event(message):
    emit('move', {'data': message['data']}, broadcast=True)


@socketio.event
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.event
def connect():
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)
    

# https://cppsecrets.com/users/12012115105110103104112971141051049711450495264103109971051084699111109/Python-Socketio-Client.php

if __name__ == "__main__":

    """! @brief    Main function"""

    # CTRL+C handler
    signal(SIGINT, signal_handler)

    # Parse arguments
    args = parser()

    # Create a FSM object
    statemachine = BoardFsm(args)

    # Create a Board object
    global chess_board
    chess_board = Board(args)

    global board_thread
    board_thread = threading.Thread(target=run, args=(statemachine, args, chess_board))
    board_thread.start()

    """
    if args.debug:
        socketio.run(app=app, host='0.0.0.0', port=8080, debug=True)
    else:
        socketio.run(app=app, host='0.0.0.0', port=8080, debug=False)
    """
    