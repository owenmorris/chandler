__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from wxPython.wx import *
from Action import Action

"""
The  DialogAction class is a subclass of Action that displays a dialog using text derived from
a template and the passed in data object
"""
class DialogAction(Action):

    # run this action synchronously with wxWindows
    def UseWxThread(self):
        return True

    def _SubstituteAttributes(self, template, dataDict):
        """
          this string substitution utility loops for each attribute in the data dictionary,
          substituting it in the template with it's value
        """
        result = template.replace("\\n", '\n')
        for attribute in dataDict.keys():
            value = str(dataDict[attribute])
            pattern = '[' + str(attribute) + ']'
            result = result.replace(pattern, value)
            
        return result
    
    def Execute(self, agent, notification):
        """
           Use wxWindows to display a dialog, with text derived from a template specified by the action,
           and data from the data parameter.   The data parameter is a dictionary associating values with keys
        """
      
        template = self.actionValue
        message = self._SubstituteAttributes(template, notification.GetData())
        
        if self.NeedsConfirmation():
            confirmDialog = wxMessageDialog(Globals.wxMainFrame, message, _("Confirm Action"), wxYES_NO | wxICON_QUESTION)
                        
            result = confirmDialog.ShowModal()
            confirmDialog.Destroy()
            # FIXME: need to execute sub-action when the result is yes
        else:
            wxMessageBox(message)

        return True
    
