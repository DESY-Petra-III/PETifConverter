# PETifConverter - Tango server with a focus on Tif data conversion 
written by K. Glazyrin

## Purpose
Petra-III at DESY uses Perkin-Elmer XRD1621 (4M) detector which, by means of QXRD software.
QXRD software produces Tif files for our station, which are have pixels of float type. 

We want a server modifying original Tif files or creating New files almost on the fly for:
* Arbitary '.tif' file data frame rotation (mult. of 90Degrees)/flip operations (+)
* Conversion into a .tif format supported by XDI software [XDI](http://www.hpcat.aps.anl.gov/webdata/ross/xdi/) written by Ross Hrubiak. (+)

## Tango Server
The tango server can be run on Linux and Windows.
The initial support was written for Python 3.6, [PyTango 9.2.3](https://github.com/NexeyaSGara/pytango/releases)
The basic operations were tested.

#### Configuration
Server has only one parameter configurable through the Tango Database - property (**numworkers**)
In addition to that one could use **app\config\main_config.py** to start from scratch, without using the Tango Properties

In the initial state the server produces lots of debugging messages, in order to reduce them, please open the file **app\common\tester.py**
and uncomment **__# DEBUG_LEVEL = logging.INFO__** on the line **#10**

#### Tango Properties
**numworkers** - sets the number of processes started during the initialization stage (multiptocessing.Process)

#### Tango Attributes
All attributes are read only. 

|**Attributes**                 | **Type** | **Description** |
| ------------- |:-------------:| -----:|
|**NumProcessed**           | ReadOnly | Number of processed files ( all files, even non correctly formed ) |
|**NumWorkers**             | ReadOnly | Number of workers - multiprocessing.Process used for data conversion. Set by means of the **app\config\main_config.py** or by **numworkers** property|
|**ConfRotation**           | ReadOnly | Rotation of the image. Set in **app\config\main_config.py** |
|**ConfFlip**               | ReadOnly | Flip of the image in a convension of numpy.ndarray.flip. Set in **app\config\main_config.py**|
|**ConfType**               | ReadOnly | Numerical type of the written pixel. Set in **app\config\main_config.py**|
|**StatisticsTotalFrames**  | ReadOnly | Total frames converted (real .tif files)|
|**StatisticsTotalTime**    | ReadOnly | Total time used for conversion of all .tif files|
|**StatisticsAverageTime**  | ReadOnly | Average conversion time per a frame|

#### Tango Commands
|**Attributes**                 | **Input** | **Description** |
| ------------- |:-------------:| -----:|
|AddFiles|[str]| Adds a list of files (or a single file) for conversion|
|AddFolder|str|Adds a folder for conversion|

## Procedure
If a *'.tif'* file is added to the queue for processing, no processing of the file will take place, unless within a given
timeout (**app\config\main_config.py**, default 15s) all of the following conditions will be satisfied:
* timestamp of file modification is 3s older than the current timestamp
* file size is lower than 16Mb 

## Future expansion
Creating ESPERANTO files for data processing with Crysalis software

## Python Libraries used
Conventional
* sys
* os
* logging
* time
* glob
* shutil
* signal
* ctypes
* multiprocessing
* queue
* copy

Non conventional
* NumPy
* PyTango
* fabio

 