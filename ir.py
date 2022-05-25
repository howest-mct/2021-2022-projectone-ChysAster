import RPi.GPIO as IO

import time

IO.setwarnings(False)

IO.setmode(IO.BCM)


IO.setup(21, IO.OUT)  # GPIO 2 -> Red LED as output

IO.setup(20, IO.OUT)  # GPIO 3 -> Green LED as output

IO.setup(25, IO.IN)  # GPIO 14 -> IR sensor as input


while 1:

    if(IO.input(25) == True):  # object is far away

        IO.output(21, True)  # Red led ON

        IO.output(20, False)  # Green led OFF

    if(IO.input(25) == False):  # object is near

        IO.output(20, True)  # Green led ON

        IO.output(21, False)  # Red led OFF
