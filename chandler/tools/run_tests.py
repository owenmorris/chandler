"""
run_tests.py -- Run specified tests or suites

Usage
-----

Run tests in a specific module::

    RunPython ./tools/run_tests.py repository.tests.TestText

Run a specific test class::

    RunPython ./tools/run_tests.py repository.tests.TestText.TestText

Run a specific test method::

    RunPython ./tools/run_tests.py repository.tests.TestText.TestText.testAppend

Run all tests in a suite::

    RunPython ./tools/run_tests.py application.tests.TestSchemaAPI.suite

Run all tests in all modules in a package and its sub-packages::

    RunPython ./tools/run_tests.py application.tests

Run all tests in Chandler::

    RunPython ./tools/run_tests.py application crypto osaf repository


A '-v' option can be included after 'run_tests' to print the name and
status of each test as it runs.  Normally, just a '.' is printed for each
passing test, and an E or F for errors or failing tests.  However, since
some of Chandler's tests produce considerable console output of their
own, it may be hard to see the status dots and letters, so you may
prefer the output produced by '-v'.

If you have doctests or other tests not based on the Python unittest
module, you should add them to an 'additional_tests' function in your
module, in order for run_test's test finder to be able to locate them.
The function should return a 'unittest.TestSuite' object (such as is
returned by 'doctest.DocFileSuite' or 'doctest.DocTestSuite').

Logging is configured in the same manner as for Chandler or headless.py,
i.e. by setting the CHANDLERLOGCONFIG environment variable or the -L <file>
command line argument to specify a logging configuration file.  For example:

    RunPython ./tools/run_tests.py -L custom.conf -v application osaf

(Note: specifying package names on the 'run_tests' command line will
cause *all* modules in all sub-packages of that package to be imported.)

"""

import sys

from unittest import main
from application import Globals, Utility
from util import test_finder


if __name__ == '__main__':

    if len(sys.argv)<2 or sys.argv[1] in ('-h','--help'):   # XXX
        print __doc__
        sys.exit(2)

    options = Globals.options
    Utility.initI18n(options)
    Utility.initLogging(options)

    # Rebuild the command line for unittest.main
    args = [sys.argv[0]]
    if options.verbose:
        args.append('-v')
    if options.quiet:
        args.append('-q')
    # options.args has all the leftover arguments from Utility
    sys.argv = args + options.args

    main(module=None, testLoader=test_finder.ScanningLoader())

