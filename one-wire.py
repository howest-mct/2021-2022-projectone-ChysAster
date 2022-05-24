from RPi import GPIO
import time
GPIO.setmode(GPIO.BCM)

try:
    while True:
        sensor_file_name = '/sys/bus/w1/devices/28-00000003b2c6/w1_slave'

        sensor_file = open(sensor_file_name, 'r')
        for line in sensor_file:
            lijn = line.rstrip("\n")
            t = lijn.find("t=")

        if(t != -1):
            temp = int(lijn.split("t=")[1])
            print(f"het is: {temp/1000}\N{DEGREE SIGN} celcius")


except KeyboardInterrupt as e:

    print(e)

finally:
    sensor_file.close()

    print("script has stopped")
