Chandler README.linux
---------------------

* Compatibility *

Our Linux binaries are built on a RedHat 8 machine that has libc version
2.3.2. To run these binaries, your machine will need libc 2.3.2 or
higher. To see what version of libc you have, run "ldd --version" on
the command line. If you are building Chandler yourself you will need
gcc 3.3.x, as described here:

 http://wiki.osafoundation.org/twiki/bin/view/Chandler/BuildingChandler


* Running Chandler *

To run chandler, use the executable "chandler" in this directory, like
so:

% ./chandler

