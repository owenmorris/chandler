__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.gizmos import *

class RepositoryTreeCtrl(wxRemotelyScrolledTreeCtrl):
    def __init__(self, parent, id, style):
        wxRemotelyScrolledTreeCtrl.__init__(self, parent, id, style=style)