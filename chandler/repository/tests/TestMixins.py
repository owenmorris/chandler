
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from repository.persistence.XMLRepository import XMLRepository
from repository.tests.RepositoryTestCase import RepositoryTestCase

from repository.item.Item import Item
from repository.schema.Attribute import Attribute
from repository.schema.Kind import Kind

class MixinTest(RepositoryTestCase):
    """
    Unit tests for mixin kinds
    """

    def setUp(self):

        super(MixinTest, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.rep.loadPack(cineguidePack)
        self.rep.commit()

    def testMixin(self):

        kh = self.rep.findPath('//CineGuide/KHepburn')
        m1 = kh.movies.first()
        actor = kh.itsKind
        movie = m1.itsKind
        attribute = actor.getAttribute('movies').itsKind
        self.assert_(kh.isItemOf(actor))

        mixin = kh.mixinKinds(('add', movie), ('add', attribute))
        self.assert_(kh.isItemOf(mixin))
        self.assert_(kh.isItemOf(actor))
        self.assert_(kh.isItemOf(movie))
        self.assert_(kh.isItemOf(attribute))
        self.assert_(isinstance(kh, Attribute))

        mixin = kh.mixinKinds(('remove', attribute))
        self.assert_(kh.isItemOf(mixin))
        self.assert_(kh.isItemOf(actor))
        self.assert_(kh.isItemOf(movie))
        self.assert_(not kh.isItemOf(attribute))
        self.assert_(not isinstance(kh, Attribute))
        
        mixin = kh.mixinKinds(('remove', movie))
        self.assert_(kh.isItemOf(mixin))
        self.assert_(kh.isItemOf(actor))
        self.assert_(not kh.isItemOf(movie))
        self.assert_(not kh.isItemOf(attribute))
        self.assert_(not isinstance(kh, Attribute))
        self.assert_(mixin is actor)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestMixins.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
