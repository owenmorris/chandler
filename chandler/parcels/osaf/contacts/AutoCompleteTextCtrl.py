#!bin/env python

"""
AutoCompleteTextCtrl is a subclass of TextCtrl that features auto-completion
from a passed in list of strings.  When a new string is entered, it's added
to the list
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002, 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *

class AutoCompleteTextCtrl(wxTextCtrl):
    def __init__(self, parent, wxID, text, choiceList, multipleMode, style=0):
        self.list = choiceList
        self.style = style
        self.multipleMode = multipleMode      
        wxTextCtrl.__init__(self, parent, wxID, text, style=style)

    def AddToList(self, newChoice):
        if self.list != None:
            self.list.append(newChoice)

    # at first, we just return the first matching one.  Soon, the arrow
    # keys will cycle through the possibilities, and we'll put up a list
    # if there's more than one choice
    # Note: don't make this case-sensitive, since case is
    # important to the semantics and we want to use it to
    # distinguish
    def LookUpText(self, textSoFar):
        if self.list == None:
            return None
                
        targetText = textSoFar
        for choice in self.list:
            if choice.startswith(targetText):
                return choice

        return None
                
    def AutoComplete(self, keycode):         
        selection = self.GetSelection()
 
        if keycode < 256:
            keyString = chr(keycode)
            self.Replace(selection[0], selection[1], keyString)
            self.SetInsertionPoint(selection[0] + 1)
        else:
            return
        
        # FIXME: for now, we don't do any completion in multiple mode; we'll implement for real soon
        if self.multipleMode:
            return

        textSoFar = self.GetValue()
        matchingText = self.LookUpText(textSoFar)
                
        if matchingText != None:
            self.SetValue(matchingText)
            # select the part that the user didn't type
            self.SetSelection(len(textSoFar), -1)
