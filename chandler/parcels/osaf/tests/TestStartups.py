import unittest

from application import schema
from repository.schema import Types
from repository.persistence.RepositoryView import NullRepositoryView
from repository.query.Query import Query

def test_startups():
    import doctest
    return doctest.DocFileSuite(
        'startups.txt', optionflags=doctest.ELLIPSIS, package='osaf',
    )


def additional_tests():
    return unittest.TestSuite(
        [ test_startups(), ]
    )


if __name__=='__main__':
    from run_tests import ScanningLoader
    unittest.main(testLoader = ScanningLoader())

