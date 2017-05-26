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
        lex = ["aihacklex"]

        logger.LogThis("__main__.py: Contacting polly to convert command to voice")
        response = polly.synthesize_speech(Text=value, TextType="ssml", OutputFormat="mp3", VoiceId="Emma", LexiconNames=lex)
        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                output = os.path.join("speech.mp3")
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
            pygame.mixer.music.load('speech.mp3')
            pygame.mixer.music.play()
            time.sleep(10)
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



#text = '<speak>Hello everyone! Someone, who shall remain nameless <break time="100ms"/> '\
#       '<amazon:effect name="whispered">but is bald and wears glasses</amazon:effect> <break time="100ms"/> '\
#        'wanted me to say, <prosody volume="x-loud"><prosody rate="slow">May the 4th be with you!</prosody></prosody></speak>'

text = '<speak>I can use a lexicon to change the characters <break time="100ms"/><say-as interpret-as="character">W Y S I W Y G</say-as> into the phrase WYSIWYG</speak>'


pollySays(text)



