import argparse
import time
import threading
import sys
import RPi.GPIO as GPIO
import time
import collections
import json

from flask import Flask, Response, request, render_template, url_for
from flask_socketio import SocketIO
from signal import signal, SIGINT
from statemachine import StateMachine, State
from stockfish import (
    Stockfish,
)  # https://pypi.org/project/stockfish/ edited to fit for Minic


from gevent.pywsgi import WSGIServer
from werkzeug.serving import run_with_reloader
from werkzeug.debug import DebuggedApplication

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
    chess_board.set_leds("")
    sys.exit(0)

async_mode = None
app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.event
def my_broadcast_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)

@socketio.event
def move_event(message):
    emit('move', {'data': message['data']}, broadcast=True)


@socketio.event
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.event
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room')
def on_close_room(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         to=message['room'])
    close_room(message['room'])


@socketio.event
def my_room_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         to=message['room'])


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
def my_ping():
    emit('my_pong')


@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
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
    chess_board = Board(args)

    #board_thread = threading.Thread(target=run, args=(statemachine, args, chess_board))
    #board_thread.start()

    #app = Flask(__name__, static_url_path='')
    #@app.route('/', methods=['GET'])
    #def index():

    #    return render_template('index.html', fen="rnbqkbnr/pppppppp/8/8/8/7P/PPPPPPP1/RNBQKBNR b KQkq - 0 1")

    socketio.run(app=app, host='0.0.0.0', port=8080, debug=True)

    print("Something runs")

    #http_server = WSGIServer(('0.0.0.0', 8080), DebuggedApplication(app))
    #http_server.serve_forever()
    
