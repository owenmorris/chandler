import unittest

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
    try:
        from signal import signal, alarm, SIGALRM
    except ImportError:
        pass    # no alarm on Windows  :(
    else:
        # Set up a 90 second maximum timeout
        def timeout(*args):
            alarm(12)
            raise AssertionError("Timeout occurred")
        signal(SIGALRM, timeout)
        alarm(90)

    from run_tests import ScanningLoader
    unittest.main(testLoader = ScanningLoader())

