import time
import board
import adafruit_bno055
from gpiozero import Button, LED, Buzzer

i2c = board.I2C()
sensor = adafruit_bno055.BNO055_I2C(i2c)

button = Button(23)
led1 = LED(22)
led2 = LED(27)
buzzer = Buzzer(17)

def sing_buzzer():
    buzzer.on()
    time.sleep(1)
    buzzer.off()
    time.sleep(0.1)

try:
    while True:
        h, r, p = sensor.euler
        print(h, r, p)

        if button.is_pressed:
            print("Button pressed! LEDs ON and buzzer singing.")
            led1.on()
            led2.on()

            sing_buzzer()

            time.sleep(1)
        else:
            led1.off()
            led2.off()

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Program interrupted by user")

finally:
    print("Cleaning up")

