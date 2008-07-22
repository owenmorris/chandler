#   Copyright (c) 2003-2008 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import unittest
this_module = "application.tests.TestSchemaAPI"     # change this if it moves
from i18n.tests import uw

from application import schema, tests
from chandlerdb.schema import Types
from chandlerdb.persistence.RepositoryView import NullRepositoryView

class Dummy(schema.Item):
    """Just a test fixture"""
    attr = schema.One(schema.Text)
    other = schema.Many()

class Other(schema.Item):
    thing = schema.One(Dummy, inverse=Dummy.other)


TEST_PATH = "//this/is/a/test"

class Mixed(Dummy, Types.Type):
    __default_path__ = TEST_PATH

class AnEnum(schema.Enumeration):
    values = "yes", "no"

class CoreAnnotation(schema.Annotation):
    schema.kindInfo(annotates=schema.Kind)
    extraInfo = schema.One(schema.Text)
    otherItem = schema.One(schema.Item, inverse=schema.Sequence())

class ForwardAnnotation(schema.Annotation):
    schema.kindInfo(annotates=Dummy)
    fwd_attr1 = schema.One() # XXX ForwardAnnotation
    fwd_attr2 = schema.One()

class OtherForward(schema.Annotation):
    schema.kindInfo(annotates=Dummy)
    foo = schema.One(inverse=ForwardAnnotation.fwd_attr2)

class SchemaTestCase(unittest.TestCase):
    """Reset the schema API between unit tests"""

    def setUp(self):
        self.rv = NullRepositoryView(verify=True)

    def tearDown(self):
        self.failUnless(self.rv.check(), "check() failed")

class SchemaTests(SchemaTestCase):

    def testDeriveFromCore(self):
        self.assertEqual(
            list(schema.itemFor(Mixed, self.rv).superKinds),
            [schema.itemFor(Dummy, self.rv), schema.itemFor(Types.Type, self.rv)]
        )

    def testAttrKindType(self):
        self.assertEqual(schema.itemFor(Dummy.attr, self.rv).getAspect('type'),
            self.rv.findPath('//Schema/Core/Text'))
        self.assertEqual(schema.itemFor(Other.thing, self.rv).getAspect('type'),
                         schema.itemFor(Dummy, self.rv))
        self.assertRaises(TypeError, schema.Descriptor, str)

    def testImportAll(self):
        schema.initRepository(self.rv)

        # Verify that //userdata and the test default path don't exist
        self.assertRaises(KeyError, lambda: self.rv['userdata'])
        self.assertEqual( self.rv.findPath(TEST_PATH), None)

        schema.synchronize(self.rv, this_module)
        path = "//parcels/%s/" % this_module.replace('.','/')

        # Everything should exist now, including the default parent objects
        self.assertNotEqual( self.rv.findPath(TEST_PATH), None)
        self.assertNotEqual( self.rv.findPath("//userdata"), None)
        self.assertNotEqual( self.rv.findPath(path+'Dummy'), None)
        self.assertNotEqual( self.rv.findPath(path+'AnEnum'), None)

    def testAnnotateKind(self):
        kind_kind = schema.itemFor(schema.Kind, self.rv)
        CoreAnnotation(kind_kind).extraInfo = uw("Foo")
        self.assertEqual(CoreAnnotation(kind_kind).extraInfo, uw("Foo"))
        parcel = schema.parcel_for_module(__name__, self.rv)
        CoreAnnotation(kind_kind).otherItem = parcel
        self.assertEqual(
            list(getattr(parcel, __name__+".CoreAnnotation.otherItem.inverse")),
            [kind_kind]
        )

    def testAnnotateForwardRefs(self):
        schema.itemFor(ForwardAnnotation, self.rv)


def test_schema_api():
    import doctest
    return doctest.DocFileSuite(
        'parcel-schema-guide.txt',
        'schema_api.txt',
        optionflags=doctest.ELLIPSIS, package='application',
        globs=tests.__dict__
    )


def additional_tests():
    return unittest.TestSuite(
        [ test_schema_api(), ]
    )


if __name__=='__main__':
    # This module can't be safely run as __main__, so it has to be re-imported
    # and have *that* copy run.
    from util.test_finder import ScanningLoader
    unittest.main(
        module=None, testLoader = ScanningLoader(),
        argv=["unittest", this_module]
    )
else:
    assert __name__ == this_module, (
        "This module must be installed in its designated location"
    )
