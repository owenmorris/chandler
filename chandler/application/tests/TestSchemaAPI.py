import unittest
this_module = "application.tests.TestSchemaAPI"     # change this if it moves

from application import schema
from repository.schema import Types
from repository.persistence.RepositoryView import NullRepositoryView

class Dummy(schema.Item):
    """Just a test fixture"""
    attr = schema.One(Types.String)
    other = schema.Many()

class Other(schema.Item):
    thing = schema.One(Dummy, inverse=Dummy.other)


class SchemaTestCase(unittest.TestCase):
    """Reset the schema API between unit tests"""

    def setUp(self):
        schema.reset()  # clear schema state before starting

    def tearDown(self):
        self.failUnless(schema.reset().check(), "check() failed")

class SchemaTests(SchemaTestCase):

    def testResetCache(self):
        # Parcel/kind/attr caches should be cleared between resets
        parcel1 = schema.parcel_for_module(this_module)
        kind1 = Dummy._schema_kind
        attr1 = Dummy.attr._schema_attr

        old = schema.reset()
        parcel2 = schema.parcel_for_module(this_module)
        kind2 = Dummy._schema_kind
        attr2 = Dummy.attr._schema_attr

        self.failIf(parcel2 is parcel1)
        self.failIf(kind2 is kind1)
        self.failIf(attr2 is attr1)

        # But switching back to an old state should restore the cache
        schema.reset(old)
        parcel3 = schema.parcel_for_module(this_module)
        kind3 = Dummy._schema_kind
        attr3 = Dummy.attr._schema_attr
        self.failUnless(parcel3 is parcel1)
        self.failUnless(attr3 is attr1)
        self.failUnless(attr3 is attr1)

    def testAttrKindType(self):
        self.assertEqual(Dummy.attr._schema_attr.getAspect('type'),
            schema.nrv.findPath('//Schema/Core/String'))
        self.assertEqual(Other.thing._schema_attr.getAspect('type'),
                         Dummy._schema_kind)
        self.assertRaises(TypeError, schema.Role, str)

    def testImportAll(self):
        rv = NullRepositoryView()
        schema.initRepository(rv)
        schema.synchronize(rv, this_module)
        path = "//parcels/%s" % this_module.replace('.','/')
        self.assertNotEqual( rv.findPath(path+'/Dummy'), None)


def test_schema_api():
    import doctest
    return doctest.DocFileSuite(
        'schema_api.txt', optionflags=doctest.ELLIPSIS, package='application',
    )

def suite():
    return unittest.TestSuite(
        [
            test_schema_api(),
            unittest.defaultTestLoader.loadTestsFromName(__name__)
        ]
    )

if __name__=='__main__':
    # This module can't be safely run as __main__, so it has to be re-imported
    # and have *that* copy run.
    unittest.main(
        module=None,
        argv=["unittest", this_module+".suite"]
    )
else:
    assert __name__ == this_module, (
        "This module must be installed in its designated location"
    )
