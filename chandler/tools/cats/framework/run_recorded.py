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

import sys
import os
import logging
from application import Globals
from datetime import datetime

logger = logging.getLogger('recorded_test_framework')

recorded_scripts_dir = os.path.abspath(os.path.join(
                                                os.path.dirname(sys.modules[__name__].__file__),
                                                os.path.pardir, 
                                                'recorded_scripts'))

test_callables = {}
sys.path.insert(0, recorded_scripts_dir)
                                                
for filename in os.listdir(recorded_scripts_dir):
    if filename.endswith('.py') and not filename.startswith('.'):
        (filename, extension) = os.path.splitext (filename)
        test_module = __import__(filename)

        # Check for platform exclutions
        if (not hasattr(test_module, '_platform_exclutions_') or
                (sys.platform not in test_module._platform_exclutions_ and
                'all' not in test_module._platform_exclutions_)):
            test_callables[filename] = getattr(test_module, 'run')

sys.path.pop(0)

def run_test_by_name(name):
    logger.info('Starting Test:: %s' % name)
    if not test_callables.has_key(name):
        logger.error('Test dictionary does not have test named %s' % name)
        return False
    
    try:
        test_callables[name]()
        logger.info('Test %s has passed' % name)
    except AssertionError, e:
        logger.exception('Test "%s" has failed' % name)
        return False
    except Exception, e:
        logger.exception('Test "%s" has failed due to traceback' % name)
        return False

    return True

def execute_frame(option_value):
    logger.info(option_value)
    
    result = "PASSED"
    if option_value == 'all':
        testNames = test_callables.keys()
    else:
        testNames = [option_value]

    for name in testNames:
        if not run_test_by_name(name):
            result = "FAILED"

    print '#TINDERBOX# Testname = %s' % Globals.options.recordedTest 
    print '#TINDERBOX# Time elapsed = %s' % str (datetime.now() - Globals.test_dict['starttime'])
    print '#TINDERBOX# Status = %s' % result
