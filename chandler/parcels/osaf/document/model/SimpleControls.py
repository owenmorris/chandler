__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from Block import Block
from wxPython.wx import *


class Button(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Button'

    def Render(self, parent, sizer):
        button = wxButton(parent, self.style['id'], 
                          self.style['label'], style=self.style['style'])
        sizer.Add(button, self.style['weight'], self.style['flag'], 
                  self.style['border'])

        
class Choice(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Choice'

    def Render(self, parent, sizer):
        choice = wxChoice(parent, self.style['id'], choices=self.style['choices'], 
                          style=self.style['style'])
        sizer.Add(choice, self.style['weight'], self.style['flag'], self.style['border'])
    
        
class Label(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Label'
    
    def Render(self, parent, sizer):
        label = wxStaticText(parent, self.style['id'], self.style['label'], 
                             style=self.style['style'])
        sizer.Add(label, self.style['weight'], self.style['flag'], self.style['border'])
    

class List(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/List'

    def Render(self, parent, sizer):
        list = wxListCtrl(parent, self.style['id'], style=self.style['style'])
        sizer.Add(list, self.style['weight'], self.style['flag'], self.style['border'])

    

class RadioBox(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/RadioBox'

    def Render(self, parent, sizer):
        radioBox = wxRadioBox(parent, self.style['id'], self.style['label'], 
                              choices=self.style['choices'], style=self.style['style'], 
                              majorDimension=self.style['dimensions'])
        sizer.Add(radioBox, self.style['weight'], self.style['flag'], self.style['border'])

        
class RadioButton(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/RadioButton'

    def Render(self, parent, sizer):
        radioButton = wxRadioButton(parent, self.style['id'], self.style['label'], 
                                    style=self.style['style'])
        sizer.Add(radioButton, self.style['weight'], self.style['flag'], self.style['border'])

        
class ScrolledWindow(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/ScrolledWindow'

    def Render(self, parent, sizer):
        scrolledWindow = wxScrolledWindow(parent, self.style['id'], 
                                          style=self.style['style'])
        sizer.Add(scrolledWindow, self.style['weight'], self.style['flag'], 
                  self.style['border'])
    
        
class Text(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Text'

    def Render(self, parent, sizer):
        text = wxTextCtrl(parent, self.style['id'], self.style['value'], 
                          style=self.style['style'])
        sizer.Add(text, self.style['weight'], self.style['flag'], self.style['border'])
        

class ToggleButton(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/ToggleButton'

    def Render(self, parent, sizer):
        toggleButton = wxToggleButton(parent, self.style['id'], self.style['label'], 
                                      style=self.style['style'])
        sizer.Add(toggleButton, self.style['weight'], self.style['flag'], 
                  self.style['border'])
  
        
class Tree(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Tree'
    
    def Render(self, parent, sizer):
        tree = wxTreeCtrl(parent, self.style['id'], 
                          style=self.style['style'])
        sizer.Add(tree, self.style['weight'], self.style['flag'], 
                  self.style['border'])


        