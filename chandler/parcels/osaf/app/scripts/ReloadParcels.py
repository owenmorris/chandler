# This is the StartupTest script, used to test Chandler at start up time.
App_ns = app_ns()

# workaround bug 4554 - do the reload in the All view, not the Calendar view
App_ns.root.ApplicationBarAll()
App_ns.root.ReloadParcels()
