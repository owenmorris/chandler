#!bin/env python

"""
    return the menu for the Contacts Package
"""

from wxPython.wx import *

class SampleMenu:
    def __init__(self):
        self.resource = wxXmlResource("components/sample/resources/menu.xrc")
        self.menu = self.resource.LoadMenu("SampleMenu")
                
    def GetMenu(self):
        return self.menu
