"""
Unit tests for persistent collections
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import RepositoryTestCase, os, unittest

from repository.schema.Attribute import Attribute

class PersistentCollectionsTest(RepositoryTestCase.RepositoryTestCase):
    """Test Persistent Collection"""
    
    # The big thing to be tested is persisting ordinary python collections and dicts
    # otherwise this functionality has already been tested in TestLiteralAttributes and
    # TestLiteralReferenceAttributes

    def _checkManagerAndEmployeesList(self, m, es):
        """Make sure a list of employees has the same manager"""
        for i in es:
            self.assertEquals(i.manager, m)
            self.assert_(m.hasValue('employees', i))

    def _checkManagerAndEmployeesDict(self, m, es):
        """Make sure a list of employees has the same manager"""
        for e,v in es.items():
            self.assertEquals(v.manager, m)
            self.assert_(m.hasValue('employees', v))

            
    def testPersistingPythonList(self):
        """Test making a regular Python list persistent"""
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

        emps = []
        empNames = ['employee1','employee2','employee3','employee4']
        for e in empNames:
            emps.append(employeeKind.newItem(e, self.rep))

        manager.employees = emps
        self._checkManagerAndEmployeesList(manager, emps)

        self._reopenRepository()
        
        manager = self.rep.find("//boss")
        emps = []
        for i in empNames:
            emps.append(self.rep.find("//%s" % i))
        self._checkManagerAndEmployeesList(manager, emps)
        
    
    def testPersistingPythonDict(self):
        """Test making a regular Python dict persistent"""
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

        manager = managerKind.newItem('boss', self.rep)
        
        emps = {}
        empNames = ['employee1','employee2','employee3','employee4']
        for e in empNames:
            emps[e] = employeeKind.newItem(e, self.rep)

        manager.employees = emps
#        print manager.employees
#        print emps['employee1']
#        print emps['employee1'].manager
#        for i in emps:
#            print emps[i]
#            print emps[i].manager
        self._checkManagerAndEmployeesDict(manager, emps)
        
        
        self._reopenRepository()
        manager = self.rep.find('//boss')
        emps = {}
        for e in empNames:
            emps[e] = self.rep.find('//%s' % e)
        self._checkManagerAndEmployeesDict(manager,emps)
        
                  
if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
