
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, logging

class ClassLoader(object):

    def loadClass(cls, name, module=None):

        if module is None:
            lastDot = name.rindex('.')
            module = name[:lastDot]
            name = name[lastDot+1:]

        try:
            m = __import__(module, globals(), locals(), name)
        except ImportError:
            raise
        except:
            logging.getLogger('repository').exception('Importing class %s.%s failed', module, name)
            # yes, this is valid python, a traceback can be the second argument
            raise ImportError, sys.exc_value, sys.exc_traceback

        try:
            return getattr(m, name)
        except AttributeError:
            raise ImportError, "Module %s has no class %s" %(module, name)

    loadClass = classmethod(loadClass)
