import json
import os
import ast
try:
    import RPi.GPIO as GPIO
except:
    pass
import time
from collections import namedtuple
from boto3 import Session

#session = Session(profile_name="default")
#rekognition = session.client("rekognition")

#with open("capture.png", "rb")as imagefile:
    #response = rekognition.detect_labels(Image={'Bytes': imagefile.read()}, MaxLabels=10)

#print type(response)

#quote = "I am "

#for label in response["Labels"]:
    #c = round(label["Confidence"],2)
    #quote+=str(c)
    #quote+=str(" percent confident I see a ")
    #quote+=str(label["Name"])
    #quote+=str(" , ")

class Joint():
    NAME = None
    GPIO = None
    START_POS = None
    LOW = None
    MIDDLE = None
    HIGH = None
    Limitations = None


def loadJointMap():
    jointmap = []

    if os.path.exists("JOINTMAP"):
        print("cortex.py::loadJointMap(): JOINTMAP file found, loading...")
        try:
            with open("JOINTMAP") as f:
                content = f.read()
                print "JOINTMAP data is of type {}".format(type(content))

                dContent = ast.literal_eval(content)
                print "JOINTMAP data is now of type {}".format(type(dContent))

                #for joint in dContent["Joints"]:
                    #j = Joint #Create new joint obj
                    #j.GPIO = joint["GPIO"]
                    #j.Limitations = joint["LIMITATIONS"]
                    #j.LOW = joint["LOW"]
                    #j.MIDDLE = joint["MIDDLE"]
                    #j.HIGH = joint["HIGH"]
                    #j.START_POS = joint["START_POS"]
                    #j.NAME = joint["Name"]

                    #jointmap.append(j)
        except Exception as e:
            print("cortex.py::loadJointMap(): Error loading JOINTMAP - {}".format(e.message))
    else:
        print("cortex.py::loadJointMap(): Unable to find/or open the JOINTMAP")

    return dContent


def main():
    #pos = input("Choose a servo position. 1 = LOOK UP, 2 = LOOK STRAIGHT (LEVEL), 3 = LOOK DOWN ")
    #move(pos)

    jointmap = loadJointMap()

    for joint in jointmap["Joints"]:
        print joint["Name"]




def move(pos):
    joint = None
    for j in Js:
        if j.name == "NECK_ELEVATION":
            joint = j

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(j.GPIO, GPIO.OUT)
    pwm = GPIO.PWM(j.GPIO, 50)
    pwm.start(0)
    try:
        if pos == 1:
            print "Moving NECK joint to LOOK UP position (servo-left) "
            pwm.ChangeDutyCycle(j.LOW)
            time.sleep(1.5)
            pwm.stop()
        elif pos == 2:
            print "Moving NECK joint to STRAIGHT position (servo-middle) "
            pwm.ChangeDutyCycle(j.MIDDLE)
            time.sleep(1.5)
            pwm.stop()
        elif pos == 3:
            print "Moving NECK joint to LOOK DOWN position (servo-right) "
            pwm.ChangeDutyCycle(j.HIGH)
            time.sleep(1.5)
            pwm.stop()
    except Exception:
        print Exception.message

    GPIO.cleanup()
    main()


main()








#j = "{u'Labels': [{u'Confidence': 99.29132843017578, u'Name': u'Human'},{u'Confidence': 99.29470825195312, u'Name': u'People'},{u'Confidence': 99.29470825195312, u'Name': u'Person'},{u'Confidence': 98.16999053955078, u'Name': u'Arm'},{u'Confidence': 51.457489013671875, u'Name': u'Face'},{u'Confidence': 51.457489013671875, u'Name': u'Selfie'}], 'ResponseMetadata': {'RetryAttempts': 0,'HTTPStatusCode': 200, 'RequestId': '39737a42-e9cf-11e6-b837-ef727c7b4c2e', 'HTTPHeaders': {'date': 'Fri, 03 Feb 2017 05:11:32 GMT','x-amzn-requestid': '39737a42-e9cf-11e6-b837-ef727c7b4c2e','content-length': '302','content-type': 'application/x-amz-json-1.1','connection': 'keep-alive'}}}"

