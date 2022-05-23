#!/usr/bin/env python3
import serial
from RPi import GPIO
from serial import Serial, PARITY_NONE
ser = serial.Serial("/dev/serial0")


try:
    with Serial('/dev/ttyS0', 115200, bytesize=8, parity=PARITY_NONE, stopbits=1) as port:
        while True:
            if port.in_waiting > 0:
                line = port.readline().decode('utf-8').rstrip()
                print(line)
except KeyboardInterrupt as e:
    print(e)
finally:
    GPIO.cleanup()
    ser.close()
    print("script has stopped")


