"""
  :File:        __init__.py

  :Details:     Contains initialized flask factories and function for flask app initialization.

  :Copyright:   Copyright (c) 2023 Mick Kirkegaard. All rights reserved.

  :Date:        28-05-2023
  :Author:      Mick Kirkegaard, Circle Consult ApS.
"""




def create_app(config_class=Config):
    """Returns instantiated flask application."""

    # Create flask app instance.
    app = Flask(__name__)
