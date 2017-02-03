#1/16/2017
#Chris Burns @Forecast_Cloudy

#Vision class will take pictures/video
import pygame
import pygame.camera
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
import Log

"""def get_client(endpoint):
    key_id = environ.get('AWS_ACCESS_KEY_ID')
    secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
    token = environ.get('AWS_SESSION_TOKEN')
    if not key_id or not secret_key or not token:
            raise Exception('Missing AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, or AWS_SESSION_TOKEN')
    client = boto3.client('rekognition', region_name='us-east-1',endpoint_url=endpoint,
                          verify=False,
                          aws_access_key_id=key_id,
                          aws_secret_access_key=secret_key,
                          aws_session_token=token)
    return client

def get_args():
    parser = ArgumentParser(description='Call index faces')
    parser.add_argument('-e', '--endpoint')
    parser.add_argument('-i', '--image')
    parser.add_argument('-c', '--collection')
    return parser.parse_args()"""
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
                response = rekognition.detect_labels(Image={'Bytes': imagefile.read()}, MaxLabels=10)

            quote = "I am "

            for label in response["Labels"]:
                c = round(label["Confidence"], 2)
                quote += str(c)
                quote += str(" percent confident I see a")
                quote += str(label["Name"])
                quote += str(" , ")

        except Exception as e:
            logger.LogError("computerVision.py: callRekognition(): Unable to take picture! : {} ".format(e))

        return quote



    @staticmethod
    def takeSinglePicture(detect_labels=False):
        try:
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





