import tools.QAUITestAppLib as QAUITestAppLib
from i18n.tests import uw

#initialization
fileName = "TestDates.log"
logger = QAUITestAppLib.QALogger(fileName, "TestDates")

START_DATE = 0
START_TIME = 1
END_DATE   = 2
END_TIME   = 3
TIMEZONE   = 4

    # tests that need to be added:
    #     week to week transistions
    #     non-pacific time zones
    #     other locales

dateValues = { 'us': [  # year end transistion
                      ('12/31/04', '11:30 PM', '1/1/05',   '12:30 AM', 'US/Central'),
                        # leap year (feb has 29 days)
                      ('2/28/04',  '11:30 PM', '2/29/04',  '12:30 AM', 'US/Central'),
                        # leap year (feb has 29 days)
                      ('2/29/04',  '11:30 PM', '3/1/04',   '12:30 AM', 'US/Central'),
                        # Daylight savings time start
                      ('4/2/06',   '1:00 AM',  '4/2/06',   '3:00 AM',  'US/Central'),
                        # Daylight savings time end
                      ('10/29/06', '2:00 AM',  '10/29/06', '1:00 AM',  'US/Central'),
                     ],
             }

try:
    # creation
    event = QAUITestAppLib.UITestItem("Event", logger)

    for locale in dateValues:
        testItems = dateValues[locale]

        for test in testItems:
            s = uw('%s %s :: %s %s :: %s' % test)

            event.SetAttr(displayName=uw("Test"),
                          startDate=test[START_DATE],
                          startTime=test[START_TIME],
                          body=s,
                          timeZone=test[TIMEZONE]
                         )

            event.Check_DetailView({"displayName": uw("Test")),
                                    "startDate":   test[START_DATE],
                                    "endDate":     test[END_DATE],
                                    "startTime":   test[START_TIME],
                                    "endTime":     test[END_TIME],
                                    "body":        s,
                                   })

finally:
    #cleaning
    logger.Close()
