"""Spike tests package"""

import doctest
from unittest import TestSuite, defaultTestLoader

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
test_uuidgen = make_docsuite('uuidgen.txt')



def all():
    # Return all tests
    return TestSuite( [suite(), slow()] )

def slow():
    return TestSuite([
        test_codegen(), defaultTestLoader.loadTestsFromNames(
            ['pim.tests.slow']
        )
    ])

def suite():
    # Return all dependency-free unit tests
    return TestSuite(
        [test_uuidgen(), test_events(), test_models(), test_schema(),
            defaultTestLoader.loadTestsFromNames(
                ['pim.tests.suite', 'spike.tests.test_query'])
        ]
    )

