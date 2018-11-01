__author__ = 'Konstantin Glazyrin'

import os
import time
import glob
import logging

import app.config.main_config as config

# DEBUG_LEVEL = logging.INFO

# Logger class
class Logger(object):
    DEFAULTLEVEL = logging.DEBUG

    DEFAULTFILE = "{}{}".format(config.get_instance().getMainLogFile(), ".log")

    DEBUG_LEVELS = "INFO: {}; WARNING: {}; DEBUG: {}".format(logging.INFO, logging.WARNING, logging.DEBUG)

    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    CRITICAL = logging.CRITICAL

    def __init__(self, def_file=None, debug_level=None, log_folder=None):
        # local configuration
        c = config.get_instance()

        self.debug_level = None
        self.local_log_folder = log_folder

        if debug_level is not None:
            self.debug_level = debug_level
        else:
            self.debug_level = self.DEFAULTLEVEL

        logging.basicConfig(level=self.DEFAULTLEVEL,
                            format=c.getLoggingMainFormat(),
                            datefmt=c.getLoggingMainDate(),
                            filemode='a')

        if def_file is None:
            self._logger = logging.getLogger("{}".format(self.__class__.__name__))
        else:
            self._logger = logging.getLogger("{}/{}".format(os.path.basename(def_file), self.__class__.__name__))

        self._fh = None

        self.setDebugLevel(self.debug_level)

        try:
            if def_file is not None:
                self.DEFAULTFILE = "{}.log".format(def_file)

            if self.DEFAULTFILE is not None and len(self.DEFAULTFILE) > 0:

                # creating a log file
                temp = [self.DEFAULTFILE]

                local_log_folder = None
                if self.local_log_folder is None:
                    self.local_log_folder = c.getFolderLog()
                self.debug("Setting default file name with logFolder ({})".format(self.local_log_folder))
                self.DEFAULTFILE = os.path.join(self.local_log_folder, *temp)

                self.DEFAULTFILE = self.DEFAULTFILE.replace(".pyc", "")
                self.DEFAULTFILE = self.DEFAULTFILE.replace(".py", "")

                # check that we can use file
                if os.path.exists(self.DEFAULTFILE) and not os.path.isfile(self.DEFAULTFILE):
                    self.error("Cannot create a log file ({})".format(self.DEFAULTFILE))
                    raise AttributeError
                else:
                    self.addFileHandler(self.DEFAULTFILE)
        except (AttributeError):
            pass

        # check the global settings
        self.prepare_dl()

    def test(self, value=None, type=None):
        """
        Main function testing values
        :param value:
        :param type:
        :return:
        """
        res = False

        if value is not None:
            if type is not None and isinstance(value, type):
                res = True
            elif type is None:
                res = True

        return res

    @property
    def logger(self):
        return self._logger

    def prepare_dl(self):
        try:
            global DEBUG_LEVEL
            DEBUG_LEVEL
            if self.test(DEBUG_LEVEL):
                self.setDebugLevel(DEBUG_LEVEL)
        except NameError:
            self.debug("global DEBUG_LEVEL is not defined")
        finally:
            self.debug("Using the DEBUG_LEVEL ({})".format(self.debug_level))

    def setDebugLevel(self, level):
        self.logger.setLevel(level)

        for h in self.logger.handlers:
            h.setLevel(level)

    def info(self, msg):
        msg = self._check_msg(msg)
        self._logger.info(msg)

    def debug(self, msg):
        msg = self._check_msg(msg)
        self._logger.debug(msg)

    def error(self, msg):
        msg = self._check_msg(msg)
        self._logger.error(msg)

    def warning(self, msg):
        msg = self._check_msg(msg)
        self._logger.error(msg)

    def _check_msg(self, msg):
        if msg is not None:
            if isinstance(msg, str):
                pass
            else:
                msg = str(msg)
        else:
            msg = str(msg)
        return msg

    def confError(self, key, def_value, e=None):
        self.error("Configuration key {0} does not exist, using default value {1}".format(key, def_value))
        if e is not None:
            self.error("Error message as follows:\n{0}".format(e))

    def confIndexError(self, index, def_value):
        self.error("Configuration index {0} does not exist, reporting default value".format(index, def_value))

    def defFailedError(self, device_path, e=None):
        self.error("Device {0} reports DevFailed error".format(device_path))
        if e is not None:
            self.error("Error message as follows:\n{0}".format(e))

    def addFileHandler(self, filename):

        c = config.get_instance()

        self.debug("Using default filename for logging ({})".format(filename))

        fh = logging.FileHandler(filename, "w+")
        fh.setLevel(self.debug_level)

        # add formatter
        fmtr = logging.Formatter(c.getLoggingFileFormat(),
                                 c.getLoggingFileDate())
        fh.setFormatter(fmtr)

        self.logger.addHandler(fh)

    def __del__(self):
        self.debug("Removing handlers")
        handlers = self._logger.handlers[:]
        for handler in handlers:
            handler.close()
            self._logger.removeHandler(handler)


# Wrapper to test specific value types
class Tester(Logger):
    def __init__(self, def_file=None, debug_level=None, log_folder=None):
        Logger.__init__(self, def_file=def_file, debug_level=debug_level, log_folder=log_folder)

        self.debug("Class initialization ({}).".format(self.__class__.__name__))

    def testString(self, value):
        """
        Tests value for being a string
        :param value:
        :return:
        """
        res = False
        if self.test(value, str):
            res = True
        return res

    def testFloat(self, value):
        """
        Tests value for being a float
        :param value:
        :return:
        """
        return self.test(value, float)

    def testInt(self, value):
        """
        Tests value for being an integer
        :param value:
        :return:
        """
        return self.test(value, int)

