#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

"""
Unit tests for reference attributes
"""

import os, unittest

from chandlerdb.util.RepositoryTestCase import RepositoryTestCase
from chandlerdb.item.Item import Item
from chandlerdb.schema.Attribute import Attribute


class ReferenceAttributesTest(RepositoryTestCase):
    """ Test Reference Attributes """

    def _createManagerAndEmployeeKinds(self, type):

        view = self.view

        kind = view.findPath('//Schema/Core/Kind')
        itemKind = view.findPath('//Schema/Core/Item')
        attrKind = itemKind.itsParent['Attribute']

        managerKind = kind.newItem('manager', view)
        employeesAttribute = Attribute('employees', managerKind, attrKind)
        employeesAttribute.cardinality = type
        employeesAttribute.otherName = 'manager'
        managerKind.addValue('attributes',
                             employeesAttribute, alias='employees')
        employeeKind = kind.newItem('employee', view)
        managerAttribute = Attribute('manager', employeeKind, attrKind)
        managerAttribute.otherName = 'employees'
        employeeKind.addValue('attributes', managerAttribute, alias='manager')

        return managerKind, employeeKind

    # support functions for testListReferenceAttributes and testDictReferenceAttributes
    def _findManagerAndEmployees(self, mPath, e1Path, e2Path, e3Path, e4Path):
        """Use find to retrieve our test data from the repository """
        view = self.view
        manager = view.findPath(mPath)
        emp1 = view.findPath(e1Path)
        emp2 = view.findPath(e2Path)
        emp3 = view.findPath(e3Path)
        emp4 = view.findPath(e4Path)
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
        view = self.view
        managerKind = view.findPath('//manager')
        employeesAttribute = managerKind.getAttribute('employees')
        self.assertEquals(employeesAttribute.cardinality, 'list')
        self.assertEquals(employeesAttribute.getAttributeValue('otherName'),
                          'manager')        
        employeeKind = view.findPath('//employee')
        managerAttribute = employeeKind.getAttribute('manager')
        self.assertEquals(managerAttribute.otherName,'employees')

        # add employees to manager
        manager = managerKind.newItem('boss', view)

        emp1 = employeeKind.newItem('employee1', view)
        emp2 = employeeKind.newItem('employee2', view)
        emp3 = employeeKind.newItem('employee3', view)
        emp4 = employeeKind.newItem('employee4', view)

        manager.setValue('employees', emp1)
        manager.addValue('employees', emp2)
        manager.addValue('employees', emp3)
        manager.addValue('employees', emp4)
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now write what we've done and read it back
        self._reopenRepository()
        view = self.view
        managerKind = view['manager']
        employeeKind = view['employee']
        (manager, [emp1, emp2, emp3, emp4]) = self._findManagerAndEmployees('//boss','//employee1','//employee2','//employee3','//employee4')
        self._checkManagerAndEmployees(manager, [ emp1, emp2, emp3, emp4 ])

        # now do it from the other end add manager to employees
        manager = managerKind.newItem('bossA', view)

        emp1 = employeeKind.newItem('employeeA1', view)
        emp1.manager = manager
        emp2 = employeeKind.newItem('employeeA2', view)
        emp2.manager = manager
        emp3 = employeeKind.newItem('employeeA3', view)
        emp3.manager = manager
        emp4 = employeeKind.newItem('employeeA4', view)
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
        view = self.view
        itemKind = view.findPath('//Schema/Core/Item')
        attrKind = view.findPath('//Schema/Core/Attribute')
        self.assert_(itemKind is not None)

        attr = Attribute('references', view.findPath('//Schema/Core'), attrKind,
                         cardinality='list', otherName='item')
        itemKind.attributes.append(attr, alias='references')
        
        attr_name = 'references'
        
        item = Item('item1', view, itemKind)
        attrKind = itemKind.itsParent['Attribute']

        # subattributes are created by assigning the "parent" attribute
        # to the superAttribute attribute of the "child" attribute
        testAttr = itemKind.getAttribute(attr_name)
        criticalSubAttr = Attribute('critical', testAttr, attrKind)
        criticalSubAttr.superAttribute = testAttr
        self.assert_(criticalSubAttr.superAttribute is testAttr)
        self.assert_(criticalSubAttr in testAttr.subAttributes)

        # now do it by assigning to the subAttributes list to ensure that
        # the bidirectional ref is getting updated.
        normalSubAttr = Attribute('normal', testAttr, attrKind)
        testAttr.subAttributes.append(normalSubAttr)
        self.assert_(normalSubAttr.superAttribute is testAttr)
        self.assert_(normalSubAttr in testAttr.subAttributes)
        
        # now do it by callin addValue on the Attribute item
        minorSubAttr = Attribute('minor', testAttr, attrKind)
        testAttr.addValue('subAttributes', minorSubAttr)
        self.assert_(minorSubAttr.superAttribute is testAttr)
        self.assert_(minorSubAttr in testAttr.subAttributes)

        # now write what we've done and read it back
        self._reopenRepository()
        view = self.view
        item = view.findPath('//item1')
        itemKind = item.itsKind
        testAttr = itemKind.getAttribute(attr_name)

        attMap = {}
        for i in testAttr.subAttributes:
            attMap[i.itsName] = i 
            
        criticalSubAttr = attMap['critical']
        normalSubAttr = attMap['normal']
        minorSubAttr = attMap['minor']
        self.assert_(criticalSubAttr.superAttribute is testAttr)
        self.assert_(criticalSubAttr in testAttr.subAttributes)
        self.assert_(normalSubAttr.superAttribute is testAttr)
        self.assert_(normalSubAttr in testAttr.subAttributes)
        self.assert_(minorSubAttr.superAttribute is testAttr)
        self.assert_(minorSubAttr in testAttr.subAttributes)
        
if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
    pass
