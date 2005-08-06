"""Sharing tests package

When adding sharing test modules to this package, please add their
name to the __all__ list, below.  Do not add non-test modules, or module
names outside this package.
"""

__all__ = [
    'TestFileSystemSharing', 'TestICalendar', 'TestLargeImportICalendar', 
]

def suite():
    """Unit test suite; run by testing 'parcels.osaf.sharing.tests.suite'"""
    from run_tests import ScanningLoader
    from unittest import defaultTestLoader, TestSuite
    loader = ScanningLoader()
    return TestSuite(
        [loader.loadTestsFromName(__name__+'.'+test_name)
            for test_name in __all__]
    )

