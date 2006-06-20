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
