"""
Unit tests for persistent collections
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import AttributeTestCase, os, unittest

from repository.schema.Attribute import Attribute
from repository.util.Path import Path

class PersistentCollectionsTest(AttributeTestCase.AttributeTestCase):
    """Test Persistent Collection"""
    
    # The big thing to be tested is persisting ordinary python collections and dicts
    # otherwise this functionality has already been tested in TestLiteralAttributes and
    # TestLiteralReferenceAttributes

    def _checkManagerAndEmployeesList(self, m, es):
        """Make sure a list of employees has the same manager"""
        for i in es:
            self.assert_(i.manager is m)
            self.assert_(m.hasValue('employees', i))

    def _checkManagerAndEmployeesDict(self, m, es):
        """Make sure a list of employees has the same manager"""
        for k,v in es.items():
            self.assert_(v.manager is m)
            self.assert_(m.hasValue('employees', v))

            
    def testPersistingPythonList(self):
        """Test making a regular Python list persistent"""
        (managerKind, employeeKind) = self._createManagerAndEmployeeKinds('list')

        manager = managerKind.newItem('boss', self.rep)

        emps = []
        empNames = ['employee1','employee2','employee3','employee4']
        for e in empNames:
            emps.append(employeeKind.newItem(e, self.rep))

        manager.employees = emps
        self._checkManagerAndEmployeesList(manager, emps)

        self._reopenRepository()
        
        manager = self._find("//boss")
        emps = []
        for i in empNames:
            emps.append(self._find(Path('//', i)))
        self._checkManagerAndEmployeesList(manager, emps)
        
    
    def testPersistingPythonDictByAssignment(self):
        """Test making a regular Python dict persistent by using assignment"""
        (managerKind, employeeKind) = self._createManagerAndEmployeeKinds('dict')

        manager = managerKind.newItem('boss', self.rep)
        
        emps = {}
        empNames = ['employee1','employee2','employee3','employee4']
        for e in empNames:
            emp = employeeKind.newItem(e, self.rep)
            emps[str(emp.getUUID())] = emp

        manager.employees = emps
        self._checkManagerAndEmployeesDict(manager, emps)
        
        self._reopenRepository()
        manager = self._find('//boss')
        emps = {}
        for e in empNames:
            emp = self._find(Path('//', e))
            emps[str(emp.getUUID())] = emp
        self._checkManagerAndEmployeesDict(manager,emps)

    def testPersistingPythonDictByUpdate(self):
        """Test making a regular Python dict persistent by using dict update method"""
        (managerKind, employeeKind) = self._createManagerAndEmployeeKinds('dict')

        manager = managerKind.newItem('boss', self.rep)
        
        emps = {}
        empNames = ['employee1','employee2','employee3','employee4']
        for e in empNames:
            emp = employeeKind.newItem(e, self.rep)
            emps[str(emp.getUUID())] = emp

        for k, v in emps.items():
            print k,v
        manager.employees = []
        manager.employees.update(emps)
        for k, v in manager.employees.items():
            print k,v
        self._checkManagerAndEmployeesDict(manager, emps)
        
        self._reopenRepository()
        manager = self._find('//boss')
        emps = {}
        for e in empNames:
            emp = self._find((Path('//', e)))
            emps[str(emp.getUUID())] = emp
        self._checkManagerAndEmployeesDict(manager,emps)
       
                  
if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
     unittest.main()
