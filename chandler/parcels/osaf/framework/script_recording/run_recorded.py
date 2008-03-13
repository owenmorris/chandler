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

import sys, wx, traceback
import os
import logging
from application import Globals
from datetime import datetime
from osaf.framework.blocks.Block import Block
from application.Application import Globals

logger = logging.getLogger('recorded_test_framework')

def recorded_scripts_dir():
    return os.path.abspath(os.path.join (Globals.chandlerDirectory,
                                         "tools/cats/recorded_scripts"))

last_format_exception = None

def _inSeconds(tDelta):
    """return a timedelta object as a float of seconds"""
    return (tDelta.days * 86400) + tDelta.seconds + (tDelta.microseconds * .000001)
    
def get_test_modules(observe_exclusions=True):
    test_modules = {}
    scripts_dir = recorded_scripts_dir()
    if os.path.isdir (scripts_dir):
        sys.path.insert(0, scripts_dir)                     
        for filename in os.listdir(scripts_dir):
            if filename.endswith('.py') and not filename.startswith('.'):
                (filename, extension) = os.path.splitext (filename)
                
                try:
                    test_module = __import__(filename)
                except:
                    logger.exception('Failed to import test module %s' % filename)
                else:
                    # Check for platform exclusions
                    if observe_exclusions is True:
                        if (not hasattr(test_module, '_platform_exclusions_') or
                                (sys.platform not in test_module._platform_exclusions_ and
                                'all' not in test_module._platform_exclusions_)):
                            test_modules[filename] = test_module
                    else:
                        test_modules[filename] = test_module
                    
        sys.path.pop(0)
    return test_modules

default_test_modules = None

def run_test_by_name(name, test_modules=None):
    global last_format_exception
    global default_test_modules
    
    if default_test_modules is None:
        default_test_modules = get_test_modules()
        
    if test_modules is None:
        test_modules  = get_test_modules()

    last_format_exception = ""
    logger.info('Starting Test:: %s' % name)

    if not test_modules.has_key(name):
        logger.info('Test dictionary does not have test named %s' % name)
        return True
    
    # Run any dependencies
    if hasattr(test_modules[name], '_depends_' ):
        import recorded_test_lib
        for dependency in [getattr(recorded_test_lib, dep) for dep in test_modules[name]._depends_ if (
                           hasattr(recorded_test_lib, dep) ) and (
                           dep not in recorded_test_lib.executed_dependencies ) ]:
            try:
                dependency()
                recorded_test_lib.executed_dependencies.append(dependency.__name__)
                logger.info('executed dependency %s' % dependency.__name__)

            except AssertionError, e:
                logger.exception('executing dependency "%s" has failed' % dependency.__name__)
                last_format_exception = traceback.format_exception(*sys.exc_info())
                return False

            except Exception, e:
                logger.exception('executing dependency "%s" has failed due to traceback' % dependency.__name__)
                last_format_exception = traceback.format_exception(*sys.exc_info())
                return False
    
    if Globals.options.catch == "never":
        test_modules[name].run()
    
    else:
        # Run the callable
        try:
            test_modules[name].run()
    
        except AssertionError, e:
            logger.exception('Test "%s" has failed' % name)
            last_format_exception = traceback.format_exception(*sys.exc_info())
            return False
        
        except Exception, e:
            logger.exception('Test "%s" has failed due to traceback' % name)
            last_format_exception = traceback.format_exception(*sys.exc_info())
            return False

    logger.info('Test %s has passed' % name)
    return True

def execute_frame(option_value):
    logger.info(option_value)
    
    result = "PASSED"
    if option_value == 'all':
        testNames = test_modules.keys()
    else:
        testNames = [option_value]

    for name in testNames:
        if not run_test_by_name(name):
            result = "FAILED"

    # Process the Quit message, which will check and cleanup the repository
    # and do the normal close down of Chandler. Wrap this work in an except
    # block so we can log failures
    try:
        Block.postEventByNameWithSender ("Quit", {})
    except Exception, e:
        logger.exception('Chandler "%s" has failed due to traceback' % name)
        result = "FAILED"
    finally:
        print '#TINDERBOX# Testname = %s' % Globals.options.recordedTest 
        print '#TINDERBOX# Time elapsed = %0.2f (seconds)' % _inSeconds((datetime.now() - Globals.test_dict['starttime']))
        print '#TINDERBOX# Status = %s' % result
        
        
        # Exit in a way that shouldn't cause any failures not to b  e logged.
        if result == "FAILED":
            sys.exit(1)
        else:
            sys.exit()
