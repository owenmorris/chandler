"""Spike tests package"""

import doctest

def test_codegen():
    return doctest.DocFileSuite(
        'codegen.txt', optionflags=doctest.ELLIPSIS, package='spike',
    )

def suite():
    # Return all tests, just codegen doctest for now
    return test_codegen()
