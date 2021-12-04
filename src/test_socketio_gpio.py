import RPi.GPIO as GPIO
import socketio

GPIO.setmode(GPIO.BCM)
MCB_BUT_WHITE = 17  # Closest to WHITE side
MCB_BUT_CONFIRM = 27  # Middle close to WHITE side
MCB_BUT_BACK = 23  # Middle close to BLACK side
MCB_BUT_BLACK = 22  # Closest to BLACK side
GPIO.setup(MCB_BUT_WHITE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MCB_BUT_CONFIRM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MCB_BUT_BACK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MCB_BUT_BLACK, GPIO.IN, pull_up_down=GPIO.PUD_UP)

sio = socketio.Client(logger=True, engineio_logger=True)

def move(channel):
    
    print("move")
    sio.connect('http://10.0.1.10:5000', wait_timeout=10)
    sio.emit('my_broadcast_event', {'data': 'lol'})
    sio.disconnect()

if __name__ == '__main__':

    print("Startup")

    GPIO.add_event_detect(MCB_BUT_WHITE, GPIO.FALLING, callback=move, bouncetime=200)

    while True:

        if GPIO.event_detected(MCB_BUT_WHITE):
            print("Press")
