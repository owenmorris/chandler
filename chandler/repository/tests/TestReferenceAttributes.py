"""
Unit tests for reference attributes
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import AttributeTestCase, os, unittest

from repository.item.Item import Item
from repository.schema.Attribute import Attribute

class ReferenceAttributesTest(AttributeTestCase.AttributeTestCase):
    """ Test Reference Attributes """

    def testReferenceAttributes(self):
        """Test bidirectional single valued attribute"""
        kind = self._find('//Schema/Core/Kind')
        itemKind = self._find('//Schema/Core/Item')
        self.assert_(itemKind is not None)

        kind1 = Item('kind1', self.rep, kind)
        self.assert_(kind1 is not None)

        item1 = Item('item1', self.rep, itemKind)
        self.assert_(item1 is not None)

        # check kind
        self.assert_(kind1.kind is kind)
        self.assert_(kind1 in kind.items)

        # check kind and otherName
        self.assert_(item1.kind is itemKind)
        self.assert_(item1 in itemKind.items)

        # set kind Attribute (update bidirectional ref)
        item1.kind = kind1
        self.assert_(item1.kind is kind1)

        # now test that  otherName side of kind now = items of kind1
        self.assert_(item1 in kind1.items)
        # and verify item1 no longer in kind.items (old otherName)
        self.assert_(item1 not in kind.items)

        # create a third item and switch kind using __setattr__
        item2 = Item('item2', self.rep, itemKind)
        self.assert_(item2 is not None)
        item2.kind = kind1

        # again, verify kind
        self.assert_(item2.kind is kind1)

        # now verify that otherName side of kind is list cardinality
        self.assertEquals(len(kind1.items), 2)
        self.assert_(item1 in kind1.items)
        self.assert_(item2 in kind1.items)

        # now write what we've done and read it back
        self._reopenRepository()
        kind = self._find('//Schema/Core/Kind')
        itemKind = self._find('//Schema/Core/Item')
        kind1 = self._find('//kind1')
        item1 = self._find('//item1')
        item2 = self._find('//item2')

        # check kind
        self.assert_(kind1.kind is kind)
        self.assert_(kind1 in kind.items)

        # set kind Attribute (update bidirectional ref)
        self.assert_(item1.kind is kind1)

        # now test that otherName side of kind now = items of kind1
        self.assert_(item1 in kind1.items)
        # and verify item1 no longer in kind.items (old otherName)
        self.assert_(item1 not in kind.items)
        # again, verify kind
        self.assert_(item2.kind is kind1)

        # now verify that otherName side of kind is list cardinality
        self.assertEquals(len(kind1.items), 2)
        self.assert_(item1 in kind1.items)
        self.assert_(item2 in kind1.items)

        # test removeAttributeValue
        item2.removeAttributeValue('kind')
        self.failUnlessRaises(AttributeError, lambda: item2.kind)
        self.assertEquals(len(kind1.items), 1)
        self.failIf(item2 in kind1.items)

        # now write what we've done and read it back
        self._reopenRepository()
        kind1 = self._find('//kind1')
        item2 = self._find('//item2')
        self.failUnlessRaises(AttributeError, lambda: item2.kind)
        self.assertEquals(len(kind1.items), 1)
        self.failIf(item2 in kind1.items)

    # support functions for testListReferenceAttributes and testDictReferenceAttributes
    def _findManagerAndEmployees(self):
        """Use find to retrieve our test data from the repository """
        manager = self._find('//boss')
        emp1 = self._find('//employee1')
        emp2 = self._find('//employee2')
        emp3 = self._find('//employee3')
        emp4 = self._find('//employee4')
        return (manager, [emp1, emp2, emp3, emp4])

    def _checkManagerAndEmployees(self, m, es):
        """Make sure a list of employees has the same manager"""
        for i in es:
            self.assertEquals(i.manager, m)
            self.assert_(m.hasValue('employees', i))

    def testListReferenceAttributes(self):
        """Test list valued bidirectional references"""
        (managerKind, employeeKind) = self._createManagerAndEmployeeKinds('list')

        # now write what we've done and read it back
        self._reopenRepository()
        managerKind = self._find('//manager')
        employeesAttribute = managerKind.getAttribute('employees')
        self.assert_(employeesAttribute is not None)
        self.assertEquals(employeesAttribute.cardinality, 'list')
        self.assertEquals(employeesAttribute.getAttributeValue('otherName'),
                          'manager')
        employeeKind = self._find('//employee')
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
        (managerKind, employeeKind) = self._createManagerAndEmployeeKinds('dict')

        # now write what we've done and read it back
        self._reopenRepository()
        managerKind = self._find('//manager')
        employeesAttribute = managerKind.getAttribute('employees')
        self.assert_(employeesAttribute is not None)
        self.assertEquals(employeesAttribute.cardinality, 'dict')
        self.assertEquals(employeesAttribute.getAttributeValue('otherName'),
                          'manager')        
        employeeKind = self._find('//employee')
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
        itemKind = self._find('//Schema/Core/Item')
        self.assert_(itemKind is not None)

        item = Item('item1', self.rep, itemKind)
        attrKind = itemKind.getAttribute('kind').kind

        # subattributes are created by assigning the "parent" attribute
        # to the superAttribute attribute of the "child" attribute
        issuesAttr = itemKind.getAttribute('issues')
        criticalSubAttr = Attribute('critical', issuesAttr, attrKind)
        criticalSubAttr.superAttribute = issuesAttr
        self.assert_(criticalSubAttr.superAttribute is issuesAttr)
        self.assert_(criticalSubAttr in issuesAttr.subAttributes)

        # now do it by assigning to the subAttributes list to ensure that
        # the bidirectional ref is getting updated.
        normalSubAttr = Attribute('normal', issuesAttr, attrKind)
        issuesAttr.subAttributes.append(normalSubAttr)
        self.assert_(normalSubAttr.superAttribute is issuesAttr)
        self.assert_(normalSubAttr in issuesAttr.subAttributes)
        
        # now do it by callin addValue on the Attribute item
        minorSubAttr = Attribute('minor', issuesAttr, attrKind)
        issuesAttr.addValue('subAttributes', minorSubAttr)
        self.assert_(minorSubAttr.superAttribute is issuesAttr)
        self.assert_(minorSubAttr in issuesAttr.subAttributes)

        # now write what we've done and read it back
        self._reopenRepository()
        item = self._find('//item1')
        itemKind = item.kind
        issuesAttr = itemKind.getAttribute('issues')

        attMap = {}
        for i in issuesAttr.subAttributes:
            attMap[i.getItemName()] = i 
            
        criticalSubAttr = attMap['critical']
        normalSubAttr = attMap['normal']
        minorSubAttr = attMap['minor']
        self.assert_(criticalSubAttr.superAttribute is issuesAttr)
        self.assert_(criticalSubAttr in issuesAttr.subAttributes)
        self.assert_(normalSubAttr.superAttribute is issuesAttr)
        self.assert_(normalSubAttr in issuesAttr.subAttributes)
        self.assert_(minorSubAttr.superAttribute is issuesAttr)
        self.assert_(minorSubAttr in issuesAttr.subAttributes)
        
if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
     unittest.main()
