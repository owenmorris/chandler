__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Founation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

# The query tests package

__all__ = [
    'TestSimpleQueries', 'TestCompoundQueries', 'TestNotification'
]


def suite():
    """Unit test suite; run by testing 'repository.tests.suite'"""

    from unittest import defaultTestLoader, TestSuite
    return TestSuite(
        [defaultTestLoader.loadTestsFromName(__name__+'.'+test_name)
            for test_name in __all__]
    )

