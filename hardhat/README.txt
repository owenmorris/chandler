HardHat README.txt

HardHat is the Chandler build tool, consisting of a set of Python scripts
which build a collection of subsystems in
a modular fashion.  Each subsystem directory contains a python file
implementing build, clean, and execution methods.  HardHat sets up 
the environment appropriately and calls each of these methods as 
needed.  This approach allows each subsystem to use whatever particular
build technology is required (make, distutils, VisualStudio solution),
and provides a uniform interface for invoking them.  Output from all the
subsystem builds is captured to a file named hardhat.log.
Since HardHat is itself a Python module wrapped by a Python command-line
script, the module could be embedded in another application such as an 
automated build system, or perhaps a GUI.
   

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Build Instructions for Chandler
-------------------------------

- Make sure you have Python installed on your system.
- set your CVSROOT to :pserver:username@cvs.osafoundation.org:/usr/local/cvsrep
- cvs login
- cvs checkout hardhat  (to retrieve HardHat)
- cvs checkout chandler-source  (to retreive Chandler and required libraries)


The following commands should be run from the osaf/chandler directory that
you checked out via "cvs checkout chandler-source":

- Build entire tree:
hardhat.py -B 

- Build entire tree (with debugging flags passed to each module):
hardhat.py -dB

- Run Chandler using the non-debug binaries:
hardhat.py -x

- Run Chandler using the debug binaries:
hardhat.py -dx

- Clean entire tree:
hardhat.py -C



HardHat commandline options
---------------------------

-b 	build module 
-B 	build module and its dependencies
-c 	clean module 
-C 	clean module and its dependencies
-d      use debug version
-D      create a distribution
-h      display usage
-n      non-interactive (won't prompt during scrubbing)
-r      use release version (this is the default)
-s      scrub module (remove all local files not in CVS)
-S      scrub module and its dependencies
-t 	test module 
-x 	execute module

If you want to run an aribtrary python script via the release or debug
version of python that you have built (as opposed to your system's installed 
python), cd to a diretory that has a __hardhat__.py file (the osaf/chandler
directory for example) and do the following:

hardhat.py path/to/myscript.py

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

