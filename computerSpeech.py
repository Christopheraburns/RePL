# 2/3/17 The Computerspeech module will coordinate all activites that require speech from AWS Polly service
# Chris Burns @Forecast_Cloudy

# TODO: Incorporate a grammar library for proper grammar when speaking results of commands
# TODO: Take a look at this one:
# TODO: pip install --user --upgrade grammar-check
# TODO: https://pypi.python.org/pypi/grammar-check

import log
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
import os
import pygame.mixer
from contextlib import closing
import time

# Create an AWS Client obj
session = Session(profile_name="default")
polly = session.client("polly")

# Create a logger object
logger = log.rLog(False)


def callAudible(wav):
    pygame.init()
    if wav.lower() == "ack":
        pygame.mixer.music.load('audio/ack.wav')
        pygame.mixer.music.play()
        time.sleep(1)
    elif wav.lower() == "limit":
        pygame.mixer.music.load('audio/limit.wav')
        pygame.mixer.music.play()


def pollySays(value):
    try:
        logger.LogThis("__main__.py: Contacting polly to convert command to voice")
        response = polly.synthesize_speech(Text=value, OutputFormat="ogg_vorbis", VoiceId="Emma")
        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                output = os.path.join("speech.ogg")
                try:
                    # Open a file for writing the output as a binary stream
                    logger.LogThis("computeSpeech.py: writing the response to speech.ogg.")
                    with open(output, "wb") as file:
                        file.write(stream.read())
                except IOError as e:
                    # Could not write to file
                    # callAudible("limit")
                    logger.LogError("computeSpeech.py: IOError: {}".format(e.message))

            pygame.mixer.init()
            pygame.mixer.music.load('speech.ogg')
            pygame.mixer.music.play()
            time.sleep(1)
        else:
            # The response didn't contain audio data, exit gracefully
            logger.LogThis("computeSpeech.py: Response did not contain audio!")

    except(BotoCoreError, ClientError) as e:
        callAudible("limit")
        logger.LogError("computeSpeech.py: Error: {}".format(e))
    except KeyboardInterrupt:
        logger.LogThis("computeSpeech.py: PollySays(): Ctrl-C interrupt")


# Use some pre-recorded soundbytes to fill in time delay gaps
def playAudio(audioFile):
    try:
        pygame.mixer.init()
        path = "audio/" + audioFile + ".ogg"
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        time.sleep(1)
    except Exception as e:
        logger.LogError("computerspeech.py: playAudio(): Unable to play:".format(e))
