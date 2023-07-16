"""
  :File:        __init__.py

  :Details:     Contains initialized flask factories and
                function for flask app initialization.

  :Copyright:   Copyright (c) 2023 Circle Mick Kirkegaard. All rights reserved.

  :Date:        28-05-2023
  :Author:      Mick Kirkegaard.
"""
from application import create_app

#: Flask application instance.
app = create_app()