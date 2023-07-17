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

socketio = SocketIO()


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
