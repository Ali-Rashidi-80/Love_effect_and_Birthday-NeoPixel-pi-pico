#https://wokwi.com/projects/406321749821699073
from neopixel import NeoPixel
from machine import Pin
from time import sleep
import random


num_pixels = 16
pixels = NeoPixel(Pin(13), num_pixels)

def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

while True:
    for i in range(num_pixels):
        pixels[i] = random_color()
    pixels.write()
    sleep(0.1)
