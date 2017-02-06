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


#Create a logger object
logger = log.rLog(False)

#Create motorfunction instance
Robot = mf.Body()


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

def processCmd(command, voice):
    try:
        cmdRecognized = True
        if command:
            logger.LogThis("cortex.py: recieved command: {}".format(command))
            command = command.lower()

            if command == "center": #center all servos
                rightArm = Robot.RightArm()
                leftArm = Robot.LeftArm()
                neck = Robot.Neck()
            if "right" in command or "write" in command:
                logger.LogThis("cortex.py: Keyword RIGHT (or WRITE) detected, creating rightArm object")
                rightArm = Robot.RightArm()
                if "up" in command or "raise" in command:
                    logger.LogThis("cortex.py: OPTION 1: Keyword UP (or RAISE) detected, calling rightArm.moveUp()")
                    rightArm.moveUp()
                elif "down" in command or "lower" in command:
                    logger.LogThis("cortex.py: OPTION 2: Keyword DOWN (or Lower) detected, calling rightArm.moveDown()")
                    rightArm.moveDown()
                elif "out" in command:
                    logger.LogThis("cortex.py: OPTION 3: Keyword OUT detected, calling rightArm.moveParallel()")
                    rightArm.moveParallel()
                elif "bend" in command:
                    logger.LogThis("cortex.py: OPTION 4: Keyword BEND detected, calling rightArm.bend()")
                    rightArm.bend()
                elif "straight" in command:
                    logger.LogThis("cortex.py: OPTION 5: Keyword STRAIGHT detected, calling rightArm.straighten()")
                    rightArm.straighten()
                else:
                    cmdRecognized = False
            elif "left" in command:
                logger.LogThis("cortex.py: Keyword LEFT detected, creating leftArm object")
                leftArm = Robot.LeftArm()
                if "up" in command or "raise" in command:
                    logger.LogThis("cortex.py: OPTION 6 :Keyword UP detected, calling leftArm.moveUp()")
                    leftArm.moveUp()
                elif "down" in command or "lower" in command:
                    logger.LogThis("cortex.py: OPTION 7: Keyword DOWN (or lower) detected, calling leftArm.moveDown()")
                    leftArm.moveDown()
                elif "out" in command:
                    logger.LogThis("cortex.py: OPTION 8: Keyword OUT detected, calling leftArm.moveParallel()")
                    leftArm.moveParallel()
                elif "bend" in command:
                    logger.LogThis("cortex.py: OPTION 9: Keyword BEND detected, calling leftArm.bend()")
                    leftArm.bend()
                elif "straight" in command:
                    logger.LogThis("cortex.py: OPTION 10: Keyword STRAIGHT detected, calling leftArm.straighten()")
                    leftArm.straighten()
                else:
                    cmdRecognized = False
            elif "both" in command or "arms" in command:
                logger.LogThis("cortex.py: Keyword BOTH or ARMS detected, creating leftArm & rightArm objects")
                rightArm = Robot.RightArm()
                leftArm = Robot.LeftArm()
                if "up" in command or "raise" in command:
                    logger.LogThis("cortex.py: OPTION 11: Keyword UP or RAISE detected, calling leftArm.moveUp() & rightArm.moveUp()")
                    leftArm.moveUp()
                    rightArm.moveUp()
                elif "down" in command or "lower" in command:
                    logger.LogThis("cortex.py: OPTION 12: Keyword DOWN (or lower) detected, calling leftArm.moveDown() & rightArm.moveDown()")
                    leftArm.moveDown()
                    rightArm.moveDown()
                elif "out" in command:
                    logger.LogThis("cortex.py: OPTION 13: Keyword OUT detected, calling leftArm.moveParallel() & rightArm.moveParallel()")
                    leftArm.moveParallel()
                    rightArm.moveParallel()
                elif "bend" in command:
                    logger.LogThis("cortex.py: OPTION 14: Keyword BEND detected, calling leftArm.bend() & rightArm.bend()")
                    leftArm.bend()
                    rightArm.bend()
                elif "straight" in command:
                    logger.LogThis("cortex.py: OPTION 15: Keyword STRAIGHT detected, calling leftArm.straighten() & rightArm.straighten()")
                    leftArm.straighten()
                    rightArm.straighten()
                else:
                    cmdRecognized = False
            elif "look" in command:
                neck = Robot.Neck()
                if "right" in command:
                    neck.lookRight()
                elif "left" in command:
                    neck.lookLeft()
                elif "forward" in command or "foreward" in command:
                    neck.lookForward()
                elif "up" in command:
                    neck.lookUp()
                elif "down" in command:
                    neck.lookDown()
                elif "straight" in command or "strait" in command:
                    neck.lookStraight()
                else:
                    cmdRecognized = False
            elif 'help' in command:
                showHelp()
            elif 'exit' in command:
                exit()
            elif "identify" in command:
                cv.Vision.takeSinglePicture()
                response = cv.Vision.callRekognition()
                cs.pollySays(response)
            elif "what is this" in command:  # call detect labels
                cv.Vision.takeSinglePicture()
                cs.playAudio("interesting")
                response = cv.Vision.callRekognition()
                cs.pollySays(response)
            elif "shut" in command and "down" in command \
                    or "terminate" in command \
                    or "terminator" in command \
                    or "shot down" in command:
                cs.playAudio("shuttingdown")
                sys.exit()
            else:
                cmdRecognized = False


            if not cmdRecognized:
                    if voice:
                        cs.pollySays("I don't understand " + command)
            else:
                logger.LogError("cortex: processCmd(): Nothing returned from Voice to Text service!")
    except KeyboardInterrupt:
        logger.LogThis("cortex:  processCmd() CTRL+C pressed.")
