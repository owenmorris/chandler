"""Spike tests package"""

import doctest
from unittest import TestSuite

def make_docsuite(filename,package='spike',**kw):
    def suite():
        return doctest.DocFileSuite(
            filename, optionflags=doctest.ELLIPSIS, package=package, **kw
        )
    return suite        

test_schema = make_docsuite('schema.txt')
test_models = make_docsuite('models.txt')
test_events = make_docsuite('events.txt')
test_codegen = make_docsuite('codegen.txt')

def suite():
    # Return all tests
    return TestSuite(
        [test_schema(), test_models(), test_events(), test_codegen()]
    )
