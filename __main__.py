import motorFunctions as mf
import computerVision as cv
import speechrecognition as sr
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os.path
import sys
import subprocess
import Log
import time
from tempfile import gettempdir

#Create a logger object
logger = Log.rLog(True)

DEBUG = False

#Create an AWS Client obj
session = Session(profile_name="default")
polly = session.client("polly")
r = sr.Recognizer()
m = sr.Microphone()
Robot = mf.Body();

#Does not get logged
def showHelp():
    if os.path.exists("help"):
        with open("help") as f:
            hcontent = f.readlines()
            hcontent = [x.strip() for x in hcontent]
            for line in hcontent:
                print(line)
    else:
        logger.LogError("__main__.py: Help file is missing - cannot display commands")


def processCmd(command, voice):
    if command:
        logger.LogThis("recieved command: {}".format(command))
        command = command.lower()
        if "right" in command:
            if DEBUG: logger.LogDebug("keyword RIGHT detected, creating rightArm object")
            rightArm = Robot.RightArm()
            if "up" in command:
                if DEBUG: logger.LogDebug("keyword UP found, calling rightArm.moveUp()")
                rightArm.moveUp()
            elif "down" in command:
                if DEBUG: logger.LogDebug("keyword DOWN found, calling rightArm.moveDown()")
                rightArm.moveDown()
            elif "out" in command:
                if DEBUG: logger.LogDebug("keyword OUT found, calling rightArm.moveParallel()")
                rightArm.moveParallel()
            elif "bend" in command:
                if DEBUG: logger.LogDebug("keyword BEND found, calling rightArm.bend()")
                rightArm.bend()
            elif "straight" in command:
                if DEBUG: logger.LogDebug("keyword STRAIGHT found, calling rightArm.straighten()")
                rightArm.straighten()
        elif "left" in command:
            if DEBUG: logger.LogDebug("keyword LEFT found, creating leftArm object")
            leftArm = Robot.LeftArm()
            if "up" in command:
                if DEBUG: logger.LogDebug("keyword UP found, calling leftArm.moveUp()")
                leftArm.moveUp()
            elif "down" in command:
                if DEBUG: logger.LogDebug("keyword DOWN found, calling leftArm.moveDown()")
                leftArm.moveDown()
            elif "out"in command:
                if DEBUG: logger.LogDebug("keyword OUT found, calling leftArm.moveParallel()")
                leftArm.moveParallel()
            elif "bend" in command:
                if DEBUG: logger.LogDebug("keyword BEND found, calling leftArm.bend()")
                leftArm.bend()
            elif "straight" in command:
                if DEBUG: logger.LogDebug("keyword STRAIGHT found, calling leftArm.straighten()")
                leftArm.straighten()
        elif "both" in command:
            if DEBUG: logger.LogDebug("keyword BOTH found, creating leftArm & rightArm objects")
            rightArm = Robot.RightArm()
            leftArm = Robot.LeftArm()
            if "up" in command:
                if DEBUG: logger.LogDebug("keyword UP found, calling leftArm.moveUp() & rightArm.moveUp()")
                leftArm.moveUp()
                rightArm.moveUp()
            elif "down" in command:
                if DEBUG: logger.LogDebug("keyword DOWN found, calling leftArm.moveDown() & rightArm.moveDown()")
                leftArm.moveDown()
                rightArm.moveDown()
            elif "out" in command:
                if DEBUG: logger.LogDebug("keyword OUT found, calling leftArm.moveParallel() & rightArm.moveParallel()")
                leftArm.moveParallel()
                rightArm.moveDown()
            elif "bend" in command:
                if DEBUG: logger.LogDebug("keyword BEND found, calling leftArm.bend() & rightArm.bend()")
                leftArm.bend()
                rightArm.bend()
            elif "straight" in command:
                if DEBUG: logger.LogDebug("keyword STRAIGHT found, calling leftArm.straighten() & rightArm.straighten()")
                leftArm.straighten()
                rightArm.straighten()
        elif 'help' in command:
            showHelp()
        elif 'exit' in command:
            exit()
        elif "identify" in command:
            cv.Vision.takeSinglePicture()
    else:
        logger.LogError("Nothing returned from Voice to Text service!")

    if not voice:
        main(False)


def listenVoiceCmd():
    strValue = None
    try:
        logger.LogThis("__main__.py: NLU Service starting...silence please..")
        with m as source: r.adjust_for_ambient_noise((source))
        logger.LogThis("__main__.py: Set min energy threshold to {}".format(r.energy_threshold))
        while True:
            logger.LogThis("__main__.py: You may now issue voice commands!")
            with m as source: audio = r.listen(source)

            logger.LogThis ("__main__.py: Received audio data. Attempting to translate Voice to Text now...")
            try:
                #value = r.recognize_sphinx(audio)
                value = r.recognize_google(audio)

                if str is bytes:  # this version of Python uses bytes for strings (Python 2)
                    #print(u"You said {}".format(value).encode("utf-8"))
                    strValue = value.encode("utf-8")
                else:  # this version of Python uses unicode for strings (Python 3+)
                    #print("You said {}".format(value))
                    strValue = value

                logger.LogThis("__main__.py: Translation Service returned: {}".format(strValue))
                processCmd(strValue, True)
                time.sleep(5)
            except sr.UnknownValueError as e:
                logger.LogError("__main__.py: TranslateServiceError: Unable to translate audio: {}".format(e.message))
                pass
            except sr.RequestError as e:
                logger.LogError("__main__.py: TranslateServiceError: Unable to access NLP service {}".format(e.message))
                pass

    except KeyboardInterrupt:
        sys.exit(-1)

    main(False)


def main(init):

    if len(sys.argv) == 1:
        if init:
            logger.LogThis("No parameters found, defaulting to manual mode.  Try -h for help")
    if "voice" in sys.argv:
        listenVoiceCmd()
    elif "help" in sys.argv:
        showHelp()
    elif "debug" in sys.argv:
        DEBUG = True
        Robot.debugMode(True)
    else:
        command = raw_input("Enter a command:")
        command = command.lower()
        processCmd(command)

def talkToPolly(strValue):
    try:
        response = polly.synthesize_speech(Text=strValue, OutputFormat="mp3", VoiceId="Emma")
        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                output = os.path.join("speech.mp3")
                try:
                    # Open a file for writing the output as a binary stream
                    logger.LogThis("__main__.py: writing the response to MP3 file...")
                    with open(output, "wb") as file:
                        file.write(stream.read())
                except IOError as e:
                    # Could not write to file, exit gracefully
                    logger.LogError(e.message)
                    sys.exit(-1)
        else:
            # The response didn't contain audio data, exit gracefully
            logger.LogThis("__main__.py: Response did not contain audio!")
            sys.exit(-1)

            # play the audio using the platform's default player
            if sys.platform == "win32":
                os.startfile(output)
            else:
                # The following works on mac and linux. (Darwin = mac, xdg-open = linux).
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, output])
    except(BotoCoreError, ClientError) as e:
        logger.LogError("Error: {}".format(e))
        sys.exit(-1)
#Main
if __name__ == "__main__":
    main(True)