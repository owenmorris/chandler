Chandler README.linux
---------------------

* Compatibility *

Our Linux binaries are built on a computer running Fedora Core 2.
They have been tested on Fedora Core 2, but are unlikely to work
on any other version of Linux.

If you are building Chandler yourself you will need a few extra 
things.  For details on how to build, please see:

 http://wiki.osafoundation.org/twiki/bin/view/Chandler/BuildingChandler


* Running Chandler *

To run chandler, use the executable "RunChandler" in the release or debug
directory, like so:

% ./release/RunChandler

or, if you have a "debug" version: 

% ./debug/RunChandler

If you aren't sure which you have, you can run:

% ./*/RunChandler

