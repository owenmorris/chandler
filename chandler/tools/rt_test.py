#!/usr/bin/env python
#   Copyright (c) 2007 Open Source Applications Foundation
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
Test rt.py

    No parameters given should generate the help output
    >>> import build_lib
    >>> build_lib.runCommand(['python', 'rt.py'])
    0

    Try and run non-existent test
    >>> build_lib.runCommand(['python', 'rt.py', '-t', 'TestFoo.py'])
    Unit test TestFoo.py not found
    0

    Try and specify an invalid mode
    >>> build_lib.runCommand(['python', 'rt.py', '-m', 'foo', '-u'])
    foo removed from mode list
    0

    Run unit tests with --dryrun
    >>> build_lib.runCommand(['python', 'rt.py', '-d', '-u'], timeout=300)   #doctest: +ELLIPSIS
    unittest: ...chandler/application/tests/TestAllParcels.py
    ...
    0

    Run functional tests with --dryrun
    >>> build_lib.runCommand(['python', 'rt.py', '-d', '-f'])   #doctest: +ELLIPSIS
    functest: ...tools/cats/Functional/FunctionalTestSuite.py
    0
"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()