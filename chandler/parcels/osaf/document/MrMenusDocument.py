__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application.Application import app

from OSAF.document.model.Document import Document
from OSAF.document.model.SimpleContainers import *
from OSAF.document.model.SimpleControls import *

class MrMenusDocument:
    def __init__(self, view):
            self.view = view
            
    def ShowMrMenus(self, event):
        mrmenusDocument = app.repository.find('//Document/MrMenusDocument')
        if mrmenusDocument != None:
            mrmenusDocument.delete()
        mrmenusDocument = self.CreateMrMenusDocument()
        mrmenusDocument.Render(self.view)        
        self.view.GetContainingSizer().Layout()
            
    def CreateMrMenusDocument(self):
        """
          Creates the MrMenus document to be shown.
        """
        mrmenusDocument = Document('MrMenusDocument')
        radiobox = RadioBox('RadioBox', mrmenusDocument)
        radiobox.style['label'] = 'Please choose'
        radiobox.style['dimensions'] = 1
        radiobox.style['choices'] = ['Lunch', 'Dinner']
        radiobox.style['weight'] = 0
        radiobox.style['flag'] = wxALIGN_CENTER|wxALL
        radiobox.style['border'] = 25
        
        return mrmenusDocument
    
    