from app.common.imports import *
import app.config.main_config as config
from app.worker import *

class StarterException(Exception):
    pass

class Starter(Tester):
    # number of child processes
    NUM_PROC = None

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

        # value of total conversion time (s)
        self.value_time = Value(ctypes.c_double, 0.0)
        # value of total conversion files
        self.value_frames = Value(ctypes.c_uint32, 0)

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

    def startTiffApplication(self):
        """
        Initialization of the program - starts new processes
        :return:
        """
        c = config.get_instance()

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

        c = config.get_instance()

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
        c = config.get_instance()
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
                self.qquit.put("Stop")

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
            for iproc in range(self.NUM_PROC):
                self.qquit.put("Stop")

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
