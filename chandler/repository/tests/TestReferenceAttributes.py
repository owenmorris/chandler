"""
Unit tests for reference attributes
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import AttributeTestCase, os, unittest

from repository.item.Item import Item
from repository.schema.Attribute import Attribute

class ReferenceAttributesTest(AttributeTestCase.AttributeTestCase):
    """ Test Reference Attributes """

    # support functions for testListReferenceAttributes and testDictReferenceAttributes
    def _findManagerAndEmployees(self, mPath, e1Path, e2Path, e3Path, e4Path):
        """Use find to retrieve our test data from the repository """
        manager = self._find(mPath)
        emp1 = self._find(e1Path)
        emp2 = self._find(e2Path)
        emp3 = self._find(e3Path)
        emp4 = self._find(e4Path)
        return (manager, [emp1, emp2, emp3, emp4])

    def _checkManagerAndEmployees(self, m, es):
        """Make sure a list of employees has the same manager"""
        for i in es:
            self.assertEquals(i.manager, m)
            self.assert_(m.hasValue('employees', i))

    def testListReferenceAttributes(self):
        """Test dictionary valued bidirectional references"""
        (managerKind, employeeKind) = self._createManagerAndEmployeeKinds('list')

        # now write what we've done and read it back
        self._reopenRepository()
        managerKind = self._find('//manager')
        employeesAttribute = managerKind.getAttribute('employees')
        self.assertEquals(employeesAttribute.cardinality, 'list')
        self.assertEquals(employeesAttribute.getAttributeValue('otherName'),
                          'manager')        
        employeeKind = self._find('//employee')
        managerAttribute = employeeKind.getAttribute('manager')
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
        managerKind = self.rep['manager']
        employeeKind = self.rep['employee']
        (manager, [emp1, emp2, emp3, emp4]) = self._findManagerAndEmployees('//boss','//employee1','//employee2','//employee3','//employee4')
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now do it from the other end add manager to employees
        manager = managerKind.newItem('bossA', self.rep)

        emp1 = employeeKind.newItem('employeeA1', self.rep)
        emp1.manager = manager
        emp2 = employeeKind.newItem('employeeA2', self.rep)
        emp2.manager = manager
        emp3 = employeeKind.newItem('employeeA3', self.rep)
        emp3.manager = manager
        emp4 = employeeKind.newItem('employeeA4', self.rep)
        emp4.manager = manager
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now write what we've done and read it back
        self._reopenRepository()
        (manager, [emp1, emp2, emp3, emp4]) = self._findManagerAndEmployees('//bossA','//employeeA1','//employeeA2','//employeeA3','//employeeA4')
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now test reassigning the same ref collection
        numEmployees = len(manager.employees)
        manager.employees = manager.employees
        self.assert_(len(manager.employees) == numEmployees)

        # make sure extend() works, and len gives the right answer.
        empClone = []
        for anEmp in manager.employees:
            empClone.append(anEmp)
        print "manager has %d employees" % len(manager.employees)
        manager.employees = empClone
        print "manager has %d employees" % len(manager.employees)
        print "manager has %d employee values" % len(manager.employees.values())
        self.assert_(len(manager.employees) == numEmployees)

    def testSubAttributes(self):
        """Test attributes which have sub attributes (subAttributes and superAttribute attributes)"""
        itemKind = self._find('//Schema/Core/Item')
        self.assert_(itemKind is not None)

        item = Item('item1', self.rep, itemKind)
        attrKind = itemKind.itsParent['Attribute']

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
        itemKind = item.itsKind
        issuesAttr = itemKind.getAttribute('issues')

        attMap = {}
        for i in issuesAttr.subAttributes:
            attMap[i.itsName] = i 
            
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
    pass
