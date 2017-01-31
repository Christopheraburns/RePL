#1/16/2017
#Chris Burns @Forecast_Cloudy

#Vision class will take pictures/video
import pygame
import pygame.camera

class Vision(object):


    @staticmethod
    def takeSinglePicture():
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
            print ("Unable to take picture! : {} ", e)
