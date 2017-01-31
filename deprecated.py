#  1/25/16
import RPi.GPIO as GPIO_re #right elbow
import RPi.GPIO as GPIO_rs #right shoulder
import time
import pygame.mixer
from pygame.mixer import Sound


pygame.mixer.init()
ack = Sound("ack.wav")
limit = Sound("limit.wav")
#r2 = Sound("r2-d2.wav")
#r2.play()
#time.sleep(5)


###### Supress Warnings
GPIO_rs.setwarnings(False)
GPIO_re.setwarnings(False)


###### Set GPIO to board numbering System
GPIO_re.setmode(GPIO_re.BOARD)
GPIO_rs.setmode(GPIO_rs.BOARD)

try:
        GPIO_re.setup(11, GPIO_re.OUT)
        GPIO_rs.setup(12, GPIO_rs.OUT)
except Error:
        print "Error setting GPIO to BOARD numbering: {}",Error

######  Set FrequencyHertz and create PWM objects
frequencyHertz = 50
msPerCycle = 1000 / frequencyHertz
pwm_re = GPIO_re.PWM(11, frequencyHertz) #right elbow
pwm_rs = GPIO_rs.PWM(12, frequencyHertz) #right shoulder


###### Create default shoulder posistions
leftPosition = 0.75
rightPosition = 2.5
middlePosition = (rightPosition - leftPosition) / 2 + leftPosition

#positionList = [leftPosition, middlePosition, rightPosition, middlePosition]

print "Right Shoulder moving to Resting position"
dutyCycle = leftPosition * 100 / msPerCycle
pwm_rs.start(dutyCycle)
ack.play()
time.sleep(2)


print "Right Shoulder moving to Parallel Position"
dutyCycle = middlePosition * 100 / msPerCycle
pwm_rs.start(dutyCycle)
ack.play()
time.sleep(2)

print "Right Shoulder moving to  Extended Position"
dutyCycle = rightPosition * 100 / msPerCycle
pwm_rs.start(dutyCycle)
ack.play()

#for i in range(2):
        #for position in positionList:
                #dutyCyclePercentage = position * 100 / msPerCycle
                #print "Position: " + str(position)
                #print "Duty Cycle: " + str(dutyCyclePercentage) + "%"
                #pwm_re.start(dutyCyclePercentage)
                #pwm_rs.start(dutyCyclePercentage)
                #time.sleep(.5)

pwm_re.stop() #right elbow
pwm_rs.stop() #right shoulder

GPIO_re.cleanup(11)
GPIO_rs.cleanup(12)
