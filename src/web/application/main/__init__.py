"""
  :File:        main/__init__.py

  :Details:     Contains the blueprint initialization of main.

  :Copyright:   Copyright (c) 2023 Mick Kirkegaard. All rights reserved.

  :Date:        28-05-2023
  :Author:      Mick Kirkegaard.
"""
from flask import Blueprint

bp = Blueprint("main", __name__)

from application.main import routes  # noqa: E402, F401.
