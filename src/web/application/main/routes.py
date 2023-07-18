"""
  :File:        main/routes.py

  :Details:     Contains the main functions of the web app.

  :Copyright:   Copyright (c) 2023 Mick Kirkegaard. All rights reserved.

  :Date:        28-05-2023
  :Author:      Mick Kirkegaard, Circle Consult ApS.
"""
import os
from flask import (
    render_template,
    request,
    session,
    copy_current_request_context,
    send_from_directory,
    current_app,
)
from flask_socketio import emit, disconnect

from application import socketio, board
from application.main import bp


@bp.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@bp.route("/favicon.ico")
def favicon():
    """Function that serves the favicon file."""
    return send_from_directory(
        os.path.join(current_app.root_path, "static"),
        "img/apple-touch-icon.png",
        mimetype="image/vnd.microsoft.icon",
    )


@bp.route('/img/<path:filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(current_app.root_path, "static", "img"), filename)


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
    # received, and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.event
def board_move(message):
    # move done via electronic chess board.
    emit('board_move', {'data': message['data']}, broadcast=True)


@bp.route('/app_move', methods=['GET', 'POST'])
def app_move():
    move = request.args.get('move', 0, type=str)
    print(move)
    return move


@socketio.event
def engine_move(message):
    # move done via chess engine.
    print(board.board_fen())
    emit('ai_move', {'data': message['data']}, broadcast=True)


@socketio.event
def connect():
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)
