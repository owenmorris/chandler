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


import sys, logging


class ClassLoader(object):

    def __init__(self, itemClass, missingClass=None):

        self.itemClass = itemClass
        self.missingClass = missingClass

    def getItemClass(self):

        return self.itemClass

    def loadClass(self, name, module=None):

        try:
            if module is None:
                try:
                    lastDot = name.rindex('.')
                except ValueError:
                    try:
                        return __builtins__[name]
                    except KeyError:
                        raise ImportError, "Class %s unknown" %(name)
                else:
                    module = name[:lastDot]
                    name = name[lastDot+1:]

            try:
                m = __import__(module, globals(), locals(), ['__name__'])
            except ImportError:
                raise
            except TypeError:
                raise
            except:
                logging.getLogger(__name__).exception('Importing class %s.%s failed', module, name)
                x, value, traceback = sys.exc_info()

                # yes, this is valid python,
                # a traceback can be raise's third arg
                raise ImportError, value, traceback

            try:
                return getattr(m, name)
            except AttributeError:
                raise ImportError, "Module %s has no class %s" %(module, name)

        except ImportError, e:
            logging.getLogger(__name__).exception('Importing class %s.%s failed', module, name)
            if self.missingClass is not None:
                return self.missingClass
            raise
