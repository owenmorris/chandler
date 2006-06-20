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

"""Application tests package

When adding application test modules to this package, please add their
name to the __all__ list, below.  Do not add non-test modules, or module
names outside this package.
"""

__all__ = [
    'TestAllParcels', 'TestAnonymous', 'TestAttributes', 'TestCircular', 
    'TestClasses', 'TestClouds', 'TestCollections', 'TestCopying', 
    'TestDependency','TestItems', 'TestKindAndItem', 'TestLocalAttrs', 
    'TestNamespaceErrors', 'TestParcelErrors', 'TestParcelLoader',
    'TestParcelPerf', 'TestSchemaAPI', 'TestStringTypes',
]

def suite():
    """Unit test suite; run by testing 'application.tests.suite'"""
    from run_tests import ScanningLoader
    from unittest import defaultTestLoader, TestSuite
    loader = ScanningLoader()
    return TestSuite(
        [loader.loadTestsFromName(__name__+'.'+test_name)
            for test_name in __all__]
    )

