"""profile_tests.py -- Profile specified tests or suites

Usage
-----

Profile tests in a specific module::

    RunPython -m profile_tests repository.tests.TestText

Profile a specific test class::

    RunPython -m profile_tests repository.tests.TestText.TestText

Profile a specific test method::

    RunPython -m profile_tests repository.tests.TestText.TestText.testAppend

Profile all tests in a suite::

    RunPython -m profile_tests repository.tests.suite

By default, the top 10 routines (by time consumed) will be printed,
and the profile statistics will be saved in 'profile.dat'.  However, if
you'd like to query the statistics interactively, add a '-i' before
'profile_tests.py' on the command line, e.g.::

    RunPython -i profile_tests.py repository.tests.TestText

This will drop you to a Python interpreter prompt when the tests are
finished, and you will have a loaded 'stats' object in the variable 's'.
So, to re-sort the statistics by cumulative time and print the top 20
routines, you would do something like this::

    >>> s.sort_stats("cumulative")
    >>> s.print_stats(20)

and a report will be displayed.  For more information on generating
profiler reports, see http://python.org/doc/current/lib/profile-stats.html
or the 'pstats' module chapter of your Python manual.
"""

import sys
from run_tests import ScanningLoader
from unittest import main
from hotshot import Profile
from hotshot.stats import load


if __name__ == '__main__':
    if len(sys.argv)<2 or sys.argv[1] in ('-h','--help'):   # XXX
        print __doc__
        sys.exit(2)

    stats_file = "profile.dat"
    
    try:
        Profile(stats_file).run(
            "main(module=None, testLoader=ScanningLoader())"
        )
    except SystemExit:
        # prevent unittest.main() from forcing an early exit
        pass
    
    s = load(stats_file)
    s.sort_stats("time")
    s.print_stats(10)

