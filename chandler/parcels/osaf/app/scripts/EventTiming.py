App_ns = app_ns()
App_ns.root.timing.clear()
for i in range(0, 3):
    App_ns.root.NewCalendar()
newCalList = App_ns.root.timing['NewCalendar']
print newCalList
newCalListStrings = App_ns.root.timing.strings['NewCalendar']
print newCalListStrings