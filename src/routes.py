from flask import Flask, Response, request, render_template, url_for
import chess, chess.pgn
import chess.engine
import traceback
import time
import collections
import json
from gevent.pywsgi import WSGIServer

def run_routes():

    app = Flask(__name__, static_url_path='')
    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')



    http_server = WSGIServer(('0.0.0.0', 8080), app)
    http_server.serve_forever()