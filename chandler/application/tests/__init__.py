"""Application tests package

When adding application test modules to this package, please add their
name to the __all__ list, below.  Do not add non-test modules, or module
names outside this package.
"""

__all__ = [
    'TestAllParcels', 'TestAnonymous', 'TestAttributes', 'TestCircular', 
    'TestClasses', 'TestClouds', 'TestCollections', 'TestCopying', 
    'TestDependency','TestItems', 'TestKindAndItem', 'TestLocalAttrs', 
    'TestNamespaceErrors', 'TestParcelErrors', 'TestParcelLoader','TestUuidOf',
    'TestParcelPerf', 'TestSchemaAPI.suite',
]

def suite():
    """Unit test suite; run by testing 'application.tests.suite'"""

    from unittest import defaultTestLoader, TestSuite
    return TestSuite(
        [defaultTestLoader.loadTestsFromName(__name__+'.'+test_name)
            for test_name in __all__]
    )

