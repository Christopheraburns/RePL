# 2/3/17
# Chris Burns @Forecast_Cloudy
"""
    This file holds logic for processing a command, including alll possible commands to date as well as the function call
    to the appropriate module.
"""
import log
import time
import os
import computerVision as cv
import computerSpeech as cs
import sys
import ast
import paho.mqtt.client as mqtt

# Create a logger object
logger = log.rLog(False)


def on_connect(client, userdata, flags, rc):
    print("connected to message queue with result code "+str(rc))
    client.subscribe([("REPL_MF/#", 0), ("REPL_PERIPHERALS/#", 0)])


# Callback for when a message is received from the server
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

# Set up message queue
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("127.0.0.1", 1883, 60)
client.loop_forever


def showHelp():
    if os.path.exists("help"):
        with open("help") as f:
            hcontent = f.readlines()
            hcontent = [x.strip() for x in hcontent]
            for line in hcontent:
                print(line)
    else:
        cs.callAudible("limit")
        logger.LogError("cortex.py: Help file is missing - cannot display commands")


def loadJointMap():
    if os.path.exists("JOINTMAP"):
        print("cortex.py::loadJointMap(): JOINTMAP file found, loading...")
        try:
            with open("JOINTMAP") as f:
                content = f.read()
                joints = ast.literal_eval(content)
                return joints
        except Exception as e:
            print("cortex.py::loadJointMap(): Error loading JOINTMAP - {}".format(e.message))
    else:
        print("cortex.py::loadJointMap(): Unable to find/or open the JOINTMAP")

# Try loading this one time at module load. -
# TODO add logic to reload JOINTMAP on command
JOINTMAP = loadJointMap()


# Run at Startup to "center" all servos.  Will also run whenever the command "center" is given
def center():
    try:
        JOINTMAP = loadJointMap()
        if JOINTMAP is not None:
            for joint in JOINTMAP["Joints"]:
                # Move all joints to their respective START_POS
                logger.LogThis("cortex.py::center(): Centering {}".format(joint["Name"]))
                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(joint["START_POS"]) +"}")
                time.sleep(1)
        else:
            print("cortex.py::center(): Unable to Load JOINTMAP correctly or JOINTMAP is empty")
            cs.pollySays("I am unable to load my JOINTMAP file correctly")
    except Exception as e:
        logger.LogError("cortex.py::center(): Error: {}".format(e.message))


def processCmd(command, voice):
    try:
        cmdRecognized = True
        if command:
            command = command.lower()
            logger.LogThis("cortex.py::processCmd(): received command: {}".format(command))
            if "center" in command or "centre" in command or "wake up" in command or "reset" in command:  # center all servos
                logger.LogThis("cortex.py::processCmd(): CENTER detected, calling center function")
                center()
            elif "look" in command:
                logger.LogThis("Level 1 Keyword 'LOOK' detected")
                if "right" in command or "write" in command:                                #LOOK RIGHT
                    logger.LogThis("Level 2 Keyword 'RIGHT' detected")
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "NECK_ROTATION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["LOW"]) + "}")
                elif "left" in command:                                                     #LOOK LEFT
                    logger.LogThis("Level 1 Keyword 'LEFT' detected")
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "NECK_ROTATION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["HIGH"]) + "}")
                elif "straight" in command or "strait" in command or "at me" in command:                          #LOOK Straight ahead
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "NECK_ROTATION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["MIDDLE"]) + "}")
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "NECK_ELEVATION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["MIDDLE"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                elif "up" in command or lookup in command:                                                       #LOOK UP
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "NECK_ELEVATION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["LOW"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["LOW"])
                elif "down" in command:                                 #LOOK DOWN
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "NECK_ELEVATION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["HIGH"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["HIGH"])
                else:
                    cmdRecognized = False
            elif "arm" in command:
                if "right" in command or "write" in command:
                    if "up" in command or "raise" in command:                               #Raise RIGHT ARM
                        for joint in JOINTMAP["Joints"]:
                            if joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                    joint["HIGH"]) + "}")
                                #mf.executeMovement(joint["GPIO"], joint["HIGH"])
                    elif "down" in command or "lower" in command:                           #Lower the RIGHT ARM
                        for joint in JOINTMAP["Joints"]:
                            if joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                    joint["LOW"]) + "}")
                                #mf.executeMovement(joint["GPIO"], joint["LOW"])
                    elif "out" in command:                                                  #Extend the RIGHT ARM
                        for joint in JOINTMAP["Joints"]:
                            if joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                    joint["MIDDLE"]) + "}")
                               #mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                    elif "bend" in command:                                                 #Bend the RIGHT ARM
                        for joint in JOINTMAP["Joints"]:
                            if joint["Name"] == "RIGHT_ELBOW_EXTENSION":
                                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                    joint["HIGH"]) + "}")
                                #mf.executeMovement(joint["GPIO"], joint["HIGH"])
                    elif "straight" in command or "straighten":                             #Straighten the RIGHT ARM
                        for joint in JOINTMAP["Joints"]:
                            if joint["Name"] == "RIGHT_ELBOW_EXTENSION":
                                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                    joint["MIDDLE"]) + "}")
                                #mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                    else:
                        cmdRecognized = False
                elif "left" in command:
                    if "up" in command or "raise" in command:                               #Raise RIGHT ARM
                        for joint in JOINTMAP["Joints"]:
                            if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                    joint["HIGH"]) + "}")
                                #mf.executeMovement(joint["GPIO"], joint["HIGH"])
                    elif "down" in command or "lower" in command:                           #Lower the RIGHT ARM
                        for joint in JOINTMAP["Joints"]:
                            if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                    joint["LOW"]) + "}")
                                #mf.executeMovement(joint["GPIO"], joint["LOW"])
                    elif "out" in command:                                                  #Extend the RIGHT ARM
                        for joint in JOINTMAP["Joints"]:
                            if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                    joint["MIDDLE"]) + "}")
                                #mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                    elif "bend" in command:                                                 #Bend the RIGHT ARM
                        for joint in JOINTMAP["Joints"]:
                            if joint["Name"] == "LEFT_ELBOW_EXTENSION":
                                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                    joint["LOW"]) + "}")
                                #mf.executeMovement(joint["GPIO"], joint["LOW"])
                    elif "straight" in command or "straighten" in command:                             #Straighten the RIGHT ARM
                        for joint in JOINTMAP["Joints"]:
                            if joint["Name"] == "LEFT_ELBOW_EXTENSION":
                                client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                    joint["MIDDLE"]) + "}")
                                #mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                    else:
                        cmdRecognized = False
            elif "both" in command or "arms" in command:
                if "up" in command or "raise" in command or "rays" in command:                               #Raise BOTH ARMS
                    #Raise both Arms
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["LOW"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["LOW"])
                        elif joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["HIGH"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["HIGH"])
                elif "down" in command or "lower" in command:                           #put BOTH ARMS down
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["HIGH"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["HIGH"])
                        elif joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["LOW"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["LOW"])
                elif "out" in command or "extend" in command:                                      #Extend BOTH ARMS
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["MIDDLE"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                        elif joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["MIDDLE"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                elif "bend" in command:                                                 #Bend BOTH ARMS
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "LEFT_ELBOW_EXTENSION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["LOW"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["LOW"])
                        elif joint["Name"] == "RIGHT_ELBOW_EXTENSION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["HIGH"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["HIGH"])
                elif "straight" in command or "straighten" in command or "straighter" in command:  #Straighten BOTH ARMS
                    for joint in JOINTMAP["Joints"]:
                        if joint["Name"] == "LEFT_ELBOW_EXTENSION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["MIDDLE"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                        elif joint["Name"] == "RIGHT_ELBOW_EXTENSION":
                            client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                                joint["MIDDLE"]) + "}")
                            #mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                else:
                        cmdRecognized = False
            elif "shut" in command and  "down" in command or "shutdown" in command \
                    or "terminate" in command \
                    or "terminator" in command \
                    or "shot down" in command:
                cs.playAudio("shuttingdown")
                # Lower her head to indicate shutdown mode
                for joint in JOINTMAP["Joints"]:
                    if joint["Name"] == "NECK_ELEVATION":
                        client.publish("REPL_MF", "{\"pin\":" + str(joint["GPIO"]) + ",\"pos\":" + str(
                            joint["HIGH"]) + "}")
                        #mf.executeMovement(joint["GPIO"], joint["HIGH"])
                sys.exit()
            elif 'help' in command:
                showHelp()
            elif "identify" in command:
                cv.Vision.takeSinglePicture()
                response = cv.Vision.callRekognition()
                cs.pollySays(response)
            elif "what is this" in command or "what do you see" in command:  # call detect labels
                cv.Vision.takeSinglePicture()
                cs.playAudio("interesting")
                response = cv.Vision.callRekognition()
                cs.pollySays(response)
            elif "wake up" in command:
                center()
                cs.playAudio("hello")
            else:
                cmdRecognized = False

            if not cmdRecognized:
                    if voice:
                        cs.pollySays("I don't understand " + command)
            #else:
                #logger.LogError("cortex: processCmd(): Nothing returned from Voice to Text service!")
    except KeyboardInterrupt:
        logger.LogThis("cortex:  processCmd() CTRL+C pressed.")
