import time
from RPi import GPIO
buzzer = 18
buzzer2 = 17


class Buzzer:
    from RPi import GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(buzzer, GPIO.OUT)
    GPIO.setup(buzzer2, GPIO.OUT)

    def buzzer(self):
        self.GPIO.output(buzzer, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer, GPIO.LOW)
        time.sleep(0.4)
        self.GPIO.output(buzzer, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer, GPIO.LOW)
        time.sleep(0.4)
        self.GPIO.output(buzzer, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer, GPIO.LOW)
        time.sleep(0.4)
        self.GPIO.output(buzzer, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer, GPIO.LOW)
        time.sleep(0.4)
        self.GPIO.output(buzzer, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer, GPIO.LOW)
        time.sleep(0.4)
        self.GPIO.output(buzzer, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer, GPIO.LOW)

    def buzzer2(self):
        self.GPIO.output(buzzer2, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer2, GPIO.LOW)
        time.sleep(0.4)
        self.GPIO.output(buzzer2, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer2, GPIO.LOW)
        time.sleep(0.4)
        self.GPIO.output(buzzer2, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer2, GPIO.LOW)
        time.sleep(0.4)
        self.GPIO.output(buzzer2, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer2, GPIO.LOW)
        time.sleep(0.4)
        self.GPIO.output(buzzer2, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer2, GPIO.LOW)
        time.sleep(0.4)
        self.GPIO.output(buzzer2, GPIO.HIGH)
        time.sleep(0.5)
        self.GPIO.output(buzzer2, GPIO.LOW)
