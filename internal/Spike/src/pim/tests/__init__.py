"""PIM tests"""

from unittest import TestSuite
from spike.tests import make_docsuite

test_content = make_docsuite('content.txt','pim')

def slow():
    return TestSuite([])

def suite():
    # Return all dependency-free unit tests
    return test_content()
