import motorFunctions as mf
import computerVision as cv
import speechrecognition as sr
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os.path
import sys
import Log
import pygame.mixer
from pygame.mixer import Sound
import atexit
import signal
import snowboydecoder

interrupted = False
model = None

try: #Attempt to Load RPi module - will only work on Pi
    import RPi.GPIO as GPIO
except ImportError as e:
        #logger.LogError(
        print("__main__.py: Cannot import the RPi module, install it with pip or this may not be a Raspberry Pi")

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted



#Create a logger object
logger = Log.rLog(True)
limit = Sound("audio/limit.wav")

#Create an AWS Client obj
session = Session(profile_name="default")
polly = session.client("polly")
r = sr.Recognizer()
m = sr.Microphone()
Robot = mf.Body()


GPIO.setmode(GPIO.BOARD)
GPIO.setup(40, GPIO.OUT)
GPIO.output(40, GPIO.HIGH)


#Does not get logged
def showHelp():
    if os.path.exists("help"):
        with open("help") as f:
            hcontent = f.readlines()
            hcontent = [x.strip() for x in hcontent]
            for line in hcontent:
                print(line)
    else:
        limit.play()
        logger.LogError("__main__.py: Help file is missing - cannot display commands")


def processCmd(command, voice):
    if command:
        logger.LogThis("__main__.py: recieved command: {}".format(command))
        command = command.lower()
        if "right" in command or "write" in command:
            logger.LogThis("__main__.py: Keyword RIGHT (or WRITE) detected, creating rightArm object")
            rightArm = Robot.RightArm()
            if "up" in command or "raise" in command:
                logger.LogThis("__main__.py: OPTION 1: Keyword UP (or RAISE) detected, calling rightArm.moveUp()")
                rightArm.moveUp()
            elif "down" in command:
                logger.LogThis("__main__.py: OPTION 2: Keyword DOWN detected, calling rightArm.moveDown()")
                rightArm.moveDown()
            elif "out" in command:
                logger.LogThis("__main__.py: OPTION 3: Keyword OUT detected, calling rightArm.moveParallel()")
                rightArm.moveParallel()
            elif "bend" in command:
                logger.LogThis("__main__.py: OPTION 4: Keyword BEND detected, calling rightArm.bend()")
                rightArm.bend()
            elif "straight" in command:
                logger.LogThis("__main__.py: OPTION 5: Keyword STRAIGHT detected, calling rightArm.straighten()")
                rightArm.straighten()
        elif "left" in command:
            logger.LogThis("__main__.py: Keyword LEFT detected, creating leftArm object")
            leftArm = Robot.LeftArm()
            if "up" in command or "raise" in command:
                logger.LogThis("__main__.py: OPTION 6 :Keyword UP detected, calling leftArm.moveUp()")
                leftArm.moveUp()
            elif "down" in command:
                logger.LogThis("__main__.py: OPTION 7: Keyword DOWN detected, calling leftArm.moveDown()")
                leftArm.moveDown()
            elif "out"in command:
                logger.LogThis("__main__.py: OPTION 8: Keyword OUT detected, calling leftArm.moveParallel()")
                leftArm.moveParallel()
            elif "bend" in command:
                logger.LogThis("__main__.py: OPTION 9: Keyword BEND detected, calling leftArm.bend()")
                leftArm.bend()
            elif "straight" in command:
                logger.LogThis("__main__.py: OPTION 10: Keyword STRAIGHT detected, calling leftArm.straighten()")
                leftArm.straighten()
        elif "both" in command or "arms" in command:
            logger.LogThis("__main__.py: Keyword BOTH or ARMS detected, creating leftArm & rightArm objects")
            rightArm = Robot.RightArm()
            leftArm = Robot.LeftArm()
            if "up" in command or "raise" in command:
                logger.LogThis("__main__.py: OPTION 11: Keyword UP or RAISE detected, calling leftArm.moveUp() & rightArm.moveUp()")
                leftArm.moveUp()
                rightArm.moveUp()
            elif "down" in command:
                logger.LogThis("__main__.py: OPTION 12: Keyword DOWN detected, calling leftArm.moveDown() & rightArm.moveDown()")
                leftArm.moveDown()
                rightArm.moveDown()
            elif "out" in command:
                logger.LogThis("__main__.py: OPTION 13: Keyword OUT detected, calling leftArm.moveParallel() & rightArm.moveParallel()")
                leftArm.moveParallel()
                rightArm.moveParallel()
            elif "bend" in command:
                logger.LogThis("__main__.py: OPTION 14: Keyword BEND detected, calling leftArm.bend() & rightArm.bend()")
                leftArm.bend()
                rightArm.bend()
            elif "straight" in command:
                logger.LogThis("__main__.py: OPTION 15: Keyword STRAIGHT detected, calling leftArm.straighten() & rightArm.straighten()")
                leftArm.straighten()
                rightArm.straighten()
        elif 'help' in command:
            showHelp()
        elif 'exit' in command:
            exit()
        elif "identify" in command:
            cv.Vision.takeSinglePicture()
        else:
            pass
    else:
        logger.LogError("__main__.py: Nothing returned from Voice to Text service!")

    if not voice:
        main(False)


def repeatCmd(value):
    try:
        logger.LogThis("__main__.py: Contacting polly to convert command to voice")
        response = polly.synthesize_speech(Text=value, OutputFormat="ogg_vorbis", VoiceId="Emma")
        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                output = os.path.join("speech.ogg")
                try:
                    # Open a file for writing the output as a binary stream
                    logger.LogThis("__main__.py: writing the response to speech.ogg.")
                    with open(output, "wb") as file:
                        file.write(stream.read())

                        """"# play the audio using the platform's default player
                        if sys.platform == "win32":
                            os.startfile(output)
                        else:
                            # The following works on mac and linux. (Darwin = mac, xdg-open = linux).
                            opener = "open" if sys.platform == "darwin" else "xdg-open"
                            subprocess.call([opener, output])"""

                    pygame.mixer.init()
                    cmd = Sound("speech.ogg")
                    cmd.play()
                except IOError as e:
                    # Could not write to file
                    limit.play()
                    logger.LogError("__main__.py: IOError: {}".format(e.message))
        else:
            # The response didn't contain audio data, exit gracefully
            logger.LogThis("__main__.py: Response did not contain audio!")

    except(BotoCoreError, ClientError) as e:
        limit.play()
        logger.LogError("__main__.py: Error: {}".format(e))


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

                logger.LogThis("__main__.py: Vocie-to-Text translation Service returned: {}".format(strValue))
                processCmd(strValue, True)
                repeatCmd(strValue)
            except sr.UnknownValueError as e:
                limit.play()
                logger.LogError("__main__.py: TranslateServiceError: Unable to translate audio: {}".format(e.message))
                pass
            except sr.RequestError as e:
                limit.play()
                logger.LogError("__main__.py: TranslateServiceError: Unable to access NLP service {}".format(e.message))
                pass

    except KeyboardInterrupt:
        logger.LogThis("__main__.py: listenVoiceCmd(): Ctrl+C sig received. Exiting")
        exit(-1)

    wakeOnKeyword()


def wakeOnKeyword():
    try:
        signal.signal(signal.SIGINT, signal_handler)
        detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5)

        detector.start(detected_callback=wakeOnKeyword,
                       interrupt_check=interrupt_callback,
                       sleep_time=0.03)

        detector.terminate()

    except Exception as e:
        limit.play()
        logger.LogError("__main__.py: wakeOnKeyword(): Error: {}".format(e))



def main(init):
    if len(sys.argv) == 1:
        if init:
            logger.LogThis("__main__.py: No parameters or model file specified, defaulting to manual mode.  Try -h for help")
        command = raw_input("Enter a command:")
        command = command.lower()
        processCmd(command, False)
    elif "help" in sys.argv:
        showHelp()
    else:
        global model
        model = sys.argv[1]
        wakeOnKeyword()


        #listenVoiceCmd()



def turnLEDoff():
    GPIO.output(40, GPIO.LOW)


atexit.register(turnLEDoff)
#Main
if __name__ == "__main__":
    main(True)