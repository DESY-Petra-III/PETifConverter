import os
import numpy as np
from app.config.keys import *

# storage for internal variables
CONFIG_STORAGE = {
    # folder related
    FOLDER_STARTUP: None,
    FOLDER_LOG: None,

    # process related
    PROC_MAX_NUM : 5,                       # maximum number of processes
    PROC_SLEEP_DELAY: 1.,                   # delay to sleep between process tact
    PROC_FILE_TEST_MOD_TIME: 3.,            # test - file is considered to be existing if its modified flag is older than 3s
    PROC_FILE_TEST_SIZE: 16777000,          # test - file is considerd to be existing if its size is greater than ..
    PROC_FILE_TIMEOUT: 15.,                 # timeout after which we consider the file as non existing
    PROC_FILE_ROTATE: 90.,                  # angle of image rotation - should be multiple of 90, otherwise, won't be used
    PROC_FILE_FLIP: 1,                      # axis direction of numpy.ndarray.flip - None - no operation, flip is applied after the rotation
    PROC_FILE_CONVERSION_TYPE: np.int32,    # conversion type  - numpy format
    PROC_PATH_REPLACE: ("raw", "processed"),                  # path replacement info, do not overwrite files - create new (needle, replacement)


    # logging
    LOGGING_MAIN_FILE: "main_log",
    LOGGING_MAIN_FORMAT: '%(asctime)s %(levelname)-8s %(process)-8d %(thread)-10d %(threadName)-16s %(name)-12s: %(message)s',
    LOGGING_MAIN_DATE: '%m-%d %H:%M',

    LOGGING_FILE_FORMAT: '%(asctime)s %(levelname)-8s %(process)-8d %(thread)-10d %(threadName)-16s %(name)-12s: %(message)s',
    LOGGING_FILE_DATE: '%Y-%m-%d %H:%M:%S',
}

CONFIG_INSTANCE = None

class Config(object):
    """
    Simple wrapper for configuration providing meaningful names and access process (func vs dict)
    """
    def __init__(self):
        global CONFIG_INSTANCE

        if CONFIG_INSTANCE is None:
            CONFIG_INSTANCE = self

    def setConfiguration(self, key, value):
        global CONFIG_STORAGE

        # print("Setting configuration value ({}:{})".format(key, value))
        CONFIG_STORAGE[key] = value

    def getConfiguration(self, key):
        global CONFIG_STORAGE

        # print("Retrieving configuration value ({}:{})".format(key, CONFIG_STORAGE[key]))
        return CONFIG_STORAGE[key]

    def setFolderStartup(self, v):
        self.setConfiguration(FOLDER_STARTUP, v)

    def setFolderLog(self, v):
        self.setConfiguration(FOLDER_LOG, v)

    def setProcMaxNum(self, v):
        self.setConfiguration(PROC_MAX_NUM, v)
        
    def checkBasicPaths(self):
        global CONFIG_STORAGE

        l = (
                FOLDER_STARTUP,
                FOLDER_LOG
                )

        self.printHeaderMsg("Testing configuration directories:")
        for (i, key) in enumerate(l):
            d = CONFIG_STORAGE[key]
            if os.path.exists(d) and os.path.isdir(d):
                self.printBulletMsg01("Directory ({} : {}) exists".format(key, d))
                pass
            if not os.path.exists(d):
                self.printBulletMsg02("Trying to create directory ({} : {})".format(key, d))
                os.mkdir(d)
                pass

    def getMainLogFile(self):
        return self.getConfiguration(LOGGING_MAIN_FILE)

    def getFolderLog(self):
        return self.getConfiguration(FOLDER_LOG)

    def getLoggingMainFormat(self):
        return self.getConfiguration(LOGGING_MAIN_FORMAT)

    def getLoggingMainDate(self):
        return self.getConfiguration(LOGGING_MAIN_DATE)

    def getLoggingFileFormat(self):
        return self.getConfiguration(LOGGING_FILE_FORMAT)

    def getLoggingFileDate(self):
        return self.getConfiguration(LOGGING_FILE_DATE)

    def getProcMaxNumber(self):
        return self.getConfiguration(PROC_MAX_NUM)

    def getProcSleepDelay(self):
        return self.getConfiguration(PROC_SLEEP_DELAY)

    def getProcFileTimeout(self):
        return self.getConfiguration(PROC_FILE_TIMEOUT)

    def getProcFileRotation(self):
        return self.getConfiguration(PROC_FILE_ROTATE)

    def getProcFileFlip(self):
        return self.getConfiguration(PROC_FILE_FLIP)

    def getProcFileConvType(self):
        return self.getConfiguration(PROC_FILE_CONVERSION_TYPE)

    def getProcFileTestSize(self):
        return self.getConfiguration(PROC_FILE_TEST_SIZE)

    def getProcFileTestModTime(self):
        return self.getConfiguration(PROC_FILE_TEST_MOD_TIME)

    def getProcPathReplacement(self):
        return self.getConfiguration(PROC_PATH_REPLACE)

    def printHeaderMsg(self, msg):
        """
        Prints message aas a header
        :param msg:
        :return:
        """
        print("\n### {}".format(msg))

    def printBulletMsg01(self, msg):
        """
        Prints message aas a header
        :param msg:
        :return:
        """
        print(" - {}".format(msg))

    def printBulletMsg02(self, msg):
        """
        Prints message aas a header
        :param msg:
        :return:
        """
        print("   {}".format(msg))

def get_instance():
    global CONFIG_INSTANCE

    if CONFIG_INSTANCE is None:
        Config()

    return CONFIG_INSTANCE