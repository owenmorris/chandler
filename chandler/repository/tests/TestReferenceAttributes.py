"""
Unit tests for reference attributes
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from bsddb.db import DBNoSuchFileError
from repository.item.Item import Item
from repository.item.ItemRef import RefDict
from repository.schema.Attribute import Attribute
from repository.schema.Kind import ItemKind
from repository.schema.Kind import Kind
from repository.persistence.XMLRepository import XMLRepository
import repository.schema.Types

class ReferenceAttributesTest(unittest.TestCase):
    """ Test Reference Attributes """

    def setUp(self):
        rootdir = os.environ['CHANDLERDIR']
        schemaPack = os.path.join(rootdir, 'repository', 'packs', 'schema.pack')
        self.rep = XMLRepository('ReferenceAttributesUnitTest-Repository')
        self.rep.create()
        self.rep.loadPack(schemaPack)

    def testReferenceAttributes(self):
        kind = self.rep.find('//Schema/Core/Kind')
        itemKind = self.rep.find('//Schema/Core/Item')
        self.assert_(itemKind is not None)

        item1 = Item('item1', self.rep, kind)
        self.assert_(item1 is not None)

        item2 = Item('item2', self.rep, itemKind)
        self.assert_(item2 is not None)

        # check kind
        self.assertEquals(item1.kind, kind)
        self.assert_(item1 in kind.items)

        # check kind and otherName
        self.assertEquals(item2.kind, itemKind)
        self.assert_(item2 in itemKind.items)
        # set kind Attribute (update bidirectional ref)
        item2.setAttributeValue('kind', item1)
        self.assertEquals(item2.kind, item1)
        # now test that  otherName side of kind now = items of item1
        self.assert_(item2 in item1.items)
        # and verify item2 no longer in kind.items (old otherName)
        self.assert_(item2 not in kind.items)

        # create a third item and switch kind using __setattr__
        item3 = Item('item3', self.rep, itemKind)
        self.assert_(item3 is not None)
        item3.kind = item1 
        # again, verify kind
        self.assertEquals(item3.kind, item1)
        # now verify that otherName side of kind is list cardinality
        self.assertEquals(len(item1.items), 2)
        self.assert_(item2 in item1.items)
        self.assert_(item3 in item1.items)

        # test removeAttributeValue
        item3.removeAttributeValue('kind')
        self.failUnlessRaises(AttributeError, lambda x: item3.kind, None)
        self.assertEquals(len(item1.items),1)
        self.failIf(item3 in item1.items)

    def testListReferenceAttributes(self):
        kind = self.rep.find('//Schema/Core/Kind')
        itemKind = self.rep.find('//Schema/Core/Item')
        attrKind = itemKind.getAttribute('kind').kind

        managerKind = kind.newItem('manager', self.rep)
        employeesAttribute = Attribute('employees',managerKind, attrKind)
        employeesAttribute.setAttributeValue('cardinality','list')
        employeesAttribute.setAttributeValue('otherName', 'manager')
        managerKind.addValue('attributes',
                             employeesAttribute,alias='employees')
        employeeKind = kind.newItem('employee', self.rep)
        managerAttribute = Attribute('manager',employeeKind, attrKind)
        managerAttribute.setAttributeValue('otherName', 'employees')
        employeeKind.addValue('attributes',
                              managerAttribute,alias='manager')

        manager = managerKind.newItem('boss', self.rep)

        emp1 = employeeKind.newItem('employee1', self.rep)
        emp2 = employeeKind.newItem('employee2', self.rep)
        emp3 = employeeKind.newItem('employee3', self.rep)
        emp4 = employeeKind.newItem('employee4', self.rep)

        manager.setValue('employees', emp1)
        print 'manager', manager
        print 'managerKind', managerKind.getAttribute('employees')
        print 'card', manager.getAttributeAspect('employees','cardinality')
        print 'employees', manager.employees
        print 'first', manager.employees.first()
        self.assert_(manager.hasValue('employees',emp1))
        self.assertEquals(emp1.manager, manager)
        self.assert_(manager.hasValue('employees',emp1))
        manager.addValue('employees', emp2)
        self.assertEquals(emp2.manager, manager)
        self.assert_(manager.hasValue('employees',emp2))
        manager.addValue('employees', emp3)
        self.assertEquals(emp3.manager, manager)
        self.assert_(manager.hasValue('employees',emp3))
        manager.addValue('employees', emp4)
        self.assertEquals(emp4.manager, manager)
        self.assert_(manager.hasValue('employees',emp4))

        print manager.employees
        print emp1.manager
        print emp2.manager
        print emp3.manager
        print emp4.manager

    def testSubAttributes(self):
        itemKind = self.rep.find('//Schema/Core/Item')
        self.assert_(itemKind is not None)

        item = Item('item1', self.rep, itemKind)
        attrKind = itemKind.getAttribute('kind').kind

        # subattributes are created by assigning the "parent" attribute
        # to the superAttribute attribute of the "child" attribute
        issuesAttr = itemKind.getAttribute('issues')
        subAttr = Attribute('critical', issuesAttr, attrKind)
        subAttr.superAttribute = issuesAttr
        self.assert_(subAttr.superAttribute == issuesAttr)
        self.assert_(subAttr in issuesAttr.subAttributes)

        # now do it by assigning to the subAttributes list to ensure that
        # the bidirectional ref is getting updated.
        subAttr = Attribute('normal', issuesAttr, attrKind)
        issuesAttr.subAttributes.append(subAttr)
        self.assert_(subAttr.superAttribute == issuesAttr)
        self.assert_(subAttr in issuesAttr.subAttributes)
        
        # now do it by callin addValue on the Attribute item
        subAttr = Attribute('minor', issuesAttr, attrKind)
        issuesAttr.addValue('subAttributes',subAttr)
        self.assert_(subAttr.superAttribute == issuesAttr)
        self.assert_(subAttr in issuesAttr.subAttributes)

    def tearDown(self):
        self.rep.close()
        self.rep.delete()
        pass

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
