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
import collections
import pyaudio
import snowboydetect
import time
try: #Attempt to Load RPi module - will only work on Pi
    import RPi.GPIO as GPIO
except ImportError as e:
        #logger.LogError(
        print("__main__.py: Cannot import the RPi module, install it with pip or this may not be a Raspberry Pi")


TOP_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_FILE = os.path.join(TOP_DIR, "resources/common.res")
DETECT_DING = os.path.join(TOP_DIR, "resources/ding.wav")
DETECT_DONG = os.path.join(TOP_DIR, "resources/dong.wav")
interrupted = False
model = "REPL.pmdl"
pygame.mixer.init()
ack = Sound("audio/ack.wav")
limit = Sound("audio/limit.wav")


def turnLEDoff():
    GPIO.output(40, GPIO.LOW)
    Sound.stop()

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted


#Create a logger object
logger = Log.rLog(True)


#Create an AWS Client obj
session = Session(profile_name="default")
polly = session.client("polly")

#intialize the Speech Recognition engine
r = sr.Recognizer()
m = sr.Microphone()

#initialize the Robot Library
Robot = mf.Body()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(40, GPIO.OUT)
GPIO.output(40, GPIO.HIGH)

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

class RingBuffer(object):
    """Ring buffer to hold audio from PortAudio"""
    def __init__(self, size = 4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        """Adds data to the end of buffer"""
        self._buf.extend(data)

    def get(self):
        """Retrieves data from the beginning of buffer and clears it"""
        tmp = ''.join(self._buf)
        self._buf.clear()
        return tmp

class HotwordDetector(object):
    """
    Snowboy decoder to detect whether a keyword specified by `decoder_model`
    exists in a microphone input stream.

    :param decoder_model: decoder model file path, a string or a list of strings
    :param resource: resource file path.
    :param sensitivity: decoder sensitivity, a float of a list of floats.
                              The bigger the value, the more senstive the
                              decoder. If an empty list is provided, then the
                              default sensitivity in the model will be used.
    :param audio_gain: multiply input volume by this factor.
    """
    def __init__(self, decoder_model,
                 resource=RESOURCE_FILE,
                 sensitivity=[],
                 audio_gain=1):

        tm = type(decoder_model)
        ts = type(sensitivity)
        if tm is not list:
            decoder_model = [decoder_model]
        if ts is not list:
            sensitivity = [sensitivity]
        model_str = ",".join(decoder_model)

        self.detector = snowboydetect.SnowboyDetect(
            resource_filename=resource, model_str=model_str)
        self.detector.SetAudioGain(audio_gain)
        self.num_hotwords = self.detector.NumHotwords()

        if len(decoder_model) > 1 and len(sensitivity) == 1:
            sensitivity = sensitivity*self.num_hotwords
        if len(sensitivity) != 0:
            assert self.num_hotwords == len(sensitivity), \
                "number of hotwords in decoder_model (%d) and sensitivity " \
                "(%d) does not match" % (self.num_hotwords, len(sensitivity))
        sensitivity_str = ",".join([str(t) for t in sensitivity])
        if len(sensitivity) != 0:
            self.detector.SetSensitivity(sensitivity_str)


    def start(self, detected_callback=ack.play,
              interrupt_check=lambda: False,
              sleep_time=0.03):
        """
        Start the voice detector. For every `sleep_time` second it checks the
        audio buffer for triggering keywords. If detected, then call
        corresponding function in `detected_callback`, which can be a single
        function (single model) or a list of callback functions (multiple
        models). Every loop it also calls `interrupt_check` -- if it returns
        True, then breaks from the loop and return.

        :param detected_callback: a function or list of functions. The number of
                                      items must match the number of models in
                                      `decoder_model`.
        :param interrupt_check: a function that returns True if the main loop
                                    needs to stop.
        :param float sleep_time: how much time in second every loop waits.
        :return: None
        """

        def audio_callback(in_data, frame_count, time_info, status):
            self.ring_buffer.extend(in_data)
            play_data = chr(0) * len(in_data)
            return play_data, pyaudio.paContinue

        self.ring_buffer = RingBuffer(
            self.detector.NumChannels() * self.detector.SampleRate() * 5)
        self.audio = pyaudio.PyAudio()
        self.stream_in = self.audio.open(
            input=True, output=False,
            format=self.audio.get_format_from_width(
                self.detector.BitsPerSample() / 8),
            channels=self.detector.NumChannels(),
            rate=self.detector.SampleRate(),
            frames_per_buffer=2048,
            stream_callback=audio_callback)


        if interrupt_check():
            logger.LogDebug("snowboydecoder.py: start(): detect voice return")
            return

        tc = type(detected_callback)
        if tc is not list:
            detected_callback = [detected_callback]
        if len(detected_callback) == 1 and self.num_hotwords > 1:
            detected_callback *= self.num_hotwords

        assert self.num_hotwords == len(detected_callback), \
            "Error: hotwords in your models (%d) do not match the number of " \
            "callbacks (%d)" % (self.num_hotwords, len(detected_callback))

        logger.LogDebug("snowboydecoder.py: start(): detecting...")

        while True:
            if interrupt_check():
                logger.LogDebug("snowboydecoder.py: start(): detect voice break")
                break
            data = self.ring_buffer.get()
            if len(data) == 0:
                time.sleep(sleep_time)
                continue

            ans = self.detector.RunDetection(data)
            if ans == -1:
                logger.LogWarning("snowboydecoder.py: start(): Error initializing streams or reading audio data")
            elif ans == -2:
                pass
            elif ans > 0:
                message = "Keyword " + str(ans) + " detected at time: "
                message += time.strftime("%Y-%m-%d %H:%M:%S",
                                         time.localtime(time.time()))
                logger.LogThis(message)
                callback = detected_callback[ans - 1]
                if callback is not None:
                    callback()

        logger.LogDebug("snowboydecoder.py: start(): finished.")


    def terminate(self):
        """
        Terminate audio stream. Users cannot call start() again to detect.
        :return: None
        """
        self.stream_in.stop_stream()
        self.stream_in.close()
        self.audio.terminate()

detector = HotwordDetector(model, sensitivity=0.5)

def processCmd(command, voice):
    try:
        cmdRecognized = True
        if command:
            logger.LogThis("__main__.py: recieved command: {}".format(command))
            command = command.lower()
            if "right" in command or "write" in command:
                logger.LogThis("__main__.py: Keyword RIGHT (or WRITE) detected, creating rightArm object")
                rightArm = Robot.RightArm()
                if "up" in command or "raise" in command:
                    logger.LogThis("__main__.py: OPTION 1: Keyword UP (or RAISE) detected, calling rightArm.moveUp()")
                    rightArm.moveUp()
                elif "down" in command or "lower" in command:
                    logger.LogThis("__main__.py: OPTION 2: Keyword DOWN (or Lower) detected, calling rightArm.moveDown()")
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
                else:
                    cmdRecognized = False
            elif "left" in command:
                logger.LogThis("__main__.py: Keyword LEFT detected, creating leftArm object")
                leftArm = Robot.LeftArm()
                if "up" in command or "raise" in command:
                    logger.LogThis("__main__.py: OPTION 6 :Keyword UP detected, calling leftArm.moveUp()")
                    leftArm.moveUp()
                elif "down" in command or "lower" in command:
                    logger.LogThis("__main__.py: OPTION 7: Keyword DOWN (or lower) detected, calling leftArm.moveDown()")
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
                else:
                    cmdRecognized = False
            elif "both" in command or "arms" in command:
                logger.LogThis("__main__.py: Keyword BOTH or ARMS detected, creating leftArm & rightArm objects")
                rightArm = Robot.RightArm()
                leftArm = Robot.LeftArm()
                if "up" in command or "raise" in command:
                    logger.LogThis("__main__.py: OPTION 11: Keyword UP or RAISE detected, calling leftArm.moveUp() & rightArm.moveUp()")
                    leftArm.moveUp()
                    rightArm.moveUp()
                elif "down" in command or "lower" in command:
                    logger.LogThis("__main__.py: OPTION 12: Keyword DOWN (or lower) detected, calling leftArm.moveDown() & rightArm.moveDown()")
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
                else:
                    cmdRecognized = False
            elif 'help' in command:
                showHelp()
            elif 'exit' in command:
                exit()
            elif "identify" in command:
                cv.Vision.takeSinglePicture()
                response = cv.Vision.callRekognition()
                pollySays(response)
            elif "what" in command and "is" in command and "this" in command: #call detect labels
                cv.Vision.takeSinglePicture()
                response = cv.Vision.callRekognition()
                pollySays(response)

            else:
                cmdRecognized = False

            if not cmdRecognized:
                if voice:
                    pollySays("I don't understand " + command)
        else:
            logger.LogError("__main__.py: processCmd(): Nothing returned from Voice to Text service!")

        if not voice:
            main(False)
    except KeyboardInterrupt:
        logger.LogThis("__main__.py:  processCmd() CTRL+C pressed.")
        exit()

def pollySays(value):
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
    except KeyboardInterrupt:
        logger.LogThis("__main__.py: PollySays(): Ctrl-C interrupt")
        exit()

def listenVoiceCmd():
    strValue = None
    try:
        detector.terminate()  #Turn off snowboy to allow sf to access the mic
        timer = 1
        while timer < 10: #creat timer
            logger.LogThis("__main__.py: NLU Service starting...silence please..")
            with m as source: r.adjust_for_ambient_noise(source)
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
                    logger.LogThis("Re-enabling SnowBoy")
                    break
                except sr.UnknownValueError as e:
                    processCmd("I didn't understand that", True)
                    limit.play()
                    logger.LogError("__main__.py: TranslateServiceError: Unable to translate audio: {}".format(e.message))
                except sr.RequestError as e:
                    limit.play()
                    logger.LogError("__main__.py: TranslateServiceError: Unable to access NLP service {}".format(e.message))
                break
            wakeOnKeyword()# turn snowboy back on
            time.sleep(1)
            timer = timer + 1

        wakeOnKeyword()  # turn snowboy back on

    except KeyboardInterrupt:
        logger.LogThis("__main__.py: listenVoiceCmd(): Ctrl+C sig received. Exiting")
        exit()


def wakeOnKeyword():
    try:
        logger.LogDebug("Activating SnowBoy")
        signal.signal(signal.SIGINT, signal_handler)
        global detector
        detector.start(detected_callback=listenVoiceCmd,
                       interrupt_check=interrupt_callback,
                       sleep_time=0.03)

    except Exception as e:
        limit.play()
        logger.LogError("__main__.py: wakeOnKeyword(): Error: {}".format(e))
    except KeyboardInterrupt:
        logger.LogThis("__main__.py: wakeOnKeyword(): Ctrl-C interrupt")
        exit()

#Main - look for the voice argument, as well as the model file to use with Snowboy.
def main(init):
    try:
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
    except KeyboardInterrupt:
        logger.LogThis("__main__.py: main(): Ctrl-C interrupt")
        exit()


atexit.register(turnLEDoff)

if __name__ == "__main__":
    main(True)