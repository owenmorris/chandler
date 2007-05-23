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


__all__ = [ 'getView', 'releaseView' ]

AVAILABLE = 0
IN_USE    = 1

views = []
name = "viewpool-%d"
highest = 0

def getView(repo):
    global views, highest

    for i, (view, status) in enumerate(views):
        if status == AVAILABLE:
            views[i] = (view, IN_USE)
            view.cancel( )
            view.refresh( )
            return view

    view = repo.createView(name=name%highest, pruneSize=500, notify=False)
    view.setBackgroundIndexed(True)
    views.append((view, IN_USE))
    highest += 1
    return view

def releaseView(rv):
    global views

    for i, (view, status) in enumerate(views):
        if rv is view:
            views[i] = (view, AVAILABLE)
