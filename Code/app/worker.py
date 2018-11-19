import fabio
from app.common.imports import *
import app.config.main_config as config

class WorkerFileException(Exception):
    """
    Dummy class for the conversion process related exception
    """
    pass

def convert_file(fn, fh, value_time, value_frames, logger=None, conf=None):
    """
    Open file, report the pixel type, convert file and rotate if needed
    :param fn: filename
    :param fh: fabio handle
    :param logger:
    :param c: config object
    :return:
    """
    # timestamp
    tstart, tstop = time.time(), 0

    # save the file
    t = logger
    if t is not None:
        t.debug("Starting file conversion ({})".format(fn))

    c = None
    if conf is None:
        c = config.get_instance()
    else:
        c = conf

    # get configuration parameters
    rot = c.getProcFileRotation()
    flip = c.getProcFileFlip()
    conv_type = c.getProcFileConvType()
    path_replace = c.getProcPathReplacement()
    '''t.debug("\nReplacement configuration:\n"
            "\t - Rotation ({})\n"
            "\t - Flip axis ({})\n"
            "\t - Conversion type ({})\n"
            "\t - Path replacement ({})\n".format(rot, flip, conv_type, path_replace))'''

    # initial parameters
    fn_origin, fn_new = fn, fn.replace(path_replace[0], path_replace[1])
    dir_new = os.path.dirname(fn_new)

    if t is not None:
        t.debug("The old ({}) and the new ({}) paths".format(fn_origin, fn_new))

    try:
        # creating the tree of the new directory
        os.makedirs(dir_new, exist_ok=True)
    except OSError as e:
        if t is not None:
            t.error("Error while creating a new directory ({}:{})".format(dir_new, e))

    # we consider the file to be opened
    dtype = None
    if t is not None:
        t.debug("Dimensions ({}:{})".format(fh.dim1, fh.dim2))
        if fh.dim1 > 0 and fh.dim2 > 0:
            dtype = type(fh.data[0, 0])
            t.debug("Inner file format ({}:{})".format(type(dtype), fh.nbits))

    # remove the negative values before the transformation into uints
    if fh.dim1 > 0 and fh.dim2 > 0 and dtype is not None:
        if conv_type in (np.uint, np.uint0, np.uint8, np.uint16, np.uint32, np.uint64) and dtype in (np.float, np.float16, np.float32, np.int, np.int8, np.int16, np.int32, np.long):
            fh.data[fh.data < 0] = 0

    # apply the transformation
    tdata = deepcopy(fh.data.astype(conv_type))

    if fh.dim1 > 0 and fh.dim2 > 0:

        # if rotation angle is a multiple of 90 - do rotation
        if rot % 90. == 0 and rot != 0:
            if t is not None:
                t.debug("Rotating the image by ({}) degrees".format(rot))
            tdata = np.rot90(tdata, int(rot/90.))

        # perform flipping
        if flip is not None:
            if t is not None:
                t.debug("Flipping the image by axis/axes ({})".format(flip))
            tdata = np.flip(tdata, axis=flip)

    # create new file - saving transformed data
    if t is not None:
        t.debug("Writing the new file ({})".format(fn_new))

    try:
        tfh = fabio.tifimage.TifImage(tdata)
        tfh.write(fn_new)
        tfh.close()
    except (OSError, IOError) as e:
        if t is not None:
            t.error("Error while writing new data ({})".format(fn_new, e))

    # time of conversion
    tstop = time.time()
    tconversion = tstop-tstart
    if t is not None:
        t.debug("Time of conversion ({}s)".format(tconversion))

    # report the values via multiprocessing.Value
    if value_time is not None:
        with value_time.get_lock():
            value_time.value += tconversion
            t.debug("Total conversion time ({})".format(value_time.value))

    # report the number of frames collected via multiprocessing.Value
    if value_frames is not None:
        with value_frames.get_lock():
            value_frames.value += 1
            t.debug("Total conversion frames ({})".format(value_frames.value))

def create_skip(fn, logger=None, conf=None, shapex=2048, shapey=2048):
    """
    If the file is not existing - create its substitution as empty file
    :return:
    """
    t = logger
    if t is not None:
        t.debug("Starting skip file process ({})".format(fn))

    c = None
    if conf is None:
        c = config.get_instance()
    else:
        c = conf

    conv_type = c.getProcFileConvType()
    path_replace = c.getProcPathReplacement()

    # initial parameters
    fn_origin, fn_new = fn, fn.replace(path_replace[0], path_replace[1])
    dir_new = os.path.dirname(fn_new)

    if t is not None:
        t.debug("The old ({}) and the new skip dummy ({}) paths".format(fn_origin, fn_new))

    try:
        # creating the tree of the new directory
        os.makedirs(dir_new, exist_ok=True)
    except OSError as e:
        if t is not None:
            t.error("Error while creating a new directory ({}:{})".format(dir_new, e))

    tdata = np.zeros([shapex, shapey], dtype=conv_type)

    # saves the empty TIF file
    try:
        tfh = fabio.tifimage.TifImage(tdata)
        tfh.write(fn_new)
        tfh.close()
    except (OSError, IOError) as e:
        if t is not None:
            t.error("Error while writing new data ({})".format(fn_new, e))

def worker(file_queue, stop_queue, log_folder, value_time, value_frames, debug=None):
    """
    Function serving as a process
    :param file_queue:
    :param stop_queue:
    :return:
    """
    local_name = current_process().name

    # get static information from config file - remain unmodified through the program operation
    c = config.get_instance()
    delay = c.getProcSleepDelay()
    ftimeout = c.getProcFileTimeout()
    ftestsize = c.getProcFileTestSize()
    ftestmod = c.getProcFileTestModTime()
    rot = c.getProcFileRotation()
    flip = c.getProcFileFlip()
    conv_type = c.getProcFileConvType()
    path_replace = c.getProcPathReplacement()

    t = Tester(def_file=local_name, log_folder=log_folder)

    t.info("\nReplacement configuration:\n"
           "\t - Process sleep delay ({})\n"
           "\t - Process file timeout ({})\n"
           "\t - Process file size test ({})\n"
           "\t - Process file test modification time ({}s)\n"
            "\t - Rotation ({})\n"
            "\t - Flip axis ({})\n"
            "\t - Conversion type ({})\n"
            "\t - Path replacement ({})\n".format(delay, ftimeout, ftestsize, ftestmod, rot, flip, conv_type, path_replace))

    t.debug("Worker {} has started, setting the delay to ({})".format(local_name, delay))

    bstop = False
    debug_cnt = 0

    fn = None

    # timestamp for file to be converted - if the file is not existing within
    # 10s - consider it as missing
    fnts_start = None

    while True:

        # obtaining the filename
        if fn is None:
            try:
                fn = file_queue.get(False)
                t.debug("Got filename ({})".format(fn))
                fnts_start = time.time()
            except Empty:
                # t.debug("Empty on filename")
                pass

        # process if we have some input
        try:
            if fn is not None:
                # after certain timeout - consider the file to be non existing
                ftstamp = time.time()

                if ftstamp - fnts_start > ftimeout:
                    t.error("Timeout ({}), considering the file ({}) as non existing. Skipping..".format(ftimeout, fn))
                    # creating an empty file - skip file
                    create_skip(fn, logger=t, conf=c)
                    fn, fnts_start = None, None
                    raise WorkerFileException

                # convert the file if the file exist
                bexist = False
                if os.path.exists(fn):
                    # make a test - size, modification time
                    try:
                        # file size test - passed or Exception
                        fsize = os.path.getsize(fn)
                        t.debug("Size of the file ({}) vs test size ({}). Test ({})".format(fsize, ftestsize, fsize > ftestsize))
                        if fsize < ftestsize:
                            raise WorkerFileException

                        # file modification time test
                        fmodtime = os.path.getmtime(fn)
                        t.debug("Modification time of the file ({}) vs timestamp ({}). Delay: ({}). Test({})".format(fmodtime, ftstamp, ftestmod, ftstamp - fmodtime>ftestmod))
                        if ftstamp - fmodtime < ftestmod:
                            raise WorkerFileException

                    except OSError: # raised based on the file access status
                        t.error("OSError exception ({})".format(fn))
                        raise WorkerFileException

                    # final test - we can open the file by fabio and convert itx
                    fh = None
                    try:
                        fh = fabio.openimage.openimage(fn)

                        # if all the tests passed - convert
                        convert_file(fn, fh, value_time, value_frames, logger=t, conf=c)

                        fh.close()
                    except IOError:
                        t.error("File ({}) was not recognized by fabio. Skipping..".format(fn))

                        # redundant cleanup
                        if fh is not None:
                            fh.close()
                    # cleanup the information, wait for the next file
                    fn, fnts_start = None, None
                else:
                    t.error("File ({}) does not exist".format(fn))
                    raise WorkerFileException
        except WorkerFileException:
            # - file does not satisfy some criterion - size of modification time
            t.debug("Got the WorkerFileException")
            pass

        # get stop queue
        try:
            stop_queue.get(False)
            bstop = True
        except Empty:
            # t.debug("Empty on stop")
            pass

        if bstop:
            t.debug("Process ({}) has received the stop signal".format(local_name))
            break

        # work with file - wait until the file gets proper status - X seconds modified,
        # decent size - if not, wait

        time.sleep(delay)

        # debugging purposes
        if debug:
            t.debug("New cycle")
            if debug_cnt == 9:
                stop_queue.put("stop")
            debug_cnt = debug_cnt + 1

    t.debug("Worker ({}) is stopped ".format(local_name))

if __name__ == "__main__":
    qfile = Queue()
    qfile.put("123.tif")
    qquit = Queue()

    worker(qfile, qquit, "C:\\Users\\lorcat\\Dropbox\\Mine\\PyCharm\\_by_hosts\\win\\ConvertServer\\log", debug=True)
