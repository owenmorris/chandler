__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from application.Application import app

from OSAF.document.model.Document import Document
from OSAF.document.model.SimpleContainers import *
from OSAF.document.model.SimpleControls import *

class TimeclockDocument:
    def __init__(self, view):
            self.view = view
            
    def ShowTimeclock(self, event):
        timeclockDocument = app.repository.find('//Document/TimeclockDocument')
        if timeclockDocument != None:
            timeclockDocument.delete()
        timeclockDocument = self.CreateTimeclockDocument()
        timeclockDocument.Render(self.view)
        self.view.GetContainingSizer().Layout()
        
    def CreateTimeclockDocument(self):
        """
          Creates the Timeclock document to be shown.
        """
        timeclockDocument = Document('TimeclockDocument')
        verticalSizer = BoxContainer('OuterSizer', timeclockDocument,
                                     orientation=wxVERTICAL)

        titleSizer = BoxContainer('TitleSizer', verticalSizer,
                                  orientation=wxHORIZONTAL,
                                  weight=0)
        title = Label('title', titleSizer, label='Timeclock',
                      weight=0, fontpoint=18, fontfamily=wxSWISS)
        
        description = Label('description', verticalSizer, 
                            label='This parcel is a demo showing how easy it is to add functionality to Chandler.',
                            weight=0, border=5, flag=wxALIGN_CENTRE|wxALL)
        
        buttonSizer = BoxContainer('ButtonSizer', verticalSizer,
                                   orientation=wxHORIZONTAL, weight=0,
                                   flag=wxALIGN_CENTRE|wxALL, border=5)
        startButton = Button('StartButton', buttonSizer, 
                             label='Start Clock', flag=wxALIGN_CENTRE|wxALL,
                             border=5, weight=0)
        stopButton = Button('StopButton', buttonSizer,
                             label='Stop Clock', flag=wxALIGN_CENTRE|wxALL,
                             border=5, weight=0)

        radiobox = RadioBox('CustomerBox', verticalSizer, label='Customer:',
                            dimensions=1, flag=wxALIGN_CENTER|wxALL, border=5,
                            selection=0, style=wxRA_SPECIFY_COLS,
                            choices=['Floss Recycling Incorporated', 
                                     'Northside Cowbell Foundry Corp.',
                                     'Cuneiform Designs, Ltd.'], weight=0)

        hoursSizer = BoxContainer('HoursSizer', verticalSizer, 
                                  orientation=wxHORIZONTAL, weight=0, 
                                  flag=wxALIGN_CENTRE|wxALL, border=5)
        billableHours = Button('BillableHours', hoursSizer,
                               label='See Billable Hours', weight=0,
                               flag=wxALIGN_CENTRE|wxALL, border=5)

        amountSizer = BoxContainer('AmountSizer', verticalSizer,
                                   orientation=wxHORIZONTAL, weight=0,
                                   flag=wxALIGN_CENTRE|wxALL, border=5)
        billableAmount = Button('BillableAmount', amountSizer,
                                label='See Billable Amount', weight=0,
                                flag=wxALIGN_CENTRE|wxALL, border=5)

        rateSizer = BoxContainer('RateSizer', verticalSizer, 
                                 orientation=wxHORIZONTAL, weight=0,
                                 flag=wxALIGN_CENTRE|wxALL, border=5)
        changeRate = Button('ChangeRate', rateSizer, label='Change Rate',
                            weight=0, flag=wxALIGN_CENTRE|wxALL, border=5)        
        changeRateText = Text('ChangeRateText', rateSizer, 
                              style=wxTE_PROCESS_ENTER)        
        units = Label('Units', rateSizer, label='dollars/hr', weight=0,
                      flag=wxALIGN_CENTRE|wxALL, border=5)
        
        return timeclockDocument
        
    