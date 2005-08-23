import unittest

def test_scripting():
    import doctest
    return doctest.DocFileSuite(
        'scripting.txt', optionflags=doctest.ELLIPSIS, package='osaf.framework',
    )


def additional_tests():
    return unittest.TestSuite(
        [ test_scripting(), ]
    )


if __name__=='__main__':
    from run_tests import ScanningLoader
    unittest.main(testLoader = ScanningLoader())

