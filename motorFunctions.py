# 1/25/17
# Chris Burns - @Forecast_Cloudy
# Library to provide body part movement to a droid
# Version .01

import time
import pygame.mixer
import log
from pygame.mixer import Sound


#Create a logger object
logger = log.rLog(False)

#Attempt to Load RPi module - this code will only execute on Pi
#TODO - Create a virtual bot to test code up to the point of axis manipulation
#TODO - even better if the virual bot can be a visualization
try:
    import RPi.GPIO as GPIO
except ImportError as e:
    logger.LogError("motorFunctions.py: Cannot import the RPi module, install it with pip or this may not be a Raspberry Pi")

DEBUG = False

frequencyHertz = 50  # PWm Frequency
msPerCycle = 1000 / frequencyHertz  # MilliSeconds per Frequency Cycle

###### Create default joint positions
leftPosition_RS = 0.85
rightPosition_RS = 2.25
middlePosition_RS = (rightPosition_RS - leftPosition_RS) / 2 + leftPosition_RS

pygame.mixer.init()
ack = Sound("audio/ack.wav")
limit = Sound("audio/limit.wav")


def executeMovement(pin, pos):
    try:
        # CREATE and Clean up a GPIO object with each call - until further notice
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, 50)
        pwm.start(0)
        pwm.ChangeDutyCycle(pos)
        time.sleep(.85)
        pwm.stop()
        GPIO.cleanup()
    except Exception as e:
        logger.LogError("motorFunctions::executeMovement() Error: {}".format(e.message))




class Body(object):
    """A Body class encapulates the movements of appendages """

    # Turn warnings on or off
    try:
        GPIO.setwarnings(False)
    except Exception:
        pass

    def debugMode(self, debug):
        if debug:
            GPIO.setwarnings(True)
        DEBUG = debug

    class LeftArm():
        @staticmethod
        def moveDown():
            logger.LogThis("motorFunctions.py: moving LEFT arm (GPIO 13) to DOWN position")
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(13, GPIO.OUT)
                pwm = GPIO.PWM(13, frequencyHertz)
                dutyCycle = rightPosition_RS * 100 / msPerCycle
                pwm.start(dutyCycle)
                time.sleep(1.5)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured {}".format(e.message))

        @staticmethod
        def moveParallel():
            logger.LogThis("motorFunctions.py: moving LEFT arm (GPIO 13) to be parallel with floor (out)")
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(13, GPIO.OUT)
                pwm = GPIO.PWM(13, frequencyHertz)
                dutyCycle = middlePosition_RS * 100 / msPerCycle
                pwm.start(dutyCycle)
                time.sleep(1.5)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured {}".format(e.message))

        @staticmethod
        def moveUp():
            logger.LogThis("motorFunctions.py: moving LEFT arm (GPIO 13) UP")
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(13, GPIO.OUT)
                pwm = GPIO.PWM(13, frequencyHertz)
                dutyCycle = leftPosition_RS * 100 / msPerCycle
                pwm.start(dutyCycle)
                time.sleep(1.5)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured: {}".format(e.message))

        @staticmethod
        def bend():
            logger.LogThis("motorFunctions.py: BENDing LEFT arm (GPIO 15)")
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(15, GPIO.OUT)
                pwm = GPIO.PWM(15, frequencyHertz)
                dutyCycle = leftPosition_RS * 100 / msPerCycle
                pwm.start(dutyCycle)
                time.sleep(1.5)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured: {}".format(e.message))

        @staticmethod
        def straighten():
            logger.LogThis("motorFunctions.py: STRAIGHTening LEFT arm (GPIO 15)")
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(15, GPIO.OUT)
                pwm = GPIO.PWM(15, frequencyHertz)
                dutyCycle = middlePosition_RS * 100 / msPerCycle
                pwm.start(dutyCycle)
                time.sleep(1.5)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured {}".format(e.message))


    class RightArm():

        def __init__(self):
            pass

        @staticmethod
        def moveDown(): #At Rest Position AKA Left Position of Servo on Right Shoulder
            logger.LogThis("motorFunctions.py: moving RIGHT arm (GPIO 12) to DOWN position")
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(12, GPIO.OUT)
                pwm = GPIO.PWM(12, frequencyHertz)
                dutyCycle = leftPosition_RS * 100 / msPerCycle
                pwm.start(dutyCycle)
                time.sleep(1.5)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured {}".format(e))

        @staticmethod
        def moveParallel(): #Middle Position on Either Shoulder
            logger.LogThis("motorFunctions.py: move RIGHT arm (GPIO 12) to be parallel with floor (OUT)")
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(12, GPIO.OUT)
                pwm = GPIO.PWM(12, frequencyHertz)
                dutyCycle = middlePosition_RS * 100 / msPerCycle
                pwm.start(dutyCycle)
                time.sleep(1.5)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured {}".format(e))


        @staticmethod
        def moveUp():
            logger.LogThis("motorFunctions.py: move RIGHT arm (GPIO 12) to UP position")
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(12, GPIO.OUT)
                pwm = GPIO.PWM(12, frequencyHertz)
                dutyCycle = rightPosition_RS * 100 / msPerCycle
                pwm.start(dutyCycle)
                time.sleep(1.5)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured {}".format(e))

        @staticmethod
        def bend():
            logger.LogThis("motorFunctions.py: BENDing RIGHT arm (GPIO 11)")
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(11, GPIO.OUT)
                pwm = GPIO.PWM(11, frequencyHertz)
                dutyCycle = rightPosition_RS * 100 / msPerCycle
                pwm.start(dutyCycle)
                time.sleep(1.5)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured {}".format(e))

        @staticmethod
        def straighten():
            logger.LogThis("motorFunctions.py: STRAIGHTening RIGHT arm (GPIO 11)")
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(11, GPIO.OUT)
                pwm = GPIO.PWM(11, frequencyHertz)
                dutyCycle = middlePosition_RS * 100 / msPerCycle
                pwm.start(dutyCycle)
                time.sleep(1.5)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured {}".format(e))

        @staticmethod
        def wave():
            #TODO - Add code to wave the right arm.  Wave as in "Hello or Goodbye"
            logger.LogThis("motorFunctions.py: STRAIGHTening RIGHT arm (GPIO 11)")


    class Neck():

        def __init__(self):
            pass


        @staticmethod
        def lookForward(): #At rest position - not left or right
            logger.LogThis("motorFunctions.py: moving neck to LOOK FORWARD position(GPIO 40)")
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(40, GPIO.OUT)
            pwm = GPIO.PWM(40, frequencyHertz)
            dutyCycle = middlePosition_RS * 100 / msPerCycle
            pwm.start(dutyCycle)
            time.sleep(1.5)

        @staticmethod
        def lookLeft():
            logger.LogThis("motorFunctions.py: moving neck to LOOK LEFT position (GPIO 40)")
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(40, GPIO.OUT)
            pwm = GPIO.PWM(40, frequencyHertz)
            dutyCycle = leftPosition_RS * 100 / msPerCycle
            pwm.start(dutyCycle)
            time.sleep(1.5)

        @staticmethod
        def lookRight():
            logger.LogThis("motorFunctions.py: moving neck to LOOK RIGHT position (GPIO 40)")
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(40, GPIO.OUT)
            pwm = GPIO.PWM(40, frequencyHertz)
            dutyCycle = rightPosition_RS * 100 / msPerCycle
            pwm.start(dutyCycle)
            time.sleep(1.5)

        @staticmethod
        def lookStraight(): #At rest position not looking up or down
            logger.LogThis("motorFunctions.py: moving neck to LOOK STRAIGHT ahead (GPIO 38)")
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(38, GPIO.OUT)
            pwm = GPIO.PWM(38, frequencyHertz)
            dutyCycle = middlePosition_RS * 100 / msPerCycle
            pwm.start(dutyCycle)
            time.sleep(1.5)

        @staticmethod
        def lookUp():
            logger.LogThis("motorFunctions.py: moving neck to LOOK UP (GPIO 38)")
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(38, GPIO.OUT)
            pwm = GPIO.PWM(38, frequencyHertz)
            dutyCycle = leftPosition_RS * 100 / msPerCycle
            pwm.start(dutyCycle)
            time.sleep(1.5)

        @staticmethod
        def lookDown():
            logger.LogThis("motorFunctions.py: moving neck to LOOK DOWN(GPIO 38)")
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(38, GPIO.OUT)
            pwm = GPIO.PWM(38, frequencyHertz)
            dutyCycle = 0.45 * 100 / msPerCycle
            pwm.start(dutyCycle)
            time.sleep(1.5)








