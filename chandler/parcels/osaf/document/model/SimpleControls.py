__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from Block import Block
from wxPython.wx import *
from wxPython.gizmos import *
from wxPython.html import *

class Button(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Button'

    def Render(self, parent, sizer):
        button = wxButton(parent, self.style['id'], 
                          self.style['label'], style=self.style['style'])
        self.AddToSizer(button, sizer)
        return button

    
class Choice(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Choice'

    def Render(self, parent, sizer):
        choice = wxChoice(parent, self.style['id'], choices=self.style['choices'], 
                          style=self.style['style'])
        self.AddToSizer(choice, sizer)
        return choice            

    
class HtmlWindow(Block):
    def __init__(self, name, parent=None, **_kwds):
        Block.__init__(self, name, parent, **_kwds)
        self.style['page'] = ''

    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Choice'
    
    def Render(self, parent, sizer):
        htmlWindow = wxHtmlWindow(parent, self.style['id'], 
                                  style=self.style['style'])
        htmlWindow.SetPage(self.style['page'])
        self.AddToSizer(htmlWindow, sizer)
        return htmlWindow
    
    
class Label(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Label'
    
    def Render(self, parent, sizer):
        label = wxStaticText(parent, self.style['id'], self.style['label'], 
                             style=self.style['style'])
        label.SetFont(wxFont(self.style['fontpoint'],
                             self.style['fontfamily'],
                             self.style['fontstyle'],
                             self.style['fontweight'],
                             self.style['fontunderline'],
                             self.style['fontname']))
        self.AddToSizer(label, sizer)
        return label
        

class List(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/List'

    def Render(self, parent, sizer):
        list = wxListCtrl(parent, self.style['id'], style=self.style['style'])
        self.AddToSizer(list, sizer)
        return list

    
class RadioBox(Block):
    def __init__(self, name, parent=None, selection=0, **_kwds):
        Block.__init__(self, name, parent, **_kwds)
        self.style['selection'] = selection
    
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/RadioBox'

    def Render(self, parent, sizer):
        radioBox = wxRadioBox(parent, self.style['id'], self.style['label'], 
                              choices=self.style['choices'], style=self.style['style'], 
                              majorDimension=self.style['dimensions'])
        self.AddToSizer(radioBox, sizer)
        radioBox.SetSelection(self.style['selection'])
        return radioBox

        
class RadioButton(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/RadioButton'

    def Render(self, parent, sizer):
        radioButton = wxRadioButton(parent, self.style['id'], self.style['label'], 
                                    style=self.style['style'])
        self.AddToSizer(radioButton, sizer)
        return radioButton

        
class ScrolledWindow(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/ScrolledWindow'

    def Render(self, parent, sizer):
        scrolledWindow = wxScrolledWindow(parent, self.style['id'], 
                                          style=self.style['style'])
        self.AddToSizer(scrolledWindow, sizer)
        return scrolledWindow

    
class SplitterWindow(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/SplitterWindow'
    
    def Render(self, parent, sizer):
        splitter = wxSplitterWindow(parent, self.style['id'],
                                    style=self.style['style'])
        childrenIterator = self.iterChildren()
        wxChildList = []
        for childItem in childrenIterator:
            wxChildList.append(childItem.Render(splitter, None))
        splitter.SplitHorizontally(wxChildList[0], wxChildList[1], 200)
        self.AddToSizer(splitter, sizer)
        return splitter
    

class Text(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Text'

    def Render(self, parent, sizer):
        text = wxTextCtrl(parent, self.style['id'], self.style['value'], 
                          style=self.style['style'])
        self.AddToSizer(text, sizer)
        return text
        

class ToggleButton(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/ToggleButton'

    def Render(self, parent, sizer):
        toggleButton = wxToggleButton(parent, self.style['id'], self.style['label'], 
                                      style=self.style['style'])
        self.AddToSizer(toggleButton, sizer)
        return toggleButton
  
        
class Tree(Block):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Tree'
    
    def Render(self, parent, sizer):
        tree = wxTreeCtrl(parent, self.style['id'], 
                          style=self.style['style'])
        self.AddToSizer(tree, sizer)
        return tree

class TreeList(Block):
    def __init__(self, name, parent=None, **_kwds):
        Block.__init__(self, name, parent, **_kwds)
        self.style['columns'] = []
        
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/TreeList'
    
    def Render(self, parent, sizer):
        treeList = wxTreeListCtrl(parent, self.style['id'], 
                          style=self.style['style'])
        for column in self.style['columns']:
            treeList.AddColumn(column)
        self.AddToSizer(treeList, sizer)
        return treeList


        