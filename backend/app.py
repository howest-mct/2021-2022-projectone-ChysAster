import time
from RPi import GPIO
from helpers.klasseknop import Button
import threading

from flask_cors import CORS
from flask_socketio import SocketIO, emit, send
from flask import Flask, jsonify
from repositories.DataRepository import DataRepository

from selenium import webdriver

# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options


# Code voor Hardware


def setup_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)


# Code voor Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'geheim!'
socketio = SocketIO(app, cors_allowed_origins="*", logger=False,
                    engineio_logger=False, ping_timeout=1)

CORS(app)


@socketio.on_error()        # Handles the default namespace
def error_handler(e):
    print(e)


# API ENDPOINTS


@app.route('/')
def hallo():
    return "Server is running, er zijn momenteel geen API endpoints beschikbaar."

@app.route('192.168.168.169/activiteit')


@socketio.on('connect')
def initial_connection():
    print('A new client connect')

@socketio.on()


# START een thread op. Belangrijk!!! Debugging moet UIT staan op start van de server, anders start de thread dubbel op
# werk enkel met de packages gevent en gevent-websocket.

def temperatuur():
    while True:
        sensor_file_name = '/sys/bus/w1/devices/28-00000003b2c6/w1_slave'

        sensor_file = open(sensor_file_name, 'r')
        for line in sensor_file:
            lijn = line.rstrip("\n")
            t = lijn.find("t=")

        if(t != -1):
            temp = int(lijn.split("t=")[1])
            print(f"het is: {temp/1000}\N{DEGREE SIGN} celcius")


def data_versturen():
    while True:
        print("temperatuur versturen")
        teVersturen = temperatuur()
        socketio.emit('B2F_status_temp', {'data': teVersturen}, broadcast=True)
        time.sleep(1)


def start_thread():
    print("**** Starting THREAD ****")
    thread = threading.Thread(target=data_versturen, args=(), daemon=True)
    thread.start()


# ANDERE FUNCTIES
if __name__ == '__main__':
    try:
        setup_gpio()
        print("**** Starting APP ****")
        start_thread()
        socketio.run(app, debug=False, host='0.0.0.0')
    except KeyboardInterrupt:
        print('KeyboardInterrupt exception is caught')
    finally:
        GPIO.cleanup()