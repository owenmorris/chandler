__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


"""
  ultra simple class to test actions invoking arbitrary python classes
"""
class testActionClass:
        
    def foo(self):
        print "the foo method of testActionClass has been invoked!"
        return 'foo result'
    
