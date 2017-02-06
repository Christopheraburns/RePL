#2/3/17
#Chris Burns @Forecast_Cloudy
"""
    The Computerspeech module will coordinate all activites that require speech from AWS Polly service
"""
import Log
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
import os
import pygame.mixer
from pygame.mixer import Sound
from contextlib import closing

#Create an AWS Client obj
session = Session(profile_name="default")
polly = session.client("polly")

#Create a logger object
logger = Log.rLog(False)

def callAudible(wav):
    pygame.mixer.init()
    if wav.lower() == "ack":
        Sound("audio/ack.wav")
    elif wav.lower() == "limit":
        Sound("audio/limit.wav")


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
                    pygame.mixer.init()
                    cmd = Sound("speech.ogg")
                    cmd.play()
                except IOError as e:
                    # Could not write to file
                    callAudible("limit")
                    logger.LogError("computeSpeech.py: IOError: {}".format(e.message))
        else:
            # The response didn't contain audio data, exit gracefully
            logger.LogThis("computeSpeech.py: Response did not contain audio!")

    except(BotoCoreError, ClientError) as e:
        callAudible("limit")
        logger.LogError("computeSpeech.py: Error: {}".format(e))
    except KeyboardInterrupt:
        logger.LogThis("computeSpeech.py: PollySays(): Ctrl-C interrupt")

#Use some pre-recorded soundbytes to fill in time delay gaps
def playAudio(audioFile):
    try:
        pygame.mixer.init()
        path = "audio/" + audioFile + ".ogg"
        cmd = Sound(path)
        cmd.play()
    except Exception as e:
        logger.LogError("computerspeech.py: playAudio(): Unable to play:".format(e))
