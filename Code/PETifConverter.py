from app.common.imports import *
from app.starter import *
from app.tango_server import *

class PETifConverter(TangoServer):

    # Vars
    STARTER = None
    CONFIG = None

    # Attributes

    NumProcessed = attribute(label="Number of input files", dtype=int, fget="getNumProcessed", description="Number of processes doing file conversion")
    NumWorkers = attribute(label="Number of workers", dtype=int, fget="getConfNWorkers", description="Number of workers set by properties (higher priority) or configuration (lower priority)")

        # configuration related
    ConfRotation = attribute(label="Rotation of the image", dtype=int, fget="getConfRotation", description="Desired rotation of the frame (config file, mult. of 90 Degrees)")
    ConfFlip = attribute(label="Flip of the image axis", dtype=str, fget="getConfFlip", description="Flip configuration (config file, numpy.ndarray.flip type)")
    ConfType = attribute(label="Pixel type of the conversion", dtype=str, fget="getConfNType", description="Numeric type of the pixel in terms of numpy (config file)")

        # statistic related
    StatisticsTotalFrames = attribute(label="Total frames", dtype=int, fget="getStatTotalConverted", description="Total frames converted")
    StatisticsTotalTime = attribute(label="Total time (s)", dtype=float, fget="getStatTotalTime", description="Total time of conversion (s)")
    StatisticsAverageTime = attribute(label="Average time (s)", dtype=float, fget="getStatAverageTime", description="Average time of conversion (s)")

    # device property - number of workers
    numworkers = device_property(dtype=int, default_value=3, update_db=True)

    @property
    def t(self):
        return self.s

    @property
    def s(self):
        return self.STARTER

    @s.setter
    def s(self, v):
        self.STARTER = v

    def __init__(self, *args, **kwargs):
        TangoServer.__init__(self, *args, **kwargs)
        self.num_processed = 0

    def init_device(self):
        """
        Initialization
        :return:
        """
        # initialize properties
        self.get_device_properties()

        # start process device
        self.debug("Checking starter instance ({})".format(self.s))
        if self.s is None:
            self.s = Starter(sys.argv)

            self.debug("The number of workers provided by property is ({})".format(self.numworkers))
            self.s.getConfigInstance().setProcMaxNum(self.numworkers)

            # starts external processes - multiprocessing
            self.s.startTiffApplication()

        self.debug("Checking starter instance ({})".format(self.s))

        # sets the initial device state
        self._stateON()
        self.append_status("Device has started successfully")

    def getNumProcessed(self):
        return self.num_processed

    def getConfNWorkers(self):
        return self.numworkers

    def getConfRotation(self):
        return self.s.getConfigInstance().getProcFileRotation()

    def getConfFlip(self):
        return str(self.s.getConfigInstance().getProcFileFlip())

    def getConfNType(self):
        return str(self.s.getConfigInstance().getProcFileConvType())

    def getStatTotalConverted(self):
        v = self.s.value_frames.value
        return v

    def getStatTotalTime(self):
        v = self.s.value_time.value
        return v

    def getStatAverageTime(self):
        res = 0
        t = self.s.value_time.value
        v = float(self.s.value_frames.value)
        if v != 0:
            res = t/v
        return res

    def delete_device(self):
        """
        Cleanup function
        :return:
        """
        # cleaning up the starter object
        if self.s is not None:
            self.s.quit()

    ##
    # Commands
    ##

    @command(dtype_out=int)
    def zQuitSoftly(self):
        """
        Gently stops the tango server
        :return:
        """
        self.info("Cleaning the starter object")
        self.delete_device()
        return 0

    @command(dtype_in=[str])
    def AddFiles(self, files):
        """
        Adds new files for processing
        :return:
        """
        self.debug("Adding ({}) files for processing".format(files))

        if self.s is not None:
            self.s.addFilenames(files)
            self.num_processed += len(files)


    @command(dtype_in=str, dtype_out=int)
    def AddFolder(self, folder):
        """
        Adds new files for processing
        :return:
        """
        res = 0
        self.debug("Adding ({}) a folder for processing".format(folder))

        if not os.path.exists(folder) or not os.path.isdir(folder):
            self.error("Folder ({}) does not exist or it is not a dir")
            res = -1
        else:
            files = glob.glob(os.path.join(folder, "*.tif"))
            self.debug("Found ({}) files in the folder ({})".format(len(files), folder))

            if len(files) > 0:
                self.s.addFilenames(files)
                self.num_processed += len(files)

        return res

    @command()
    def ResetStats(self):
        """
        Adds new files for processing
        :return:
        """
        self.debug("Trying to reset statistics values")
        self.s.resetStats()

if __name__ == "__main__":
    PETifConverter.run_server()