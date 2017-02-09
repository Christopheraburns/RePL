# 2/3/17
# Chris Burns @Forecast_Cloudy
"""
    This file holds logic for processing a command, including alll possible commands to date as well as the function call
    to the appropriate module.
"""
import log
import motorFunctions as mf
import os
import computerVision as cv
import computerSpeech as cs
import sys
import ast

#Create a logger object
logger = log.rLog(False)

def callAudible(wav):
    cs.callAudible(wav)


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
                dJoints = ast.literal_eval(content)
                return dJoints
        except Exception as e:
            print("cortex.py::loadJointMap(): Error loading JOINTMAP - {}".format(e.message))
    else:
        print("cortex.py::loadJointMap(): Unable to find/or open the JOINTMAP")


#Run at Startup to "center" all servos.  Will also run whenever the command "center" is given
def center():
    try:
        dJoints = loadJointMap()
        for joint in dJoints["Joints"]:
            #Move all joints to their respective START_POS
            logger.LogThis("cortex.py::center(): Centering {}".format(joint["Name"]))
            mf.executeMovement(joint["GPIO"],joint["START_POS"])
        else:
            print("cortex.py::center(): Unable to Load JOINTMAP correctly or JOINTMAP is empty")
    except Exception as e:
        logger.LogError("cortex.py::center(): Error: {}".format(e.message))

def processCmd(command, voice):
    try:
        dJoints = loadJointMap()
        cmdRecognized = True
        if command:
            command = command.lower()
            logger.LogThis("cortex.py::processCmd(): received command: {}".format(command))
            if "center" in command or "centre" in command or "wake up" in command or "reset" in command:  # center all servos
                logger.LogThis("cortex.py::processCmd(): CENTER detected, calling center function")
                center()
            elif "look" in command:
                if "right" in command or "write" in command:                                #LOOK RIGHT
                    for joint in dJoints["Joints"]:
                        if joint["Name"] == "NECK_ROTATION":
                            mf.executeMovement(joint["GPIO"], joint["LOW"])
                elif "left" in command:                                                     #LOOK LEFT
                    for joint in dJoints["Joints"]:
                        if joint["Name"] == "NECK_ROTATION":
                            mf.executeMovement(joint["GPIO"], joint["HIGH"])
                elif "straight" in command or "strait" in command:                          #LOOK Straight ahead
                    for joint in dJoints["Joints"]:
                        if joint["Name"] == "NECK_ROTATION":
                            mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                elif "up" in command:                                                       #LOOK UP
                    for joint in dJoints["Joints"]:
                        if joint["Name"] == "NECK_ELEVATION":
                            mf.executeMovement(joint["GPIO"], joint["LOW"])
                elif "down" in command:                                                     #LOOK DOWN
                    for joint in dJoints["Joints"]:
                        if joint["Name"] == "NECK_ELEVATION":
                            mf.executeMovement(joint["GPIO"], joint["HIGH"])
                else:
                    cmdRecognized = False
            elif "arm" in command:
                if "right" in command or "write" in command:
                    if "up" in command or "raise" in command:                               #Raise RIGHT ARM
                        for joint in dJoints["Joints"]:
                            if joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                                mf.executeMovement(joint["GPIO"], joint["HIGH"])
                    elif "down" in command or "lower" in command:                           #Lower the RIGHT ARM
                        for joint in dJoints["Joints"]:
                            if joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                                mf.executeMovement(joint["GPIO"], joint["LOW"])
                    elif "out" in command:                                                  #Extend the RIGHT ARM
                        for joint in dJoints["Joints"]:
                            if joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                                mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                    elif "bend" in command:                                                 #Bend the RIGHT ARM
                        for joint in dJoints["Joints"]:
                            if joint["Name"] == "RIGHT_ELBOW_EXTENSION":
                                mf.executeMovement(joint["GPIO"], joint["HIGH"])
                    elif "straight" in command or "straighten":                             #Straighten the RIGHT ARM
                        for joint in dJoints["Joints"]:
                            if joint["Name"] == "RIGHT_ELBOW_EXTENSION":
                                mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                    else:
                        cmdRecognized = False
                elif "left" in command:
                    if "up" in command or "raise" in command:                               #Raise RIGHT ARM
                        for joint in dJoints["Joints"]:
                            if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                                mf.executeMovement(joint["GPIO"], joint["LOW"])
                    elif "down" in command or "lower" in command:                           #Lower the RIGHT ARM
                        for joint in dJoints["Joints"]:
                            if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                                mf.executeMovement(joint["GPIO"], joint["HIGH"])
                    elif "out" in command:                                                  #Extend the RIGHT ARM
                        for joint in dJoints["Joints"]:
                            if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                                mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                    elif "bend" in command:                                                 #Bend the RIGHT ARM
                        for joint in dJoints["Joints"]:
                            if joint["Name"] == "LEFT_ELBOW_EXTENSION":
                                mf.executeMovement(joint["GPIO"], joint["LOW"])
                    elif "straight" in command or "straighten":                             #Straighten the RIGHT ARM
                        for joint in dJoints["Joints"]:
                            if joint["Name"] == "LEFT_ELBOW_EXTENSION":
                                mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                    else:
                        cmdRecognized = False
            elif "both" in command or "arms" in command:
                if "up" in command or "raise" in command:                               #Raise BOTH ARMS
                    #Raise both Arms
                    for joint in dJoints["Joints"]:
                        if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                            mf.executeMovement(joint["GPIO"], joint["LOW"])
                        elif joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                            mf.executeMovement(joint["GPIO"], joint["HIGH"])
                elif "down" in command or "lower" in command:                           #put BOTH ARMS down
                    for joint in dJoints["Joints"]:
                        if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                            mf.executeMovement(joint["GPIO"], joint["HIGH"])
                        elif joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                            mf.executeMovement(joint["GPIO"], joint["LOW"])
                elif "out" in command or "extend":                                      #Extend BOTH ARMS
                    for joint in dJoints["Joints"]:
                        if joint["Name"] == "LEFT_SHOULDER_EXTENSION":
                            mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                        elif joint["Name"] == "RIGHT_SHOULDER_EXTENSION":
                            mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                elif "bend" in command:                                                 #Bend BOTH ARMS
                    for joint in dJoints["Joints"]:
                        if joint["Name"] == "LEFT_ELBOW_EXTENSION":
                            mf.executeMovement(joint["GPIO"], joint["LOW"])
                        elif joint["Name"] == "RIGHT_ELBOW_EXTENSION":
                            mf.executeMovement(joint["GPIO"], joint["HIGH"])
                elif "straight" in command or "straighten" in command or "straighter":  #Straighten BOTH ARMS
                    for joint in dJoints["Joints"]:
                        if joint["Name"] == "LEFT_ELBOW_EXTENSION":
                            mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                        elif joint["Name"] == "RIGHT_ELBOW_EXTENSION":
                            mf.executeMovement(joint["GPIO"], joint["MIDDLE"])
                else:
                        cmdRecognized = False
            elif "shut" in command and  "down" in command or "shutdown" in command \
                    or "terminate" in command \
                    or "terminator" in command \
                    or "shot down" in command:
                cs.playAudio("shuttingdown")
                #Lower her head to indicate shutdown mode
                for joint in dJoints["Joints"]:
                    if joint["Name"] == "NECK_ELEVATION":
                        mf.executeMovement(joint["GPIO"], joint["HIGH"])
                sys.exit()
            elif 'help' in command:
                showHelp()
            else:
                cmdRecognized = False

            if not cmdRecognized:
                    if voice:
                        cs.pollySays("I don't understand " + command)
            #else:
                #logger.LogError("cortex: processCmd(): Nothing returned from Voice to Text service!")
    except KeyboardInterrupt:
        logger.LogThis("cortex:  processCmd() CTRL+C pressed.")
