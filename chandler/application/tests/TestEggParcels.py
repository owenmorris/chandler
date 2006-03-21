import unittest
this_module = "application.tests.TestEggParcels"     # change this if it moves


def test_egg_parcels():
    import doctest
    return doctest.DocFileSuite(
        'egg-parcel-tests.txt',
        optionflags=doctest.ELLIPSIS, package='application.tests',
    )


def additional_tests():
    return unittest.TestSuite(
        [ test_egg_parcels(), ]
    )


if __name__=='__main__':
    # This module can't be safely run as __main__, so it has to be re-imported
    # and have *that* copy run.
    from run_tests import ScanningLoader
    unittest.main(
        module=None, testLoader = ScanningLoader(),
        argv=["unittest", this_module]
    )
else:
    assert __name__ == this_module, (
        "This module must be installed in its designated location"
    )
