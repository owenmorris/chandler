"""Repository tests package

When adding repository test modules to this package, please add their
name to the __all__ list, below.  Do not add non-test modules, or module
names outside this package.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

# The tests package

__all__ = [
    'TestAlias', 'TestBZ2', 'TestBinary', 'TestDeepCopyRef', 'TestDelete',
    'TestIndexes', 'TestItems', 'TestKinds', 'TestLiteralAttributes',
    'TestMerge', 'TestMixins', 'TestMove', 'TestPerfWithRSS',
    'TestPersistentCollections', 'TestRedirectToOrdering', 'TestRefDictAlias',
    'TestReferenceAttributes', 'TestRepository', 'TestRepositoryBasic',
    'TestSkipList', 'TestText', 'TestTypes',
]


def suite():
    """Unit test suite; run by testing 'repository.tests.suite'"""

    from unittest import defaultTestLoader, TestSuite
    return TestSuite(
        [defaultTestLoader.loadTestsFromName(__name__+'.'+test_name)
            for test_name in __all__]
    )

