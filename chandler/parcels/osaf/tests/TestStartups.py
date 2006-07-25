#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import unittest, doctest, sys
from StringIO import StringIO

class StopTests(Exception):
    """Stop doctests in progress"""
    
class StoppingRunner(doctest.DocTestRunner):
    """Stop running test cases as soon as a failure or error occurs"""

    def report_failure(*args, **kw):
        doctest.DocTestRunner.report_failure(*args, **kw)
        raise StopTests

    def report_unexpected_exception(*args, **kw):
        doctest.DocTestRunner.report_unexpected_exception(*args, **kw)
        raise StopTests

def test_startups():

    class StoppingCase(doctest.DocFileCase):
    
        def runTest(self):
            test = self._dt_test
            old = sys.stdout
            new = StringIO()
            optionflags = self._dt_optionflags
            if not (optionflags & doctest.REPORTING_FLAGS):
                optionflags |= doctest._unittest_reportflags    
            runner = StoppingRunner(optionflags=optionflags,
                                   checker=self._dt_checker, verbose=False)
            try:
                runner.DIVIDER = "-"*70
                try:
                    failures, tries = runner.run(
                        test, out=new.write, clear_globs=False)
                except StopTests:
                    failures = 1
            finally:
                sys.stdout = old
    
            if failures:
                raise self.failureException(self.format_failure(new.getvalue()))

    test = doctest.DocFileTest(
        'startups.txt', optionflags=doctest.ELLIPSIS, package='osaf',
    )

    test.__class__ = StoppingCase   # ugh
    return test


def additional_tests():
    return unittest.TestSuite(
        [ test_startups(), ]
    )


if __name__=='__main__':
    try:
        from signal import signal, alarm, SIGALRM
    except ImportError:
        pass    # no alarm on Windows  :(
    else:
        # Set up a 90 second maximum timeout
        def timeout(*args):
            raise KeyboardInterrupt("Timeout occurred")
        signal(SIGALRM, timeout)
        alarm(90)

    from util.test_finder import ScanningLoader
    unittest.main(testLoader = ScanningLoader())

