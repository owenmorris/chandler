#   Copyright (c) 2003-2006 Open Source Applications Foundation
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
