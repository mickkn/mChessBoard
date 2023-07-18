"""
  :File:        __init__.py

  :Details:     Contains initialized flask factories and function for flask app initialization.

  :Copyright:   Copyright (c) 2023 Mick Kirkegaard. All rights reserved.

  :Date:        28-05-2023
  :Author:      Mick Kirkegaard, Circle Consult ApS.
"""
from flask import Flask
from flask_socketio import SocketIO

from application.config import Config

import chess.engine

socketio = SocketIO()

engine = chess.engine.SimpleEngine.popen_uci(r"C:\Repos\mChessBoard\src\web\application\static\bin\stockfish-windows-x86-64-avx2.exe")
board = chess.Board("1k1r4/pp1b1R2/3q2pp/4p3/2B5/4Q3/PPP2B2/2K5 b - - 0 1")
limit = chess.engine.Limit(time=2.0)
engine.play(board, limit)  # doctest: +ELLIPSIS


def create_app(config_class=Config):
    """Returns instantiated flask application."""

    # Create flask app instance.
    app = Flask(__name__)

    # Configure app using config class.
    app.config.from_object(config_class)

    # Update session names for cookie handling.
    app.config.update(SESSION_COOKIE_NAME=app.config["SESSION_COOKIE_NAME"])

    # Initialize flask extensions.
    socketio.init_app(app)

    from application.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Return app instance.
    return app
