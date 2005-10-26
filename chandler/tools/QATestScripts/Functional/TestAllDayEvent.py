import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "TestAllDayEvent.log"
logger = QAUITestAppLib.QALogger(fileName,"TestAllDayEvent")

try:
    # creation
    event = QAUITestAppLib.UITestItem("Event", logger)

    # action
    event.SetAllDay(True)
    
    # verification
    event.Check_DetailView({"allDay":True})
    event.Check_Object({"allDay":True})

finally:
    # cleaning
    logger.Close()
