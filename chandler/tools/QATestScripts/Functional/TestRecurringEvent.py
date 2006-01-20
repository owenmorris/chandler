import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "TestRecurringEvent.log"
logger = QAUITestAppLib.QALogger(fileName,"TestRecurringEvent")

try:
    # Daily Event Test

    # creation
    dailyEvent = QAUITestAppLib.UITestItem("Event", logger)

    # action
    dailyEvent.SetAttr(displayName="Daily Exercise",
                       startDate="01/01/2006", 
                       startTime="6:00 AM", 
                       location="Gym", 
                       status="FYI",
                       body="Resolution: exercise daily for optimal health",
                       timeZone="US/Central", 
                       recurrence="Daily", 
                       recurrenceEnd="03/01/2006")
    
    # verification
    dailyEvent.Check_DetailView({"displayName":"Daily Exercise",
                                 "startDate":"1/1/06",
                                 "endDate":"1/1/06",
                                 "startTime":"6:00 AM",
                                 "endTime":"7:00 AM",
                                 "location":"Gym",
                                 "status":"FYI",
                                 "body":"Resolution: exercise daily for optimal health",
                                 "timeZone":"US/Central",
                                 "recurrence":"Daily", 
                                 "recurrenceEnd":"3/1/06"})

    dailyEvent.Check_Object({"displayName":"Daily Exercise",
                             "startDate":"1/1/2006",
                             "endDate":"1/1/2006",
                             "startTime":"6:00AM",
                             "endTime":"7:00AM",
                             "location":"Gym",
                             "status":"FYI",
                             "body":"Resolution: exercise daily for optimal health",
                             "timeZone":"US/Central"})

    # Weekly Event Test
                            
    # creation
    weeklyEvent = QAUITestAppLib.UITestItem("Event", logger)

    # action
    weeklyEvent.SetAttr(displayName="Weekly call home",
                        startDate="01/07/2006",
                        startTime="5:00 PM",
                        location="Phone",
                        status="FYI",
                        body="Resolution: call home weekly for good family relations",
                        timeZone="US/Central",
                        recurrence="Weekly",
                        recurrenceEnd="03/25/2006")

    # verification
      
    weeklyEvent.Check_DetailView({"displayName":"Weekly call home",
                                  "startDate":"1/7/06",
                                  "endDate":"1/7/06",
                                  "startTime":"5:00 PM",
                                  "endTime":"6:00 PM",
                                  "location":"Phone",
                                  "status":"FYI",
                                  "body":"Resolution: call home weekly for good family relations",
                                  "timeZone":"US/Central",
                                  "recurrence":"Weekly",
                                  "recurrenceEnd":"3/25/06"})

    weeklyEvent.Check_Object({"displayName":"Weekly call home",
                              "startDate":"1/7/2006",
                              "endDate":"1/7/2006",
                              "startTime":"5:00 PM",
                              "endTime":"6:00 PM",
                              "location":"Phone",
                              "status":"FYI",
                              "body":"Resolution: call home weekly for good family relations",
                              "timeZone":"US/Central"})

finally:
    # cleaning
    logger.Close()
