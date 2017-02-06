# 1/30/17
# Chris Burns @Forecast_Cloudy
# Class to asbtract logging details
import logging
import datetime
import time
LOGFILE='RePL.log'



class rLog(object):

    def __init__(self, init):
        if init: #create a new log file
            logging.getLogger("RePLLog")
            logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)
            logging.info("")
            logging.info("*******************New RePL instance booting!***********************************")
            logging.info("********************************************************************************")
            logging.info("")
        else:   #write to an existing log file
            logging.getLogger("RePLLog")
            logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)

    def LogThis(self, message):
        ts = time.time()
        logging.info(str(ts) + ":: " + message)
        print(message)

    def LogDebug(self, message):
        ts = time.time()
        logging.debug(str(ts) + ":: " + message)
        print("DEBUG: {}".format(message))

    def LogWarning(self, message):
        ts = time.time()
        logging.warning(str(ts) + ":: " + message)
        print("WARNING: {}".format(message))

    def LogError(self, message):
        ts = time.time()
        logging.error(str(ts) + ":: " + message)
        print("ERROR: {}".format(message))

    def LogCritical(self, message):
        ts = time.time()
        logging.critical(str(ts) + ":: " + message)
        print("CRITICAL: {}".format(message))
