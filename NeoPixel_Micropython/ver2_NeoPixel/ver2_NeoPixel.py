#https://wokwi.com/projects/406333071265870849
from machine import Pin
from neopixel import NeoPixel
from time import sleep
import random

# ایجاد لیستی از اشیاء NeoPixel با شماره پین‌های مربوطه
pixel_pins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
pixels_list = [NeoPixel(Pin(pin), 16) for pin in pixel_pins]

# تابع برای تولید یک رنگ تصادفی
def random_color():
    # تولید مقادیر تصادفی برای کانال‌های R، G و B
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

while True:
    # حلقه‌ای برای تخصیص رنگ‌های تصادفی به هر پیکسل
    for i in range(16):
        # تولید یک رنگ تصادفی
        color = random_color()
        # تنظیم رنگ تصادفی برای تمام پیکسل‌های هر رشته NeoPixel
        for pixels in pixels_list:
            pixels[i] = color

    # نوشتن (به‌روزرسانی) رنگ‌ها روی LEDها
    for pixels in pixels_list:
        pixels.write()

    # توقف کوتاه برای مشاهده افکت‌ها (تنظیم سرعت تغییر رنگ)
    sleep(0.1)  