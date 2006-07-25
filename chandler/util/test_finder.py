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

import os
from unittest import TestLoader, main

class ScanningLoader(TestLoader):

    def loadTestsFromModule(self, module):
        """
        Return a suite of all tests cases contained in the given module
        """

        tests = [TestLoader.loadTestsFromModule(self,module)]

        if hasattr(module, "additional_tests"):
            tests.append(module.additional_tests())

        if hasattr(module, '__path__'):
            for dir in module.__path__:
                for file in os.listdir(dir):
                    if file.endswith('.py') and file!='__init__.py':
                        if file.lower().startswith('test'):
                            submodule = module.__name__+'.'+file[:-3]
                        else:
                            continue
                    else:
                        subpkg = os.path.join(dir,file,'__init__.py')
                        if os.path.exists(subpkg):
                            submodule = module.__name__+'.'+file
                        else:
                            continue
                    tests.append(self.loadTestsFromName(submodule))

        if len(tests)>1:
            return self.suiteClass(tests)
        else:
            return tests[0] # don't create a nested suite for only one return
