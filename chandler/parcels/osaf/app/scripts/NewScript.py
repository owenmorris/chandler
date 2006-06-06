App_ns = app_ns()

from application import schema
scripting_ns = schema.ns('osaf.framework.scripting', App_ns.view)

newScript = Script(itsView=App_ns.view)
# if the Scripts collection is visible, select it
if scripting_ns.scriptsCollection in App_ns.sidebar.contents:
    App_ns.root.ApplicationBarAll()
    App_ns.sidebar.select(scripting_ns.scriptsCollection)
    App_ns.summary.postEventByName('SelectItemsBroadcast', {'items':[newScript]})
