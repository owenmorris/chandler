__version__ 	= "$Revision$"
__date__ 	= "$Date$"
__copyright__ 	= "Copyright (c) 2003 Open Source Applications Foundation"
__license__	= "GPL -- see LICENSE.txt"

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

HardHat README.txt
Morgen Sagen

HardHat is the Chandler project build tool, consisting of a set
of Python scripts which orchestrate the building of all the modules
required by Chandler.  In our CVS repository we have checked in copies
of many third-party modules such as Python, wxPython, and ZODB to make
it easier for folks to build the complete system without having to go
get each module separately.  Each module uses different build frameworks
such as Makefiles, VisualStudio projects, or distutils packages, and so
HardHat encapsulates each of those in a Python module with "build()",
"clean()", etc. methods.

Each module's directory contains a __hardhat__.py file that contains the
code needed to invoke that module's build operations.  You use HardHat
by cd'ing to a module's directory and specifying which operation to
perform on that module (build, clean, scrub*, execute).  In addition you
can tell HardHat to perform an operation on all of the modules that the
current module depends on.  For example, wxPython requires that Python
already be built, so doing a "build-with-dependencies" operation will
first build Python, then wxPython.  Finally, you can choose whether to
build with debugging flags turned on or off.

Output from all operations is captured to a file named hardhat.log;
this includes details about the environment the operations are running
in such as current working directory, all environment variables, exit
code, and command line.  The logs are created in the project's root
directory (in Chandler's case that is "osaf/chandler") and are rotated 
(with a history of 5 past logs) upon each HardHat run. 

(*scrub:  see the description under -s command line option below)



HardHat command line options
----------------------------

-b 	build module 

	Run the build method of the module in the current directory.


-B 	build module and its dependencies

	Determine the tree of dependencies (modules which must be built
	before the current module), build all of those, then build the
	module in the current directory.


-c 	clean module 

	Run the clean method of the module in the current directory.


-C 	clean module and its dependencies

	Perform the clean operation of the module in the current directory,
	then clean all of its dependencies, in the reverse order from how
	they were built.


-d      use debug version
	
	All subsequent operations will have debugging flags turned on.
	This debug flag will stay set within the current run of HardHat
	until the -r flag is specified.  Example:  "hardhat.py -dB"
	would do a debug build.


-D      create a distribution

	Reads a manifest file which describes how to put together an
	"end-user" distribution of a project, and creates the distribution
	in the directory "distrib".

	
-h      display usage


-n      non-interactive (won't prompt during scrubbing)

	Useful when running in a batch mode, this flag tells HardHat not
	to prompt the user for whether they wan't to remove files during
	a scrub.


-r      use release version (this is the default)

	Turns off the debugging flags for subsequent operations.  For
	example:  "hardhat.py -dBCrB" would do a debug build, clean, 
	the a non-debug (or "release") build.


-s      scrub module (remove all local files not in CVS)

	Scrubbing a module removes all local files in that module's 
	directory hierarchy that are not listed in CVS/Entries or
	CVS/Entries.log.  It's useful for ensuring that your module
	is *really* clean.  Use with caution.  If you have created
	a new file somewhere in a module's directory hierarchy and
	haven't yet checked it into CVS it would get removed by a
	scrub.  HardHat will examine the files in the module and provide
	a list of those not under CVS control and ask you if you really
	want to remove them, so you have a chance to change your mind
	(unless you have given the -n option as well).


-S      scrub module and its dependencies

	Scrubs a module and all modules this one depends on.  Use with
	caution.


-t 	test module 

	Recurse through this module's directories looking for directories
	named "tests".  If such a directory is found, then all files
	named "Test*.py" within that directory are run using the Python
	HardHat has built, and exit codes are examined, looking for test
	failures.
	

-x 	execute module

	Invokes the run operation of the module.  This is one way to run
	Chandler, by cd'ing to osaf/chandler/Chandler and running
	"hardhat.py -x".  If you want to run using the debug versions of
	the modules you built with -dB run "hardhat.py -dx".



Build Instructions for Chandler
-------------------------------

- Make sure you have Python installed on your system.
- set your CVSROOT to :pserver:username@cvs.osafoundation.org:/usr/local/cvsrep
- cvs login
- cvs checkout hardhat  (to retrieve HardHat)
- cvs checkout chandler-source  (to retreive Chandler and required modules)


The following commands should be run from the osaf/chandler/Chandler directory 
that you checked out via "cvs checkout chandler-source":

- Build entire tree:
hardhat.py -B 

- Run Chandler using the non-debug binaries:
hardhat.py -x

- Clean entire tree:
hardhat.py -C

- Build entire tree (with debugging flags passed to each module):
hardhat.py -dB

- Run Chandler using the debug binaries:
hardhat.py -dx


- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

Also:

If you want to run an aribtrary python script via the release or debug
version of Python that you have built (as opposed to your system's installed 
python), cd to a diretory that has a __hardhat__.py file and do the following:

hardhat.py path/to/myscript.py

For example, to run the wxPython demo using the Python you built, cd to
osaf/chandler/wxpython and run:

hardhat.py wxPython/demo/demo.py
