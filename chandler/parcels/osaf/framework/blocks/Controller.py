
from Block import Block
import application.Globals as Globals
from wxPython.wx import *


class Controller(Block):

    def onQuit (self, event):
        Globals.wxApplication.OnQuit ()

