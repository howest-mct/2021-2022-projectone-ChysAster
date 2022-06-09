import time
from RPi import GPIO
import threading

from flask_cors import CORS
from flask_socketio import SocketIO, emit, send
from flask import Flask, jsonify, request
from repositories.DataRepository import DataRepository
from subprocess import check_output
from selenium import webdriver
from pylcdlib import lcd4bit
from serial import Serial, PARITY_NONE
from matrix import Matrix
mymatrix = Matrix()

ips = check_output(['hostname', '--all-ip-addresses'])
zonderB = str(ips)[18:32]
print(zonderB)

batchGeel = 188
batchBlauw = 129

mylcd = lcd4bit()
mylcd.write_message(zonderB)

kleur = ''

eersteKolom = 21
tweedeKolom = 26
derdeKolom = 20
vierdeKolom = 16
vijfdeKolom = 19
zesdeKolom = 13
zevendeKolom = 6

endpoint = '/api/v1'
# Code voor Hardware


def setup_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(eersteKolom, GPIO.IN)
    GPIO.setup(tweedeKolom, GPIO.IN)
    GPIO.setup(derdeKolom, GPIO.IN)
    GPIO.setup(vierdeKolom, GPIO.IN)
    GPIO.setup(vijfdeKolom, GPIO.IN)
    GPIO.setup(zesdeKolom, GPIO.IN)
    GPIO.setup(zevendeKolom, GPIO.IN)


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


@app.route(endpoint + '/activiteiten/', methods=['GET'])
def get_activiteit():
    if request.method == 'GET':

        return jsonify(activiteit=DataRepository.random_activiteit()), 200


@app.route(endpoint + '/historiek/', methods=['GET'])
def get_historiek():
    if request.method == 'GET':
        return jsonify(historiek=DataRepository.get_historiek()), 200


@socketio.on('connect')
def initial_connection():
    print('A new client connect')


@socketio.on('F2B_opdracht_geel_minuten')
def opdracht_geel_timer(jsonObject):
    if(jsonObject == 1):
        mymatrix.aftellen_een_minuten
    elif(jsonObject == 3):
        mymatrix.aftellen_drie_minuten
    elif(jsonObject == 5):
        mymatrix.aftellen_vijf_minuten


@socketio.on('F2B_opdracht_blauw_minuten')
def opdracht_blauw_timer(jsonObject):
    if(jsonObject == 1):
        mymatrix.aftellen_een_minuten2
    elif(jsonObject == 3):
        mymatrix.aftellen_drie_minuten2
    elif(jsonObject == 5):
        mymatrix.aftellen_vijf_minuten2


# @socketio.on()
# START een thread op. Belangrijk!!! Debugging moet UIT staan op start van de server, anders start de thread dubbel op
# werk enkel met de packages gevent en gevent-websocket.
def temperatuur():
    sensor_file_name = '/sys/bus/w1/devices/28-00000003b2c6/w1_slave'

    sensor_file = open(sensor_file_name, 'r')
    for line in sensor_file:
        lijn = line.rstrip("\n")
        t = lijn.find("t=")

    if(t != -1):
        temp = int(lijn.split("t=")[1])
        # print(f"het is: {temp/1000}\N{DEGREE SIGN} celcius")
        return round(temp/1000, 2)


def data_versturen():
    while True:
        print("temperatuur versturen")
        socketio.emit('B2F_status_temp', {
                      'temperatuur': temperatuur()}, broadcast=True)
        DataRepository.create_historiek(2, temperatuur())
        time.sleep(15)


def start_thread():
    print("**** Starting THREAD ****")
    thread = threading.Thread(target=data_versturen, args=(), daemon=True)
    thread.start()


def read_serial():
    with Serial('/dev/ttyS0', 9600, bytesize=8, parity=PARITY_NONE, stopbits=1) as port:
        while True:
            if port.in_waiting > 0:
                line = port.readline().decode('utf-8')  .rstrip()
                print(line)
                if line == str(batchGeel):
                    DataRepository.create_historiek(1, "geel")
                    # socketio.emit('B2F_rfid_data_geel', "geel", broadcast=True)
                    kleur = 'geel'
                    if(temperatuur() > 24):
                        activiteit_geel = DataRepository.random_activiteit_water()
                    elif(temperatuur() < 24):
                        activiteit_geel = DataRepository.random_activiteit()
                    socketio.emit('B2F_opdracht_geel',
                                  activiteit_geel, broadcast=True)
                elif line == str(batchBlauw):
                    DataRepository.create_historiek(1, "blauw")
                    # socketio.emit('B2F_rfid_data_rood', "rood", broadcast=True)
                    kleur = 'blauw'
                    if(temperatuur() > 24):
                        activiteit_blauw = DataRepository.random_activiteit_water()
                    elif(temperatuur() < 24):
                        activiteit_blauw = DataRepository.random_activiteit()
                    socketio.emit('B2F_opdracht_blauw',
                                  activiteit_blauw, broadcast=True)
                socketio.emit('B2F_rfid_data', kleur, broadcast=True)

                # niet returnen anders stopt de thread
                # return line


def thread_serial():
    print("**** Starting THREAD serial ****")
    thread = threading.Thread(target=read_serial, args=())
    thread.start()

# threads kolommen


def eerste_kolom():
    while True:
        if(GPIO.input(eersteKolom) == False):
            print("versturen infrarood")
            socketio.emit('B2F_eerste_kolom', 0)
            time.sleep(5)


def thread_eerste_kolom():
    print("infrarood eerste kolom thread")
    thread = threading.Thread(target=eerste_kolom)
    thread.start()


def tweede_kolom():
    while True:
        if(GPIO.input(tweedeKolom) == False):
            print("versturen infrarood")
            socketio.emit('B2F_tweede_kolom', 1)
            time.sleep(5)


def thread_tweede_kolom():
    print("infrarood tweede kolom thread")
    thread = threading.Thread(target=tweede_kolom)
    thread.start()


def derde_kolom():
    while True:
        if(GPIO.input(derdeKolom) == False):
            print("versturen infrarood")
            socketio.emit('B2F_derde_kolom', 2)
            time.sleep(5)


def thread_derde_kolom():
    print("infrarood derde kolom thread")
    thread = threading.Thread(target=derde_kolom)
    thread.start()


def vierde_kolom():
    while True:
        if(GPIO.input(vierdeKolom) == False):
            print("versturen infrarood")
            socketio.emit('B2F_vierde_kolom', 3)
            time.sleep(5)


def thread_vierde_kolom():
    print("infrarood vierde kolom thread")
    thread = threading.Thread(target=vierde_kolom)
    thread.start()


def vijfde_kolom():
    while True:
        if(GPIO.input(vijfdeKolom) == False):
            print("versturen infrarood")
            socketio.emit('B2F_vijfde_kolom', 4)
            time.sleep(5)


def thread_vijfde_kolom():
    print("infrarood vijfde kolom thread")
    thread = threading.Thread(target=vijfde_kolom)
    thread.start()


def zesde_kolom():
    while True:
        if(GPIO.input(zesdeKolom) == False):
            print("versturen infrarood")
            socketio.emit('B2F_zesde_kolom', 5)
            time.sleep(5)


def thread_zesde_kolom():
    print("infrarood zesde kolom thread")
    thread = threading.Thread(target=zesde_kolom)
    thread.start()


def zevende_kolom():
    while True:
        if(GPIO.input(zevendeKolom) == False):
            print("versturen infrarood")
            socketio.emit('B2F_zevende_kolom', 6)
            time.sleep(5)


def thread_zevende_kolom():
    print("infrarood zevende kolom thread")
    thread = threading.Thread(target=zevende_kolom)
    thread.start()


    # ANDERE FUNCTIES
if __name__ == '__main__':
    try:
        setup_gpio()
        print("**** Starting APP ****")
        start_thread()
        thread_serial()
        thread_eerste_kolom()
        thread_tweede_kolom()
        thread_derde_kolom()
        thread_vierde_kolom()
        thread_vijfde_kolom()
        thread_zesde_kolom()
        thread_zevende_kolom()
        socketio.run(app, debug=False, host='0.0.0.0')

    except KeyboardInterrupt:
        print('KeyboardInterrupt exception is caught')
    finally:
        GPIO.cleanup()
        mylcd.clear_lcd()
