
from Block import Block
import application.Globals as Globals
from wxPython.wx import *


class Controller(Block):

    def on_chandler_Quit (self, event):
        Globals.wxApplication.OnQuit ()

    def on_chandler_Quit_UpdateUI (self, event):
        pass

