
from Block import Block
import application.Globals as Globals
from wxPython.wx import *


class Controller(Block):

    def on_chandler_Quit (self, notification):
        Globals.wxApplication.OnQuit ()

    def on_chandler_Undo_UpdateUI (self, notification):
        notification.data ['Text'] = 'Undo Command\tCtrl+Z'

    def on_chandler_Cut_UpdateUI (self, notification):
        notification.data ['Enable'] = False

    def on_chandler_Copy_UpdateUI (self, notification):
        notification.data ['Enable'] = False

    def on_chandler_Paste_UpdateUI (self, notification):
        notification.data ['Enable'] = False

