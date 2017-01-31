# 1/30/17
# Chris Burns @Forecast_Cloudy
# Class to asbtract logging details
import logging
import datetime
import time
LOGFILE='RePL.log'



class rLog(object):

    def __init__(self, init):
        if init:
            logging.getLogger("RePLLog")
            logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)
            logging.info("*******************New RePL instance booting!***********************************")
            logging.info("********************************************************************************")
            logging.info("")
        else:
            logging.getLogger("RePLLog")
            logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)

    def LogThis(self, message):
        ts = time.time()
        logging.info(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ":: " + message)
        print(message)

    def LogDebug(self, message):
        ts = time.time()
        logging.debug(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ":: " + message)
        print("DEBUG: {}".format(message))

    def LogWarning(self, message):
        ts = time.time()
        logging.warning(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ":: " + message)
        print("WARNING: {}".format(message))

    def LogError(self, message):
        ts = time.time()
        logging.error(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ":: " + message)
        print("ERROR: {}".format(message))

    def LogCritical(self, message):
        ts = time.time()
        logging.critical(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ":: " + message)
        print("CRITICAL: {}".format(message))
