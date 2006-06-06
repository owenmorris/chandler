
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

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

        except ImportError:
            if self.missingClass is not None:
                return self.missingClass
            raise
