"""
Unit tests for reference attributes
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import RepositoryTestCase, os, unittest

from repository.item.Item import Item
from repository.schema.Attribute import Attribute

class ReferenceAttributesTest(RepositoryTestCase.RepositoryTestCase):
    """ Test Reference Attributes """

    def testReferenceAttributes(self):
        """Test bidirectional single valued attrribute"""
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

        # now write what we've done and read it back
        self._reopenRepository()
        kind = self.rep.find('//Schema/Core/Kind')
        itemKind = self.rep.find('//Schema/Core/Item')
        item1 = self.rep.find('//item1')
        item2 = self.rep.find('//item2')
        item3 = self.rep.find('//item3')
        # check kind
        self.assertEquals(item1.kind, kind)
        self.assert_(item1 in kind.items)
        # set kind Attribute (update bidirectional ref)
        self.assertEquals(item2.kind, item1)
        # now test that  otherName side of kind now = items of item1
        self.assert_(item2 in item1.items)
        # and verify item2 no longer in kind.items (old otherName)
        self.assert_(item2 not in kind.items)
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

        # now write what we've done and read it back
        self._reopenRepository()
        item1 = self.rep.find('//item1')
        item3 = self.rep.find('//item3')
        self.failUnlessRaises(AttributeError, lambda x: item3.kind, None)
        self.assertEquals(len(item1.items),1)
        self.failIf(item3 in item1.items)

    # support functions for testListReferenceAttributes and testDictReferenceAttributes
    def _findManagerAndEmployees(self):
        """Use find to retrieve our test data from the repository """
        manager = self.rep.find('//boss')
        emp1 = self.rep.find('//employee1')
        emp2 = self.rep.find('//employee2')
        emp3 = self.rep.find('//employee3')
        emp4 = self.rep.find('//employee4')
        return (manager, [emp1, emp2, emp3, emp4])

    def _checkManagerAndEmployees(self, m, es):
        """Make sure a list of employees has the same manager"""
        for i in es:
            self.assertEquals(i.manager, m)
            self.assert_(m.hasValue('employees', i))

    def testListReferenceAttributes(self):
        """Test list valued bidirectional references"""
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

        # now write what we've done and read it back
        self._reopenRepository()
        managerKind = self.rep.find('//manager')
        employeesAttribute = managerKind.getAttribute('employees')
        self.assert_(employeesAttribute is not None)
        self.assertEquals(employeesAttribute.cardinality,'list')
        self.assertEquals(employeesAttribute.getAttributeValue('otherName'),'manager')        
        employeeKind = self.rep.find('//employee')
        managerAttribute = employeeKind.getAttribute('manager')
        self.assert_(managerAttribute is not None)
        self.assertEquals(managerAttribute.otherName,'employees')

        # add employees to manager
        manager = managerKind.newItem('boss', self.rep)

        emp1 = employeeKind.newItem('employee1', self.rep)
        emp2 = employeeKind.newItem('employee2', self.rep)
        emp3 = employeeKind.newItem('employee3', self.rep)
        emp4 = employeeKind.newItem('employee4', self.rep)
        manager.setValue('employees', emp1)
        manager.addValue('employees', emp2)
        manager.addValue('employees', emp3)
        manager.addValue('employees', emp4)
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now write what we've done and read it back
        self._reopenRepository()
        (manager, [emp1, emp2, emp3, emp4]) = self._findManagerAndEmployees()
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now do it from the other end add manager to employees
        manager = managerKind.newItem('boss', self.rep)

        emp1 = employeeKind.newItem('employee1', self.rep)
        emp1.manager = manager
        emp2 = employeeKind.newItem('employee2', self.rep)
        emp2.manager = manager
        emp3 = employeeKind.newItem('employee3', self.rep)
        emp3.manager = manager
        emp4 = employeeKind.newItem('employee4', self.rep)
        emp4.manager = manager
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now write what we've done and read it back
        self._reopenRepository()
        (manager, [emp1, emp2, emp3, emp4]) = self._findManagerAndEmployees()
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

    def testDictReferenceAttributes(self):
        """Test dictionary valued bidirectional references"""
        kind = self.rep.find('//Schema/Core/Kind')
        itemKind = self.rep.find('//Schema/Core/Item')
        attrKind = itemKind.getAttribute('kind').kind

        managerKind = kind.newItem('manager', self.rep)
        employeesAttribute = Attribute('employees',managerKind, attrKind)
        employeesAttribute.setAttributeValue('cardinality','dict')
        employeesAttribute.setAttributeValue('otherName', 'manager')
        managerKind.addValue('attributes',
                             employeesAttribute,alias='employees')
        employeeKind = kind.newItem('employee', self.rep)
        managerAttribute = Attribute('manager',employeeKind, attrKind)
        managerAttribute.setAttributeValue('otherName', 'employees')
        employeeKind.addValue('attributes',
                              managerAttribute,alias='manager')

        # now write what we've done and read it back
        self._reopenRepository()
        managerKind = self.rep.find('//manager')
        employeesAttribute = managerKind.getAttribute('employees')
        self.assert_(employeesAttribute is not None)
        self.assertEquals(employeesAttribute.cardinality,'dict')
        self.assertEquals(employeesAttribute.getAttributeValue('otherName'),'manager')        
        employeeKind = self.rep.find('//employee')
        managerAttribute = employeeKind.getAttribute('manager')
        self.assert_(managerAttribute is not None)
        self.assertEquals(managerAttribute.otherName,'employees')

        # add employees to manager
        manager = managerKind.newItem('boss', self.rep)

        emp1 = employeeKind.newItem('employee1', self.rep)
        emp2 = employeeKind.newItem('employee2', self.rep)
        emp3 = employeeKind.newItem('employee3', self.rep)
        emp4 = employeeKind.newItem('employee4', self.rep)

        manager.setValue('employees', emp1)
        manager.addValue('employees', emp2)
        manager.addValue('employees', emp3)
        manager.addValue('employees', emp4)
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now write what we've done and read it back
        self._reopenRepository()
        (manager, [emp1, emp2, emp3, emp4]) = self._findManagerAndEmployees()
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now do it from the other end add manager to employees
        manager = managerKind.newItem('boss', self.rep)

        emp1 = employeeKind.newItem('employee1', self.rep)
        emp1.manager = manager
        emp2 = employeeKind.newItem('employee2', self.rep)
        emp2.manager = manager
        emp3 = employeeKind.newItem('employee3', self.rep)
        emp3.manager = manager
        emp4 = employeeKind.newItem('employee4', self.rep)
        emp4.manager = manager
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now write what we've done and read it back
        self._reopenRepository()
        (manager, [emp1, emp2, emp3, emp4]) = self._findManagerAndEmployees()
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

    def testSubAttributes(self):
        """Test attributes which have sub attributes (subAttributes and superAttribute attributes)"""
        itemKind = self.rep.find('//Schema/Core/Item')
        self.assert_(itemKind is not None)

        item = Item('item1', self.rep, itemKind)
        attrKind = itemKind.getAttribute('kind').kind

        # subattributes are created by assigning the "parent" attribute
        # to the superAttribute attribute of the "child" attribute
        issuesAttr = itemKind.getAttribute('issues')
        criticalSubAttr = Attribute('critical', issuesAttr, attrKind)
        criticalSubAttr.superAttribute = issuesAttr
        self.assert_(criticalSubAttr.superAttribute == issuesAttr)
        self.assert_(criticalSubAttr in issuesAttr.subAttributes)

        # now do it by assigning to the subAttributes list to ensure that
        # the bidirectional ref is getting updated.
        normalSubAttr = Attribute('normal', issuesAttr, attrKind)
        issuesAttr.subAttributes.append(normalSubAttr)
        self.assert_(normalSubAttr.superAttribute == issuesAttr)
        self.assert_(normalSubAttr in issuesAttr.subAttributes)
        
        # now do it by callin addValue on the Attribute item
        minorSubAttr = Attribute('minor', issuesAttr, attrKind)
        issuesAttr.addValue('subAttributes',minorSubAttr)
        self.assert_(minorSubAttr.superAttribute == issuesAttr)
        self.assert_(minorSubAttr in issuesAttr.subAttributes)

        # now write what we've done and read it back
        self._reopenRepository()
        item = self.rep.find('//item1')
        itemKind = item.kind
        issuesAttr = itemKind.getAttribute('issues')

        attMap = {}
        for i in issuesAttr.subAttributes:
            attMap[i.getItemName()] = i 
            
        criticalSubAttr = attMap['critical']
        normalSubAttr = attMap['normal']
        minorSubAttr = attMap['minor']
        self.assert_(criticalSubAttr.superAttribute == issuesAttr)
        self.assert_(criticalSubAttr in issuesAttr.subAttributes)
        self.assert_(normalSubAttr.superAttribute == issuesAttr)
        self.assert_(normalSubAttr in issuesAttr.subAttributes)
        self.assert_(minorSubAttr.superAttribute == issuesAttr)
        self.assert_(minorSubAttr in issuesAttr.subAttributes)
        
if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
