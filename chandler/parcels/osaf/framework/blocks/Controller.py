
from Block import Block
from ContainerBlocks import *
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

    def on_chandler_GetTreeListData (self, notification):
        node = notification.data['node']
        data = node.GetData()
        if data:
            if data == 'root':
                for child in Globals.repository.getRoots():
                    node.AddChildNode (child, child.getItemName(), child.hasChildren())
            else:
                for child in data.iterChildren(load=False):
                    node.AddChildNode (child, child.getItemName(), child.hasChildren())
        else:
            node.AddRootNode ('root', '//', True)
