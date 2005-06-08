import unittest
this_module = "application.tests.TestSchemaAPI"     # change this if it moves

from application import schema
from repository.schema import Types
from repository.persistence.RepositoryView import NullRepositoryView
from repository.query.Query import Query

class Dummy(schema.Item):
    """Just a test fixture"""
    attr = schema.One(schema.String)
    other = schema.Many()

class Other(schema.Item):
    thing = schema.One(Dummy, inverse=Dummy.other)

class Mixed(Dummy, Query):
    pass

class AnEnum(schema.Enumeration):
    values = "yes", "no"

class SchemaTestCase(unittest.TestCase):
    """Reset the schema API between unit tests"""

    def setUp(self):
        schema.reset()  # clear schema state before starting

    def tearDown(self):
        self.failUnless(schema.reset().check(), "check() failed")

class SchemaTests(SchemaTestCase):

    def testDeriveFromCore(self):
        self.assertEqual(
            list(schema.itemFor(Mixed).superKinds),
            [schema.itemFor(Dummy), schema.itemFor(Query)]
        )

    def testResetCache(self):
        # Parcel/kind/attr caches should be cleared between resets
        parcel1 = schema.parcel_for_module(this_module)
        kind1 = schema.itemFor(Dummy)
        attr1 = schema.itemFor(Dummy.attr)

        old = schema.reset()
        parcel2 = schema.parcel_for_module(this_module)
        kind2 = schema.itemFor(Dummy)
        attr2 = schema.itemFor(Dummy.attr)

        self.failIf(parcel2 is parcel1)
        self.failIf(kind2 is kind1)
        self.failIf(attr2 is attr1)

        # But switching back to an old state should restore the cache
        schema.reset(old)
        parcel3 = schema.parcel_for_module(this_module)
        kind3 = schema.itemFor(Dummy)
        attr3 = schema.itemFor(Dummy.attr)
        self.failUnless(parcel3 is parcel1)
        self.failUnless(attr3 is attr1)
        self.failUnless(attr3 is attr1)

    def testAttrKindType(self):
        self.assertEqual(schema.itemFor(Dummy.attr).getAspect('type'),
            schema.nrv.findPath('//Schema/Core/String'))
        self.assertEqual(schema.itemFor(Other.thing).getAspect('type'),
                         schema.itemFor(Dummy))
        self.assertRaises(TypeError, schema.Role, str)

    def testImportAll(self):
        rv = NullRepositoryView()
        schema.initRepository(rv)
        schema.synchronize(rv, this_module)
        path = "//parcels/%s/" % this_module.replace('.','/')
        self.assertNotEqual( rv.findPath(path+'Dummy'), None)
        self.assertNotEqual( rv.findPath(path+'AnEnum'), None)


def test_schema_api():
    import doctest
    return doctest.DocFileSuite(
        'schema_api.txt', optionflags=doctest.ELLIPSIS, package='application',
    )


def additional_tests():
    return unittest.TestSuite(
        [ test_schema_api(), ]
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
