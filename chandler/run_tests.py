"""run_tests.py -- Run specified tests or suites

Usage
-----

Run tests in a specific module::

    RunPython run_tests.py repository.tests.TestText

Run a specific test class::

    RunPython run_tests.py repository.tests.TestText.TestText

Run a specific test method::

    RunPython run_tests.py repository.tests.TestText.TestText.testAppend

Run all tests in a suite::

    RunPython run_tests.py application.tests.suite

A '-v' option can be included to print the name and status of each
test as it runs.  Normally, just a '.' is printed for each passing
test, and an E or F for errors or failing tests.  However, since
some of Chandler's tests produce considerable console output of their
own, it may be hard to see the status dots and letters, so you may
prefer the output produced by '-v'.
"""

import sys
if len(sys.argv)<2 or sys.argv[1] in ('-h','--help'):   # XXX
    print __doc__
    sys.exit(2)

from unittest import main
main(module=None)

