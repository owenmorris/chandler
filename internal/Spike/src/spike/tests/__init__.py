"""Spike tests package"""

import doctest
from unittest import TestSuite

def test_events():
    return doctest.DocFileSuite(
        'events.txt', optionflags=doctest.ELLIPSIS, package='spike',
    )

def test_codegen():
    return doctest.DocFileSuite(
        'codegen.txt', optionflags=doctest.ELLIPSIS, package='spike',
    )


def suite():
    # Return all tests
    return TestSuite([test_events(),test_codegen()])
