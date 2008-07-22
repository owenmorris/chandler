#   Copyright (c) 2003-2008 Open Source Applications Foundation
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

from tools.cats.framework.runTests import run_tests
from tools.cats.Functional import tests
import application.Globals as Globals
import os

functional_dir = os.path.join(Globals.chandlerDirectory,"tools/cats/Functional")

teststring = ''.join(['%s:%s,' % (test, klass) for test, klass in tests.tests_to_run])[:-1]

run_tests(teststring)
