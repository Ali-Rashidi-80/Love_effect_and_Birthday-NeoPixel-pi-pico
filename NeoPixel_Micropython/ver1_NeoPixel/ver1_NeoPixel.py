#https://wokwi.com/projects/406315354835231745
from machine import Pin
from neopixel import NeoPixel
from time import sleep

# تعریف رنگ‌های رنگین‌کمان
rainbow = [
    (126, 1, 0), (114, 13, 0), (102, 25, 0), (90, 37, 0), (78, 49, 0), (66, 61, 0), (54, 73, 0), (42, 85, 0),
    (30, 97, 0), (18, 109, 0), (6, 121, 0), (0, 122, 5), (0, 110, 17), (0, 98, 29), (0, 86, 41), (0, 74, 53),
    (0, 62, 65), (0, 50, 77), (0, 38, 89), (0, 26, 101), (0, 14, 113), (0, 2, 125), (9, 0, 118), (21, 0, 106),
    (33, 0, 94), (45, 0, 82), (57, 0, 70), (69, 0, 58), (81, 0, 46), (93, 0, 34), (105, 0, 22), (117, 0, 10)
]

# ایجاد لیستی از اشیاء NeoPixel
pixel_pins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
pixels_list = [NeoPixel(Pin(pin), 16) for pin in pixel_pins]

while True:
    # چرخش رنگ‌های رنگین‌کمان
    rainbow = rainbow[-1:] + rainbow[:-1]

    # تنظیم رنگ‌ها برای هر پیکسل در همه‌ی رشته‌ها
    for i in range(16):
        color = rainbow[i]
        for pixels in pixels_list:
            pixels[i] = color

    # به‌روزرسانی همه‌ی پیکسل‌ها
    for pixels in pixels_list:
        pixels.write()

    # توقف کوتاه برای دیدن افکت‌ها
    sleep(0.04)
