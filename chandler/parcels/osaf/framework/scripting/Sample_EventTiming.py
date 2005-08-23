EventTiming.clear()
for i in range(0, 3):
    NewCalendar()
newCalList = EventTiming['NewCalendar']
print newCalList
newCalListStrings = EventTiming.timingStrings()['NewCalendar']
print newCalListStrings 