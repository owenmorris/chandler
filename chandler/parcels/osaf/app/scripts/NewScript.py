App_ns = app_ns()
newScript = Script(view=App_ns.view)
# if the Scripts collection is visible, select it
if App_ns.scriptsCollection in App_ns.sidebar.contents:
    App_ns.root.ApplicationBarAll()
    App_ns.sidebar.select(App_ns.scriptsCollection)
    #App_ns.summary.select(newScript)
    App_ns.summary.postEventByName('SelectItemsBroadcastInsideActiveView', {'items':[newScript]})
