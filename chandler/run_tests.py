"""run_tests.py -- Run specified tests or suites

Usage
-----

Run tests in a specific module::

    RunPython -m run_tests repository.tests.TestText

Run a specific test class::

    RunPython -m run_tests repository.tests.TestText.TestText

Run a specific test method::

    RunPython -m run_tests repository.tests.TestText.TestText.testAppend

Run all tests in a suite::

    RunPython -m run_tests application.tests.TestSchemaAPI.suite

Run all tests in all modules in a package and its sub-packages::

    RunPython -m run_tests application.tests

Run all tests in Chandler::

    RunPython -m run_tests application crypto osaf repository


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

(Note: specifying package names on the 'run_tests' command line will
cause *all* modules in all sub-packages of that package to be imported.)

"""

import sys, os

from unittest import TestLoader, main

class ScanningLoader(TestLoader):

    def loadTestsFromModule(self, module):
        """Return a suite of all tests cases contained in the given module"""

        tests = [TestLoader.loadTestsFromModule(self,module)]

        if hasattr(module, "additional_tests"):
            tests.append(module.additional_tests())

        if hasattr(module, '__path__'):
            for dir in module.__path__:
                for file in os.listdir(dir):
                    if file.endswith('.py') and file!='__init__.py':
                        if file.lower().startswith('test'):
                            submodule = module.__name__+'.'+file[:-3]
                        else:
                            continue
                    else:
                        subpkg = os.path.join(dir,file,'__init__.py')
                        if os.path.exists(subpkg):
                            submodule = module.__name__+'.'+file
                        else:
                            continue
                    tests.append(self.loadTestsFromName(submodule))

        if len(tests)>1:
            return self.suiteClass(tests)
        else:
            return tests[0] # don't create a nested suite for only one return


if __name__ == '__main__':
    if len(sys.argv)<2 or sys.argv[1] in ('-h','--help'):   # XXX
        print __doc__
        sys.exit(2)

    main(module=None, testLoader=ScanningLoader())

