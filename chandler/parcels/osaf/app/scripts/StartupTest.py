# This is the StartupTest script, used to test Chandler at start up time.
App_ns = app_ns()
App_ns.root.ReloadParcels()
App_ns.root.Quit()