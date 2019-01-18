Setup:
:\tmp\tango\server - exe fle for the server (bat2exe)

nssm should have this mount, otherwise the system won't find the files
before the startup 
net use x: asap /User:BeamlineUser

before the exit
net use x: asap /User:BeamlineUser /DELETE