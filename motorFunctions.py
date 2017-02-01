# 1/25/17
# Chris Burns - @Forecast_Cloudy
# Library to provide body part movement to a droid
# Version .01

import time
import pygame.mixer
import Log
import os
from pygame.mixer import Sound

#Create a logger object
logger = Log.rLog(False)

try: #Attempt to Load RPi module - will only work on Pi
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
                ack.play()
                time.sleep(2)
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
                ack.play()
                time.sleep(2)
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
                ack.play()
                time.sleep(2)
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
                ack.play()
                time.sleep(2)
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
                ack.play()
                time.sleep(2)
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
                ack.play()
                time.sleep(2)
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
                ack.play()
                time.sleep(2)
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
                ack.play()
                time.sleep(2)
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
                ack.play()
                time.sleep(2)
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
                ack.play()
                time.sleep(2)
            except Exception as e:
                limit.play()
                logger.LogError("motorFunctions.py: An error has occured {}".format(e))











