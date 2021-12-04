from flask import Flask, Response, request, render_template, url_for
import RPi.GPIO as GPIO
import json
from gevent.pywsgi import WSGIServer

GPIO.setmode(GPIO.BCM)
MCB_BUT_WHITE = 17  # Closest to WHITE side
MCB_BUT_CONFIRM = 27  # Middle close to WHITE side
MCB_BUT_BACK = 23  # Middle close to BLACK side
MCB_BUT_BLACK = 22  # Closest to BLACK side
GPIO.setup(MCB_BUT_WHITE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MCB_BUT_CONFIRM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MCB_BUT_BACK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MCB_BUT_BLACK, GPIO.IN, pull_up_down=GPIO.PUD_UP)

app = Flask(__name__, static_url_path='')

@app.route('/', methods=['GET'])
def index():
   return render_template('index.html', fen="rnbqkbnr/pppppppp/8/8/8/7P/PPPPPPP1/RNBQKBNR b KQkq - 0 1")

@app.route('/move', methods=['GET'])
def move(channel):

    print(channel)

    resp = {'fen': '', 'moves': '', 'game_over': 'true'}
    response = app.response_class(
        response=json.dumps(resp),
        status=200,
        mimetype='application/json'
        )

    print(response)

    return response

if __name__ == '__main__':

    GPIO.add_event_detect(MCB_BUT_WHITE, GPIO.FALLING, callback=move, bouncetime=200)

    #app.run(host='0.0.0.0', port=8080, debug=True)
    http_server = WSGIServer(('0.0.0.0', 8080), app)
    http_server.serve_forever()