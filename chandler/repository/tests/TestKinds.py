"""
Unit tests for kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import RepositoryTestCase, os, unittest

from repository.item.Item import Item
from repository.schema.Attribute import Attribute
from repository.schema.Kind import Kind

class KindTest(RepositoryTestCase.RepositoryTestCase):
    """ Test Kinds  """
    
    def testToXML(self):

        kind = self.rep.find('//Schema/Core/Kind')
        xml = kind.toXML()
        self.failIf(xml is None)
        
        

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
        
