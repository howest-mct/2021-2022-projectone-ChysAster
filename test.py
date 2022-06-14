from time import sleep, time
from spidev import SpiDev
import time
from RPi import GPIO


spi = SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 100  # Klokfrequentie instellen


def setup():
    spi.writebytes([0x9, 0])
    spi.writebytes([0xa, 0])
    spi.writebytes([0xb, 7])
    spi.writebytes([0xc, 1])


def volledigAan():
    spi.writebytes([0x1, 0b11111111])
    spi.writebytes([0x2, 0b11111111])
    spi.writebytes([0x3, 0b11111111])
    spi.writebytes([0x4, 0b11111111])
    spi.writebytes([0x5, 0b11111111])
    spi.writebytes([0x6, 0b11111111])
    spi.writebytes([0x7, 0b11111111])
    spi.writebytes([0x8, 0b11111111])


def clear_memory():
    spi.writebytes([0x1, 0])
    spi.writebytes([0x2, 0])
    spi.writebytes([0x3, 0])
    spi.writebytes([0x4, 0])
    spi.writebytes([0x5, 0])
    spi.writebytes([0x6, 0])
    spi.writebytes([0x7, 0])
    spi.writebytes([0x8, 0])


try:
    setup()
    while True:
        volledigAan()

except KeyboardInterrupt as e:
    print(e)

finally:
    GPIO.cleanup()
    clear_memory()
    print("script has stopped")
