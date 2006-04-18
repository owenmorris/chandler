
__revision__  = "$Revision: 8137 $"
__date__      = "$Date: 2005-10-31 15:44:56 -0800 (Mon, 31 Oct 2005) $"
__copyright__ = "Copyright (c) 2003-2006 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys
from pdb import Pdb


class debugger(Pdb):

    def __init__(self, view):

        Pdb.__init__(self)
        self.view = view

    def do_done(self, arg):

        self.set_continue()

        view = self.view
        if view._debugOn:
            view.debugOn(view._debugOn)

        return 1


def set_trace(view):
    debugger(view).set_trace(sys._getframe().f_back)    
