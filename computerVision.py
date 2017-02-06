#1/16/2017
#Chris Burns @Forecast_Cloudy

#Vision class will take pictures/video and send to AWS Rekognition for processing
import pygame
import pygame.camera
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
import Log
import os
#Create a logger object
logger = Log.rLog(False)

#Create an AWS Client obj
session = Session(profile_name="default")
rekognition = session.client("rekognition")


class Vision(object):

    @staticmethod
    def callRekognition():
        try:
            # send iamge to rekognition for labels
            with open("capture.png", "rb")as imagefile:
                response = rekognition.detect_labels(Image={'Bytes': imagefile.read()}, MaxLabels=6)

            quote = "I am "

            for label in response["Labels"]:
                if label["Confidence"] > 75.00:
                    c = round(label["Confidence"], 1)
                    quote += str(c)
                    quote += str(" percent confident I see a")
                    quote += str(label["Name"])
                    quote += str(" , ")

        except(BotoCoreError, ClientError) as e:
            logger.LogError("computerVision.py: callRekognition(): Error: {}".format(e))
        except Exception as e:
            logger.LogError("computerVision.py: callRekognition(): Unable to take picture! : {} ".format(e))

        return quote


    @staticmethod
    def takeSinglePicture(detect_labels=False):
        try:
            #delete capture.png if it exists
            #TODO - create a subfloder and logic to more, rename and store all images
            pygame.camera.init()
            cameras = pygame.camera.list_cameras()
            for camera in cameras:
                if camera:
                    cam = pygame.camera.Camera(camera,(640,480),"RGB")
                    cam.start()
                    img = cam.get_image()
                    pygame.image.save(img,"capture.png")
                    cam.stop()
                break
        except Exception as e:
            logger.LogError("computerVision.py: takeSinglePicture(): Unable to take picture! : {} ".format(e))





