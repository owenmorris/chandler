__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import RepositoryTestCase, os, unittest

from repository.schema.Attribute import Attribute

class AttributeTestCase(RepositoryTestCase.RepositoryTestCase):
    """
    Base class for testing all kinds of attributes
    
    Provide kinds for list or dict multi-valued reference attributes

    """
    
    def _createManagerAndEmployeeKinds(self, type):
        kind = self._find('//Schema/Core/Kind')
        itemKind = self._find('//Schema/Core/Item')
        attrKind = itemKind.itsParent['Attribute']

        managerKind = kind.newItem('manager', self.rep)
        employeesAttribute = Attribute('employees',managerKind, attrKind)
        employeesAttribute.cardinality = type
        employeesAttribute.otherName = 'manager'
        managerKind.addValue('attributes',
                             employeesAttribute,alias='employees')
        employeeKind = kind.newItem('employee', self.rep)
        managerAttribute = Attribute('manager',employeeKind, attrKind)
        managerAttribute.otherName = 'employees'
        employeeKind.addValue('attributes',
                              managerAttribute,alias='manager')
        return (managerKind, employeeKind)
