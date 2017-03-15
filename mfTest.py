from __future__ import division
import time

pwm = Adafruit_PCA9685.PCA9685()

servo_min = 150
servo_max = 600

def set_servo_pulse(channel, pulse):
    pulse_length = 1000000
    pulse_length //=60
    print('{0}us per period'.format(pulse_length))
    pulse_length //=4096 #12 bits of resolution
    print('{0}us per bit'.format(pulse_length))
    pulse *= 1000
    pulse //= pulse_length
    pwm.set_pwm(channel, 0, pulse)

#Set Frequency
pwm.set_pwm_freq(60)

#Move servo one time
pwm.set_pwm(3, 3, servo_min)
time.sleep(3)
pwm.set_pwm(3, 3, servo_max)
time.sleep(3)


