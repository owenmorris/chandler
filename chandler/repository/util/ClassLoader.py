
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, logging

class ClassLoader(object):

    def loadClass(cls, name, module=None):

        if module is None:
            lastDot = name.rindex('.')
            module = name[:lastDot]
            name = name[lastDot+1:]

        try:
            m = __import__(module, {}, {}, name)
        except ImportError:
            raise
        except Exception, e:
            logging.getLogger('repository').exception('Importing class %s.%s failed',
                                                      module, name)
            raise ImportError, 'see log for details'
        
        try:
            cls = getattr(m, name)
            cls.__module__

            return cls

        except AttributeError:
            raise ImportError, "Module %s has no class %s" %(module, name)
        except Exception, e:
            logging.getLogger('repository').exception('Importing class %s.%s failed',
                                                      module, name)
            raise ImportError, 'see log for details'

    loadClass = classmethod(loadClass)
