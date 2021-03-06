# imports
import time
import json
from RPi import GPIO
import threading
from spidev import SpiDev
from flask_cors import CORS
from flask_socketio import SocketIO, emit, send
from flask import Flask, jsonify, request
from repositories.DataRepository import DataRepository
from subprocess import check_output
from selenium import webdriver
from pylcdlib import lcd4bit
from serial import Serial, PARITY_NONE
import sys
import random
import multiprocessing

# get ip adres
ips = check_output(['hostname', '--all-ip-addresses'])
zonderB = str(ips)[18:32]
# write ip adres to lcd
mylcd = lcd4bit()
mylcd.write_message(zonderB)
mylcd.second_line()
mylcd.write_message("Scan your badge")

# set your batch numbers
badgeGeel = 188 #badge team yellow
badgeBlauw = 129 #badge team blue
opdrachtGestartBlauw = False
opdrachtGestartGeel = False
opdrachtGeslaagdGeel = False
opdrachtGeslaagdBlauw = False

kleuren = ["GEEL", "BLAUW"]
kleur = ''

# pin numbers of connected ir sensors
eersteKolom = 21  # first column
tweedeKolom = 22  # second
derdeKolom = 20  # third
vierdeKolom = 25  # fourth
vijfdeKolom = 19  # fith
zesdeKolom = 13  # sixt
zevendeKolom = 6  # seventh

# pin numbers of buzzer
buzzer = 18
buzzer2 = 17

buzzerScan = 26

buttonOngedaan = 27
prev_status_button = GPIO.LOW
# api endpoint
endpoint = '/api/v1'

# setup serial perhipheral interface
spi = SpiDev()
spi2 = SpiDev()
spi2.open(0, 1)
spi.open(0, 0)  # Bus is 0, device is chosen CE-pin (0 or 1)
spi.max_speed_hz = 100  # setup clock frequency
spi2.max_speed_hz = 100

# setup your pi hardware


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
    GPIO.setup(buttonOngedaan, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(buttonOngedaan, GPIO.RISING, callback=button_pressed)
    GPIO.setup(buzzer, GPIO.OUT)
    GPIO.setup(buzzer2, GPIO.OUT)
    GPIO.setup(buzzerScan, GPIO.OUT)
    spi.writebytes([0x9, 0])
    spi.writebytes([0xa, 0])
    spi.writebytes([0xb, 7])
    spi.writebytes([0xc, 1])
    spi2.writebytes([0x9, 0])
    spi2.writebytes([0xa, 0])
    spi2.writebytes([0xb, 7])
    spi2.writebytes([0xc, 1])


# Flask code
app = Flask(__name__)
app.config['SECRET_KEY'] = 'geheim!'
socketio = SocketIO(app, cors_allowed_origins="*", logger=False,
                    engineio_logger=False, ping_timeout=1)

CORS(app)

# socketia error handling


@socketio.on_error()
def error_handler(e):
    print(e)


# API ENDPOINTS
@app.route('/')
def hallo():
    return "Server is running, er zijn momenteel geen API endpoints beschikbaar."


@app.route(endpoint + '/activiteiten/', methods=['GET', 'POST'])
def get_activiteit():
    if request.method == 'GET':
        return jsonify(activiteit=DataRepository.random_activiteit()), 200
    elif request.method == 'POST':
        gegevens = DataRepository.json_or_formdata(request)
        nieuw_id = DataRepository.create_activiteit(
            gegevens['activiteit'], gegevens['isWater'], gegevens['aantalMinuten'])
        return jsonify(activiteitid=nieuw_id), 201


@app.route(endpoint + '/historiek/', methods=['GET'])
def get_historiek():
    if request.method == 'GET':
        return jsonify(historiek=DataRepository.get_historiek()), 200


@app.route(endpoint + '/historiek/badges/', methods=['GET'])
def get_badges():
    if request.method == 'GET':
        return jsonify(historiek=DataRepository.get_teams()), 200


@app.route(endpoint + '/grafiek/', methods=['GET'])
def get_temp_grafiek():
    if request.method == 'GET':
        return jsonify(temp=DataRepository.get_temp_grafiek()), 200


@app.route(endpoint + '/spelletjes/<kleur>/', methods=["GET"])
def get_gespeeld(kleur):
    if request.method == 'GET':
        return jsonify(spelletejes=DataRepository.get_gespeeld(kleur)), 200


@app.route(endpoint + '/gespeeld/geel/', methods=["GET"])
def get_gespeeld_geel():
    if request.method == "GET":
        return jsonify(spelletjes=DataRepository.get_gespeeld_geel()), 200


@app.route(endpoint + '/gespeeld/blauw/', methods=["GET"])
def get_gespeeld_blauw():
    if request.method == "GET":
        return jsonify(spelletjes=DataRepository.get_gespeeld_blauw()), 200


@app.route(endpoint + '/aantal/blauw/', methods=["GET"])
def get_aantal_blauw():
    if request.method == "GET":
        return jsonify(aantal=DataRepository.get_aantal_blauw()), 200


@app.route(endpoint + '/aantal/geel/', methods=["GET"])
def get_aantal_geel():
    if request.method == "GET":
        return jsonify(aantal=DataRepository.get_aantal_geel()), 200

# @socketio.on()
# first connection socket


@socketio.on('connect')
def initial_connection():
    print('A new client connect')

# socket to start timer yellow


@socketio.on('F2B_opdracht_geel_minuten')
def opdracht_geel_timer(minuten_geel):
    global voorwaarde
    if(minuten_geel == 1):
        voorwaarde = True
        print("starten een minuut geel")
        start_thread_aftellen_een_minuten(voorwaarde)
    elif(minuten_geel == 3):
        voorwaarde = True
        print("starten drie minuut geel")
        start_thread_aftellen_drie_minuten(voorwaarde)
    elif(minuten_geel == 5):
        voorwaarde = True
        print("starten vijf minuut geel")
        start_thread_aftellen_vijf_minuten(voorwaarde)

# socket to start timer blue


@socketio.on('F2B_opdracht_blauw_minuten')
def opdracht_blauw_timer(minuten_blauw):
    global voorwaarde_blauw
    if(minuten_blauw == 1):
        voorwaarde_blauw = True
        print("starten een minuut blauw")
        start_thread_aftellen_een_minuten2(voorwaarde_blauw)
    elif(minuten_blauw == 3):
        voorwaarde_blauw = True
        print("starten drie minuut blauw")
        start_thread_aftellen_drie_minuten2(voorwaarde_blauw)
    elif(minuten_blauw == 5):
        voorwaarde_blauw = True
        print("starten vijf minuut blauw")
        start_thread_aftellen_vijf_minuten2(voorwaarde_blauw)


@socketio.on('F2B_geslaagd_true')
def set_geslaagd_true():
    global opdrachtGeslaagdGeel, opdrachtGeslaagdBlauw
    opdrachtGeslaagdBlauw = True
    opdrachtGeslaagdGeel = True
    print("gedaan")


@socketio.on('F2B_beginner')
def beginner():
    item = random.choice(kleuren)
    socketio.emit('B2F_beginner', item)

# function to get temp


def temperatuur():
    sensor_file_name = '/sys/bus/w1/devices/28-00000003b2c6/w1_slave'
    global t, lijn, temp
    sensor_file = open(sensor_file_name, 'r')
    for line in sensor_file:
        lijn = line.rstrip("\n")
        t = lijn.find("t=")

    if(t != -1):
        temp = int(lijn.split("t=")[1])
        return round(temp/1000, 2)

# Function to restart game


@socketio.on('F2B_restart_game')
def restart_game():
    global opdrachtGestartBlauw, opdrachtGestartGeel, opdrachtGeslaagdGeel, opdrachtGeslaagdBlauw
    opdrachtGestartBlauw = False
    opdrachtGestartGeel = False
    opdrachtGeslaagdGeel = False
    opdrachtGeslaagdBlauw = False
    DataRepository.reset_blauw()
    DataRepository.reset_geel()

# function that sends temp to backend + sends temp to database


def data_versturen():
    while True:
        print("temperatuur versturen")
        socketio.emit('B2F_status_temp', {
                      'temperatuur': temperatuur()}, broadcast=True)
        if temperatuur() >= 24:
            socketio.emit('B2F_show_water_icoon')
        else:
            socketio.emit('B2F_close_water_icoon')
        DataRepository.create_historiek(2, temperatuur())
        time.sleep(15)

# thread for temp


def start_thread():
    print("**** Starting THREAD ****")
    thread = threading.Thread(target=data_versturen, args=(), daemon=True)
    thread.start()

# function that gets serial data(rfid) from arduino + controls if it is yellow or blue and sens it to frontend


def read_serial():
    global opdrachtGestartBlauw, opdrachtGestartGeel
    with Serial('/dev/ttyS0', 9600, bytesize=8, parity=PARITY_NONE, stopbits=1) as port:
        while True:
            global voorwaardee
            if port.in_waiting > 0:
                line = port.readline().decode('utf-8')  .rstrip()
                print(line)
                if line == str(badgeGeel):
                    GPIO.output(buzzerScan, GPIO.HIGH)
                    time.sleep(0.15)
                    GPIO.output(buzzerScan, GPIO.LOW)
                    mylcd.clear_lcd()
                    mylcd.write_message(zonderB)
                    mylcd.second_line()
                    mylcd.write_message("Team geel")
                    DataRepository.create_historiek(1, "geel")

                    # socketio.emit('B2F_rfid_data_geel', "geel", broadcast=True)
                    kleur = 'geel'
                    if opdrachtGestartGeel == False:
                        if(temperatuur() > 24):
                            activiteit_geel = DataRepository.random_activiteit_water_geel()
                        elif(temperatuur() < 24):
                            activiteit_geel = DataRepository.random_activiteit_geel()
                        opdrachtGestartGeel = True
                        socketio.emit('B2F_opdracht_geel',
                                      activiteit_geel, broadcast=True)
                    else:
                        socketio.emit('B2F_geslaagd_geel')
                        voorwaardee = False
                        start_thread_aftellen_een_minuten(voorwaardee)
                        start_thread_aftellen_drie_minuten(voorwaardee)
                        start_thread_aftellen_vijf_minuten(voorwaardee)
                        timeOut()
                elif line == str(badgeBlauw):
                    GPIO.output(buzzerScan, GPIO.HIGH)
                    time.sleep(0.15)
                    GPIO.output(buzzerScan, GPIO.LOW)
                    mylcd.clear_lcd()
                    mylcd.write_message(zonderB)
                    mylcd.second_line()
                    mylcd.write_message("Team blauw")
                    DataRepository.create_historiek(1, "blauw")
                    # socketio.emit('B2F_rfid_data_rood', "rood", broadcast=True)
                    kleur = 'blauw'
                    if opdrachtGestartBlauw == False:
                        if(temperatuur() > 24):
                            activiteit_blauw = DataRepository.random_activiteit_water_blauw()
                        elif(temperatuur() < 24):
                            activiteit_blauw = DataRepository.random_activiteit_blauw()
                        opdrachtGestartBlauw = True
                        socketio.emit('B2F_opdracht_blauw',
                                      activiteit_blauw, broadcast=True)
                    else:
                        socketio.emit('B2F_geslaagd_blauw')
                        voorwaardee = False
                        start_thread_aftellen_een_minuten2(voorwaardee)
                        start_thread_aftellen_drie_minuten2(voorwaardee)
                        start_thread_aftellen_vijf_minuten2(voorwaardee)
                        timeOut2()
                socketio.emit('B2F_rfid_data', kleur, broadcast=True)

# thread for serial


def thread_serial():
    print("**** Starting THREAD serial ****")
    thread = threading.Thread(target=read_serial, args=())
    thread.start()


@socketio.on('F2B_opdracht_geslaagd')
def opdracht_geslaagd(Geslaagd):
    global opdrachtGestartBlauw, opdrachtGestartGeel, opdrachtGeslaagdGeel, opdrachtGeslaagdBlauw
    if Geslaagd['geslaagd'] == False:
        if Geslaagd['kleur'] == 'geel':
            if(temperatuur() > 24):
                activiteit_geel = DataRepository.random_activiteit_water_geel()
            elif(temperatuur() < 24):
                activiteit_geel = DataRepository.random_activiteit_geel()
            opdrachtGestartGeel = True
            socketio.emit('B2F_opdracht_geel',
                          activiteit_geel, broadcast=True)
        elif Geslaagd['kleur'] == 'blauw':
            if(temperatuur() > 24):
                activiteit_blauw = DataRepository.random_activiteit_water_blauw()
            elif(temperatuur() < 24):
                activiteit_blauw = DataRepository.random_activiteit_blauw()
            opdrachtGestartBlauw = True
            socketio.emit('B2F_opdracht_blauw',
                          activiteit_blauw, broadcast=True)
        else:
            print("Kleur niet gekend")
    else:
        print("Opdracht is geslaagd")
        if Geslaagd['kleur'] == 'geel':
            opdrachtGeslaagdGeel = True
            opdrachtGestartGeel = False
            clear_memory()
        elif Geslaagd['kleur'] == 'blauw':
            opdrachtGeslaagdBlauw = True
            opdrachtGestartBlauw = False
            clear_memory2()


# frontend sends the played activity to backend and sets it as played in database


@socketio.on('F2B_opdracht_geel_is_gespeeld')
def set_geel_gespeeld(idActiviteiten):
    DataRepository.set_gespeeld_geel(idActiviteiten)

# frontend sends the played activity to backend and sets it as played in database


@socketio.on('F2B_opdracht_blauw_is_gespeeld')
def set_blauw_gespeeld(idActiviteiten):
    DataRepository.set_gespeeld_blauw(idActiviteiten)


def button_pressed(channel):
    socketio.emit('B2F_ongedaan_maken')


# thread for timer game
all_processes = []
all_processes_blauw = []


def start_thread_aftellen_een_minuten(voorwaarde):
    print("**** Starting THREAD ****")
    process_een = multiprocessing.Process(
        target=aftellen_een_minuten)
    if voorwaarde == True:
        process_een.start()
        all_processes.append(process_een)
    else:
        for process_een in all_processes:
            print(process_een)
            process_een.terminate()
        all_processes.clear()
        print(all_processes)
        clear_memory()
        voorwaarde = False


# thread for timer game


def start_thread_aftellen_drie_minuten(voorwaarde):
    print("**** Starting THREAD ****")
    process_drie = multiprocessing.Process(
        target=aftellen_drie_minuten)
    if voorwaarde == True:
        process_drie.start()
        all_processes.append(process_drie)
    else:
        for process_drie in all_processes:
            print(process_drie)
            process_drie.terminate()

            print(process_drie)
        all_processes.clear()
        print(all_processes)
        clear_memory()

# thread for timer game


def start_thread_aftellen_vijf_minuten(voorwaarde):
    print("**** Starting THREAD ****")
    process_vijf = multiprocessing.Process(
        target=aftellen_vijf_minuten)
    if voorwaarde == True:
        process_vijf.start()
        all_processes.append(process_vijf)
    else:
        for process_vijf in all_processes:
            print(process_vijf)
            process_vijf.terminate()

            print(process_vijf)
        all_processes.clear()
        print(all_processes)
        clear_memory()

# thread for timer game


def start_thread_aftellen_een_minuten2(voorwaarde):
    print("**** Starting THREAD ****")
    process_een2 = multiprocessing.Process(
        target=aftellen_een_minuten2)
    if voorwaarde == True:
        process_een2.start()
        all_processes_blauw.append(process_een2)
    else:
        for process_een2 in all_processes_blauw:
            process_een2.terminate()
        all_processes_blauw.clear()
        clear_memory2()

# thread for timer game


def start_thread_aftellen_drie_minuten2(voorwaarde):
    print("**** Starting THREAD ****")
    process_drie2 = multiprocessing.Process(
        target=aftellen_drie_minuten2)
    if voorwaarde == True:
        process_drie2.start()
        all_processes_blauw.append(process_drie2)
    else:
        for process_drie2 in all_processes_blauw:
            process_drie2.terminate()
        all_processes_blauw.clear()
        clear_memory2()

# thread for timer game


def start_thread_aftellen_vijf_minuten2(voorwaarde):
    print("**** Starting THREAD ****")
    process_vijf2 = multiprocessing.Process(
        target=aftellen_vijf_minuten2)
    if voorwaarde == True:
        process_vijf2.start()
        all_processes_blauw.append(process_vijf2)
    else:
        for process_vijf2 in all_processes_blauw:
            process_vijf2.terminate()
        all_processes_blauw.clear()
        clear_memory2()


def mag_schijf_spelen():
    global opdrachtGeslaagdGeel, opdrachtGeslaagdBlauw
    if (opdrachtGeslaagdBlauw == True or opdrachtGeslaagdGeel == True):
        return True
    else:
        return False


# threads colums


def kolom():
    global opdrachtGeslaagdGeel, opdrachtGeslaagdBlauw
    while True:
        if(GPIO.input(eersteKolom) == False and mag_schijf_spelen()):
            print("versturen infrarood 0")
            socketio.emit('B2F_kolom', 0)
            opdrachtGeslaagdBlauw = False
            opdrachtGeslaagdGeel = False
            time.sleep(5)
        elif (GPIO.input(tweedeKolom) == False and mag_schijf_spelen()):
            print("versturen infrarood 1")
            socketio.emit('B2F_kolom', 1)
            opdrachtGeslaagdBlauw = False
            opdrachtGeslaagdGeel = False
            time.sleep(5)
        elif (GPIO.input(derdeKolom) == False and mag_schijf_spelen()):
            print("versturen infrarood 2")
            socketio.emit('B2F_kolom', 2)
            opdrachtGeslaagdBlauw = False
            opdrachtGeslaagdGeel = False
            time.sleep(5)
        elif (GPIO.input(vierdeKolom) == False and mag_schijf_spelen()):
            print("versturen infrarood 3")
            socketio.emit('B2F_kolom', 3)
            opdrachtGeslaagdBlauw = False
            opdrachtGeslaagdGeel = False
            time.sleep(5)
        elif (GPIO.input(vijfdeKolom) == False and mag_schijf_spelen()):
            print("versturen infrarood 4")
            socketio.emit('B2F_kolom', 4)
            opdrachtGeslaagdBlauw = False
            opdrachtGeslaagdGeel = False
            time.sleep(5)
        elif (GPIO.input(zesdeKolom) == False and mag_schijf_spelen()):
            print("versturen infrarood 5")
            socketio.emit('B2F_kolom', 5)
            opdrachtGeslaagdBlauw = False
            opdrachtGeslaagdGeel = False
            time.sleep(5)
        elif (GPIO.input(zevendeKolom) == False and mag_schijf_spelen()):
            print("versturen infrarood 6")
            socketio.emit('B2F_kolom', 6)
            opdrachtGeslaagdBlauw = False
            opdrachtGeslaagdGeel = False
            time.sleep(5)


def thread_kolom():
    print("infrarood kolom thread")
    thread = threading.Thread(target=kolom)
    thread.start()

# buzzer and matrix


def buzzer_einde():
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(0.4)
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(0.4)
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(0.4)
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(0.4)
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(0.4)
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer, GPIO.LOW)


def buzzer_einde2():
    GPIO.output(buzzer2, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer2, GPIO.LOW)
    time.sleep(0.4)
    GPIO.output(buzzer2, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer2, GPIO.LOW)
    time.sleep(0.4)
    GPIO.output(buzzer2, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer2, GPIO.LOW)
    time.sleep(0.4)
    GPIO.output(buzzer2, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer2, GPIO.LOW)
    time.sleep(0.4)
    GPIO.output(buzzer2, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer2, GPIO.LOW)
    time.sleep(0.4)
    GPIO.output(buzzer2, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(buzzer2, GPIO.LOW)


def timer():
    spi.writebytes([0x1, 0b10000000])
    spi.writebytes([0x2, 0b00000000])
    spi.writebytes([0x3, 0b00000000])
    spi.writebytes([0x4, 0b00000000])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11000000])
    spi.writebytes([0x2, 0b00000000])
    spi.writebytes([0x3, 0b00000000])
    spi.writebytes([0x4, 0b00000000])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11100000])
    spi.writebytes([0x2, 0b00000000])
    spi.writebytes([0x3, 0b00000000])
    spi.writebytes([0x4, 0b00000000])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11110000])
    spi.writebytes([0x2, 0b00000000])
    spi.writebytes([0x3, 0b00000000])
    spi.writebytes([0x4, 0b00000000])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111000])
    spi.writebytes([0x2, 0b00000000])
    spi.writebytes([0x3, 0b00000000])
    spi.writebytes([0x4, 0b00000000])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111100])
    spi.writebytes([0x2, 0b00000000])
    spi.writebytes([0x3, 0b00000000])
    spi.writebytes([0x4, 0b00000000])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111110])
    spi.writebytes([0x2, 0b00000000])
    spi.writebytes([0x3, 0b00000000])
    spi.writebytes([0x4, 0b00000000])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000000])
    spi.writebytes([0x3, 0b00000000])
    spi.writebytes([0x4, 0b00000000])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000000])
    spi.writebytes([0x4, 0b00000000])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000000])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b00000001])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b00000001])
    spi.writebytes([0x8, 0b00000001])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b00000001])
    spi.writebytes([0x8, 0b00000011])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b00000001])
    spi.writebytes([0x8, 0b00000111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b00000001])
    spi.writebytes([0x8, 0b00001111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b00000001])
    spi.writebytes([0x8, 0b00011111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b00000001])
    spi.writebytes([0x8, 0b00111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b00000001])
    spi.writebytes([0x8, 0b01111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b00000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b00000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b00000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b00000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b00000001])
    spi.writebytes([0x4, 0b10000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b00000001])
    spi.writebytes([0x3, 0b10000001])
    spi.writebytes([0x4, 0b10000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b10000001])
    spi.writebytes([0x3, 0b10000001])
    spi.writebytes([0x4, 0b10000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11000001])
    spi.writebytes([0x3, 0b10000001])
    spi.writebytes([0x4, 0b10000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11100001])
    spi.writebytes([0x3, 0b10000001])
    spi.writebytes([0x4, 0b10000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11110001])
    spi.writebytes([0x3, 0b10000001])
    spi.writebytes([0x4, 0b10000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111001])
    spi.writebytes([0x3, 0b10000001])
    spi.writebytes([0x4, 0b10000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111101])
    spi.writebytes([0x3, 0b10000001])
    spi.writebytes([0x4, 0b10000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000001])
    spi.writebytes([0x4, 0b10000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000001])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000001])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000011])
    spi.writebytes([0x6, 0b10000001])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000011])
    spi.writebytes([0x6, 0b10000011])
    spi.writebytes([0x7, 0b10000001])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000011])
    spi.writebytes([0x6, 0b10000011])
    spi.writebytes([0x7, 0b10000011])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000011])
    spi.writebytes([0x6, 0b10000011])
    spi.writebytes([0x7, 0b10000111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000011])
    spi.writebytes([0x6, 0b10000011])
    spi.writebytes([0x7, 0b10001111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000011])
    spi.writebytes([0x6, 0b10000011])
    spi.writebytes([0x7, 0b10011111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000011])
    spi.writebytes([0x6, 0b10000011])
    spi.writebytes([0x7, 0b10111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000011])
    spi.writebytes([0x6, 0b10000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000011])
    spi.writebytes([0x6, 0b11000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b10000011])
    spi.writebytes([0x6, 0b10000011])
    spi.writebytes([0x7, 0b10111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b10000011])
    spi.writebytes([0x5, 0b11000011])
    spi.writebytes([0x6, 0b11000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b10000011])
    spi.writebytes([0x4, 0b11000011])
    spi.writebytes([0x5, 0b11000011])
    spi.writebytes([0x6, 0b11000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11000011])
    spi.writebytes([0x4, 0b11000011])
    spi.writebytes([0x5, 0b11000011])
    spi.writebytes([0x6, 0b11000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11100011])
    spi.writebytes([0x4, 0b11000011])
    spi.writebytes([0x5, 0b11000011])
    spi.writebytes([0x6, 0b11000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11110011])
    spi.writebytes([0x4, 0b11000011])
    spi.writebytes([0x5, 0b11000011])
    spi.writebytes([0x6, 0b11000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111011])
    spi.writebytes([0x4, 0b11000011])
    spi.writebytes([0x5, 0b11000011])
    spi.writebytes([0x6, 0b11000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11000011])
    spi.writebytes([0x5, 0b11000011])
    spi.writebytes([0x6, 0b11000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11000111])
    spi.writebytes([0x5, 0b11000011])
    spi.writebytes([0x6, 0b11000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11000111])
    spi.writebytes([0x5, 0b11000111])
    spi.writebytes([0x6, 0b11000011])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11000111])
    spi.writebytes([0x5, 0b11000111])
    spi.writebytes([0x6, 0b11000111])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11000111])
    spi.writebytes([0x5, 0b11000111])
    spi.writebytes([0x6, 0b11001111])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11000111])
    spi.writebytes([0x5, 0b11000111])
    spi.writebytes([0x6, 0b11011111])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11000111])
    spi.writebytes([0x5, 0b11000111])
    spi.writebytes([0x6, 0b11111111])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11000111])
    spi.writebytes([0x5, 0b11100111])
    spi.writebytes([0x6, 0b11111111])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11100111])
    spi.writebytes([0x5, 0b11100111])
    spi.writebytes([0x6, 0b11111111])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])
    time.sleep(1)


def timer2():
    spi2.writebytes([0x1, 0b10000000])
    spi2.writebytes([0x2, 0b00000000])
    spi2.writebytes([0x3, 0b00000000])
    spi2.writebytes([0x4, 0b00000000])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11000000])
    spi2.writebytes([0x2, 0b00000000])
    spi2.writebytes([0x3, 0b00000000])
    spi2.writebytes([0x4, 0b00000000])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11100000])
    spi2.writebytes([0x2, 0b00000000])
    spi2.writebytes([0x3, 0b00000000])
    spi2.writebytes([0x4, 0b00000000])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11110000])
    spi2.writebytes([0x2, 0b00000000])
    spi2.writebytes([0x3, 0b00000000])
    spi2.writebytes([0x4, 0b00000000])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111000])
    spi2.writebytes([0x2, 0b00000000])
    spi2.writebytes([0x3, 0b00000000])
    spi2.writebytes([0x4, 0b00000000])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111100])
    spi2.writebytes([0x2, 0b00000000])
    spi2.writebytes([0x3, 0b00000000])
    spi2.writebytes([0x4, 0b00000000])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111110])
    spi2.writebytes([0x2, 0b00000000])
    spi2.writebytes([0x3, 0b00000000])
    spi2.writebytes([0x4, 0b00000000])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000000])
    spi2.writebytes([0x3, 0b00000000])
    spi2.writebytes([0x4, 0b00000000])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000000])
    spi2.writebytes([0x4, 0b00000000])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000000])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b00000001])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b00000001])
    spi2.writebytes([0x8, 0b00000001])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b00000001])
    spi2.writebytes([0x8, 0b00000011])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b00000001])
    spi2.writebytes([0x8, 0b00000111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b00000001])
    spi2.writebytes([0x8, 0b00001111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b00000001])
    spi2.writebytes([0x8, 0b00011111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b00000001])
    spi2.writebytes([0x8, 0b00111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b00000001])
    spi2.writebytes([0x8, 0b01111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b00000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b00000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b00000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b00000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b00000001])
    spi2.writebytes([0x4, 0b10000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b00000001])
    spi2.writebytes([0x3, 0b10000001])
    spi2.writebytes([0x4, 0b10000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b10000001])
    spi2.writebytes([0x3, 0b10000001])
    spi2.writebytes([0x4, 0b10000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11000001])
    spi2.writebytes([0x3, 0b10000001])
    spi2.writebytes([0x4, 0b10000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11100001])
    spi2.writebytes([0x3, 0b10000001])
    spi2.writebytes([0x4, 0b10000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11110001])
    spi2.writebytes([0x3, 0b10000001])
    spi2.writebytes([0x4, 0b10000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111001])
    spi2.writebytes([0x3, 0b10000001])
    spi2.writebytes([0x4, 0b10000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111101])
    spi2.writebytes([0x3, 0b10000001])
    spi2.writebytes([0x4, 0b10000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000001])
    spi2.writebytes([0x4, 0b10000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000001])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000001])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000011])
    spi2.writebytes([0x6, 0b10000001])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000011])
    spi2.writebytes([0x6, 0b10000011])
    spi2.writebytes([0x7, 0b10000001])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000011])
    spi2.writebytes([0x6, 0b10000011])
    spi2.writebytes([0x7, 0b10000011])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000011])
    spi2.writebytes([0x6, 0b10000011])
    spi2.writebytes([0x7, 0b10000111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000011])
    spi2.writebytes([0x6, 0b10000011])
    spi2.writebytes([0x7, 0b10001111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000011])
    spi2.writebytes([0x6, 0b10000011])
    spi2.writebytes([0x7, 0b10011111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000011])
    spi2.writebytes([0x6, 0b10000011])
    spi2.writebytes([0x7, 0b10111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000011])
    spi2.writebytes([0x6, 0b10000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000011])
    spi2.writebytes([0x6, 0b11000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b10000011])
    spi2.writebytes([0x6, 0b10000011])
    spi2.writebytes([0x7, 0b10111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b10000011])
    spi2.writebytes([0x5, 0b11000011])
    spi2.writebytes([0x6, 0b11000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b10000011])
    spi2.writebytes([0x4, 0b11000011])
    spi2.writebytes([0x5, 0b11000011])
    spi2.writebytes([0x6, 0b11000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11000011])
    spi2.writebytes([0x4, 0b11000011])
    spi2.writebytes([0x5, 0b11000011])
    spi2.writebytes([0x6, 0b11000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11100011])
    spi2.writebytes([0x4, 0b11000011])
    spi2.writebytes([0x5, 0b11000011])
    spi2.writebytes([0x6, 0b11000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11110011])
    spi2.writebytes([0x4, 0b11000011])
    spi2.writebytes([0x5, 0b11000011])
    spi2.writebytes([0x6, 0b11000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111011])
    spi2.writebytes([0x4, 0b11000011])
    spi2.writebytes([0x5, 0b11000011])
    spi2.writebytes([0x6, 0b11000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111111])
    spi2.writebytes([0x4, 0b11000011])
    spi2.writebytes([0x5, 0b11000011])
    spi2.writebytes([0x6, 0b11000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111111])
    spi2.writebytes([0x4, 0b11000111])
    spi2.writebytes([0x5, 0b11000011])
    spi2.writebytes([0x6, 0b11000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111111])
    spi2.writebytes([0x4, 0b11000111])
    spi2.writebytes([0x5, 0b11000111])
    spi2.writebytes([0x6, 0b11000011])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111111])
    spi2.writebytes([0x4, 0b11000111])
    spi2.writebytes([0x5, 0b11000111])
    spi2.writebytes([0x6, 0b11000111])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111111])
    spi2.writebytes([0x4, 0b11000111])
    spi2.writebytes([0x5, 0b11000111])
    spi2.writebytes([0x6, 0b11001111])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111111])
    spi2.writebytes([0x4, 0b11000111])
    spi2.writebytes([0x5, 0b11000111])
    spi2.writebytes([0x6, 0b11011111])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111111])
    spi2.writebytes([0x4, 0b11000111])
    spi2.writebytes([0x5, 0b11000111])
    spi2.writebytes([0x6, 0b11111111])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111111])
    spi2.writebytes([0x4, 0b11000111])
    spi2.writebytes([0x5, 0b11100111])
    spi2.writebytes([0x6, 0b11111111])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111111])
    spi2.writebytes([0x4, 0b11100111])
    spi2.writebytes([0x5, 0b11100111])
    spi2.writebytes([0x6, 0b11111111])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])
    time.sleep(1)


def cijferEen():
    spi.writebytes([0x1, 0b00000000])
    spi.writebytes([0x2, 0b00000000])
    spi.writebytes([0x3, 0b10000010])
    spi.writebytes([0x4, 0b11111111])
    spi.writebytes([0x5, 0b10000000])
    spi.writebytes([0x6, 0b00000000])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)


def cijferEen2():
    spi2.writebytes([0x1, 0b00000000])
    spi2.writebytes([0x2, 0b00000000])
    spi2.writebytes([0x3, 0b10000010])
    spi2.writebytes([0x4, 0b11111111])
    spi2.writebytes([0x5, 0b10000000])
    spi2.writebytes([0x6, 0b00000000])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)


def cijferTwee():
    spi.writebytes([0x1, 0b00000000])
    spi.writebytes([0x2, 0b10000100])
    spi.writebytes([0x3, 0b11000010])
    spi.writebytes([0x4, 0b10100010])
    spi.writebytes([0x5, 0b10010010])
    spi.writebytes([0x6, 0b10001100])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)


def cijferTwee2():
    spi2.writebytes([0x1, 0b00000000])
    spi2.writebytes([0x2, 0b10000100])
    spi2.writebytes([0x3, 0b11000010])
    spi2.writebytes([0x4, 0b10100010])
    spi2.writebytes([0x5, 0b10010010])
    spi2.writebytes([0x6, 0b10001100])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)


def cijferDrie():
    spi.writebytes([0x1, 0b00000000])
    spi.writebytes([0x2, 0b01000100])
    spi.writebytes([0x3, 0b10000010])
    spi.writebytes([0x4, 0b10010010])
    spi.writebytes([0x5, 0b10010010])
    spi.writebytes([0x6, 0b01101100])
    spi.writebytes([0x7, 0b00000000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)


def cijferDrie2():
    spi2.writebytes([0x1, 0b00000000])
    spi2.writebytes([0x2, 0b01000100])
    spi2.writebytes([0x3, 0b10000010])
    spi2.writebytes([0x4, 0b10010010])
    spi2.writebytes([0x5, 0b10010010])
    spi2.writebytes([0x6, 0b01101100])
    spi2.writebytes([0x7, 0b00000000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)


def cijferVier():
    spi.writebytes([0x1, 0b00000000])
    spi.writebytes([0x2, 0b00100000])
    spi.writebytes([0x3, 0b00110000])
    spi.writebytes([0x4, 0b00101000])
    spi.writebytes([0x5, 0b00100100])
    spi.writebytes([0x6, 0b11111110])
    spi.writebytes([0x7, 0b00100000])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)


def cijferVier2():
    spi2.writebytes([0x1, 0b00000000])
    spi2.writebytes([0x2, 0b00100000])
    spi2.writebytes([0x3, 0b00110000])
    spi2.writebytes([0x4, 0b00101000])
    spi2.writebytes([0x5, 0b00100100])
    spi2.writebytes([0x6, 0b11111110])
    spi2.writebytes([0x7, 0b00100000])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)


def cijferVijf():
    spi.writebytes([0x1, 0b00000000])
    spi.writebytes([0x2, 0b00000000])
    spi.writebytes([0x3, 0b10001110])
    spi.writebytes([0x4, 0b10001010])
    spi.writebytes([0x5, 0b10001010])
    spi.writebytes([0x6, 0b10011010])
    spi.writebytes([0x7, 0b01100010])
    spi.writebytes([0x8, 0b00000000])
    time.sleep(1)


def cijferVijf2():
    spi2.writebytes([0x1, 0b00000000])
    spi2.writebytes([0x2, 0b00000000])
    spi2.writebytes([0x3, 0b10001110])
    spi2.writebytes([0x4, 0b10001010])
    spi2.writebytes([0x5, 0b10001010])
    spi2.writebytes([0x6, 0b10011010])
    spi2.writebytes([0x7, 0b01100010])
    spi2.writebytes([0x8, 0b00000000])
    time.sleep(1)


def volledigAan():
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11111111])
    spi.writebytes([0x5, 0b11111111])
    spi.writebytes([0x6, 0b11111111])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])


def volledigAan2():
    spi2.writebytes([0x1, 0b11111111])
    spi2.writebytes([0x2, 0b11111111])
    spi2.writebytes([0x3, 0b11111111])
    spi2.writebytes([0x4, 0b11111111])
    spi2.writebytes([0x5, 0b11111111])
    spi2.writebytes([0x6, 0b11111111])
    spi2.writebytes([0x7, 0b11111111])
    spi2.writebytes([0x8, 0b11111111])


def clear_memory():
    spi.writebytes([0x1, 0])
    spi.writebytes([0x2, 0])
    spi.writebytes([0x3, 0])
    spi.writebytes([0x4, 0])
    spi.writebytes([0x5, 0])
    spi.writebytes([0x6, 0])
    spi.writebytes([0x7, 0])
    spi.writebytes([0x8, 0])


def clear_memory2():
    spi2.writebytes([0x1, 0])
    spi2.writebytes([0x2, 0])
    spi2.writebytes([0x3, 0])
    spi2.writebytes([0x4, 0])
    spi2.writebytes([0x5, 0])
    spi2.writebytes([0x6, 0])
    spi2.writebytes([0x7, 0])
    spi2.writebytes([0x8, 0])


def timeOut():
    volledigAan()
    time.sleep(0.5)
    clear_memory()
    time.sleep(0.5)
    volledigAan()
    time.sleep(0.5)
    clear_memory()
    time.sleep(0.5)
    volledigAan()
    time.sleep(0.5)
    clear_memory()
    time.sleep(0.5)
    volledigAan()
    time.sleep(0.5)
    clear_memory()


def timeOut2():
    volledigAan2()
    time.sleep(0.5)
    clear_memory2()
    time.sleep(0.5)
    volledigAan2()
    time.sleep(0.5)
    clear_memory2()
    time.sleep(0.5)
    volledigAan2()
    time.sleep(0.5)
    clear_memory2()
    time.sleep(0.5)
    volledigAan2()
    time.sleep(0.5)
    clear_memory2()


def count_down(countdown_time):
    start = time.time()
    while((time.time() - start) < countdown_time):
        pass


def aftellen_vijf_minuten():
    cijferVijf()
    timer()
    cijferVier()
    timer()
    cijferDrie()
    timer()
    cijferTwee()
    timer()
    cijferEen()
    timer()
    buzzer_einde()
    timeOut()
    clear_memory()


def aftellen_drie_minuten():
    cijferDrie()
    timer()
    cijferTwee()
    timer()
    cijferEen()
    timer()
    buzzer_einde()
    timeOut()
    clear_memory()


def aftellen_een_minuten():
    cijferEen()
    timer()
    buzzer_einde()
    timeOut()
    clear_memory()


def aftellen_vijf_minuten2():
    cijferVijf2()
    timer2()
    cijferVier2()
    timer2()
    cijferDrie2()
    timer2()
    cijferTwee2()
    timer2()
    cijferEen2()
    timer2()
    buzzer_einde2()
    timeOut2()
    clear_memory2()


def aftellen_drie_minuten2():
    cijferDrie2()
    timer2()
    cijferTwee2()
    timer2()
    cijferEen2()
    timer2()
    buzzer_einde2()
    timeOut2()
    clear_memory2()


def aftellen_een_minuten2():
    cijferEen2()
    timer2()
    buzzer_einde2()
    timeOut2()
    clear_memory2()


    # ANDERE FUNCTIES
if __name__ == '__main__':
    try:
        setup_gpio()
        print("**** Starting APP ****")
        start_thread()
        thread_serial()
        thread_kolom()
        socketio.run(app, debug=False, host='0.0.0.0')

    except KeyboardInterrupt:
        print('KeyboardInterrupt exception is caught')
    finally:
        GPIO.cleanup()
        mylcd.clear_lcd()
        clear_memory()
        clear_memory2()
