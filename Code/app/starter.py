from app.common.imports import *
import app.config.main_config as config
from app.worker import *

class StarterException(Exception):
    pass

class Starter(Tester):
    # number of child processes
    NUM_PROC = None
    STOP_SIGNAL = "Stop"

    def __init__(self, argv):
        # preparation
        argv = self.prepare_additional_arguments(argv)
        self.prepare_paths(argv)

        # cleaning logs
        self.cleanLogs()

        # class relies on logs
        Tester.__init__(self, def_file="{}".format(self.__class__.__name__.lower()))

        # vars
        self.procs = []

        # quite queue
        self.qquit = Queue()
        self.qfiles = Queue()
        self.qunsorted = Queue()

        # value of total conversion time (s)
        self.value_time = Value(ctypes.c_double, 0.0)
        # value of total conversion files
        self.value_frames = Value(ctypes.c_uint32, 0)

        # sorting thread - gets its own queue with strings,
        # sorts out files, directories
        # starts processing accordingly
        self.thsort = threading.Thread(target=self.sortFilesDirs, args=[self.qunsorted, self.qfiles, self.qquit])


    def _process_element(self, el):
        """
        Internal function preparing and testing the files
        Directory gets the file system elements parsed for .tif
        Files also pass through a temporary analysis - darks are ignored
        :param el:
        :return:
        """
        tfiles = None

        rpatt = re.compile(".*(\.tif|\.tiff)$", re.IGNORECASE)

        if os.path.isdir(el):
            # check that the element is a directory, find all tif files, check that they are files
            self.debug("New element is a directory ({})".format(el))

            telements = glob.glob(os.path.join(el, "*.tif"))
            tfiles = list(filter(lambda tel: os.path.isfile(tel) and not "dark" in tel.lower(), telements))

        elif os.path.isfile(el) and not "dark" in el.lower():
            self.debug("New element is a file ({})".format(el))
            rpatt = re.compile(".*(\.tif|\.tiff)$", re.IGNORECASE)

            if rpatt.match(el):
                tfiles = [el]
        elif not "dark" in el.lower() and rpatt.match(el):
            # lets check if the f
            self.debug("New element does not exist, but it could be saved soon ({})".format(el))
            tfiles = [el]

        # process files if needed
        if tfiles is not None:
            self.debug("Adding new elements for processing ({})".format(tfiles))
            self.addFilenames(tfiles)

    def sortFilesDirs(self, qunsorted, qfiles, qquit):
        """
        Obtains a queue of elements, sorts out files and directories, adds them to the processing
        :return:
        """
        c = self.getConfigInstance()
        while True:
            try:

                paths = qunsorted.get(False)
                self.debug("Got an element to sort ({})".format(paths))
                if isinstance(paths, list) or isinstance(paths, tuple):
                    self.debug("Sotring a list")
                    for el in paths:
                        self._process_element(el)
                else:
                    self.debug("Sorting a single entry")
                    self._process_element(paths)
            except Empty:
                pass

            # test for the quit signal + sleep
            try:
                tquit = qquit.get(False)
                if tquit == self.STOP_SIGNAL:
                    break
            except Empty:
                pass

            time.sleep(min(c.getProcThreadSleepDelay(), 1))

            try:
                tquit = qquit.get(False)
                if tquit == self.STOP_SIGNAL:
                    break
            except Empty:
                pass

    def addFilenames(self, *argv):
        """
        Fill the queue with the filenames
        :return:
        """
        self.debug("Adding files for processing")
        try:
            flist = argv[0]

            if len(flist) > 0:
                for fn in argv[0]:
                    self.debug("Adding file ({}) to the queue".format(fn))
                    self.qfiles.put(fn)
        except IndexError:
            self.error("File list is empty")

    def getPreprocessQueue(self):
        """
        Returns the queue used for working with the files
        :return:
        """
        return self.qunsorted

    def startTiffApplication(self):
        """
        Initialization of the program - starts new processes
        :return:
        """
        # start the thread responsible for file and directories analysis
        self.thsort.start()

        c = self.getConfigInstance()

        self.NUM_PROC = c.getProcMaxNumber()

        try:
            self.debug("Starting ({}) worker processes".format(self.NUM_PROC))

            for iproc in range(int(self.NUM_PROC)):
                proc = Process(target=worker, args=(self.qfiles, self.qquit, c.getFolderLog(), self.value_time, self.value_frames))
                self.procs.append(proc)
                proc.start()

        except StarterException:
            self.debug("Exit on {}".format(StarterException.__class__.__name__))
            # sys.exit(-1)

    def prepare_additional_arguments(self, argv):
        """
        Prepares additional arguments
        :return:
        """
        return argv

    def prepare_paths(self, argv):
        """
        Prepares the most important paths
        :return:
        """
        basepath = os.path.dirname(os.path.realpath(argv[0]))
        os.chdir(basepath)

        c = self.getConfigInstance()

        if isinstance(c, config.Config):
            c.printHeaderMsg("Preparing configuration paths")
            path = basepath
            c.printBulletMsg01("Startup path ({})".format(path))
            c.setFolderStartup(path)

            path = os.path.join(basepath, "log")
            c.printBulletMsg01("Log path ({})".format(path))
            c.setFolderLog(path)

            c.checkBasicPaths()

    def performTests(self):
        """
        Tests necessary for the startup
        :return:
        """
        self.debug("Performing startup tests")
        res = True

        return res

    def cleanLogs(self):
        """
        Cleans up the logs
        :return:
        """
        c = self.getConfigInstance()
        c.printHeaderMsg("Cleaning log files")
        c.printBulletMsg01("Log directory is ({})".format(c.getFolderLog()))
        log_folder = c.getFolderLog()

        if log_folder is not None:
            for fn in os.listdir(c.getFolderLog()):
                fn = os.path.join(log_folder, fn)
                if os.path.isfile(fn):
                    print(" - Deleting old log file ({})".format(fn))
                    os.unlink(fn)
        # TODO - keep previous log
        pass

    def quit_debug(self):
        """
        Exit function
        :return:
        """
        self.info("Quitting the application with a delay of 10s")
        time.sleep(10)
        self.info("Quitting the application now")

        if self.NUM_PROC is not None:
            for iproc in range(self.NUM_PROC):
                self.qquit.put(self.STOP_SIGNAL)

            self.info("Quitting the application now")

            # wating for the processes to stop

            while True:
                time.sleep(1)

                cnt = 0

                for proc in self.procs:
                    if proc.exitcode is None:
                        proc.join()
                    else:
                        cnt = cnt + 1

                self.debug("Quit counter value is ({})".format(cnt))
                if cnt >= len(self.procs):
                    break

        self.debug("Cleaning process is finished")
        del self.procs[:]

    def quit(self):
        """
        Exit function
        :return:
        """
        self.info("Quitting the application now")

        if self.NUM_PROC is not None:
            for iproc in range(self.NUM_PROC+1):
                self.qquit.put(self.STOP_SIGNAL)

            self.info("Quitting the application now")

            # wating for the processes to stop
            if len(self.procs) > 0:
                while True:
                    time.sleep(1)

                    cnt = 0

                    for proc in self.procs:
                        if proc.exitcode is None:
                            proc.join()
                        else:
                            cnt = cnt + 1

                    self.debug("Quiting.. Counter value is ({})".format(cnt))
                    if cnt >= len(self.procs):
                        break
            del self.procs[:]

        # close the thread
        if self.thsort.isAlive():
            self.info("Stopping the sorting thread")
            self.qquit.put(self.STOP_SIGNAL)
            self.thsort.join()

        self.info("Cleaning process is finished")

    def getConfigInstance(self):
        """
        Returns the config instance
        :return:
        """
        res = None
        c = config.get_instance()
        if isinstance(c, config.Config):
            res = c
        return res

    def resetStats(self):
        """
        Resets the statistics
        :return:
        """
        self.debug("Resetting the stat. multiprocessing.Values")
        if self.value_time is not None:
            with self.value_time.get_lock():
                self.value_time.value = 0.

        if self.value_frames is not None:
            with self.value_frames.get_lock():
                self.value_frames.value = 0
