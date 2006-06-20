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


App_ns = app_ns()

from application import schema
scripting_ns = schema.ns('osaf.framework.scripting', App_ns.view)

newScript = Script(itsView=App_ns.view)
# if the Scripts collection is visible, select it
if scripting_ns.scriptsCollection in App_ns.sidebar.contents:
    App_ns.root.ApplicationBarAll()
    App_ns.sidebar.select(scripting_ns.scriptsCollection)
    App_ns.summary.postEventByName('SelectItemsBroadcast', {'items':[newScript]})
