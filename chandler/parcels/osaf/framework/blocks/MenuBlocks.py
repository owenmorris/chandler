__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from Block import Block
import wx

class MenuEntry(Block):

    def rebuildMenus (self, startingAtBlock):
        """
          Rebuild the menus, starting with the any menus that
        are children of startingAtBlock, and proceeding up
        all the parents.
        """
        
        def buildMenuList (block, data):
            """
               buildMenuList collects all the data about the menus by
            scanning all the blocks and their parents looking for menu
            blocks, keeping track of the things in the dictionary named
            "data".
            
              Menu's are identified by their itemName rather than
            their UUIDs. This requires itemNames to be unique across all
            items and that nesting blocks be aware of the names of
            the menus in their parent blocks.
            """
            parent = block.parentBlock
            if (parent):
                buildMenuList (parent, data)
            """
              Initialize data if it's empty
            """
            if len (data) == 0:
                data['mainMenu'] = []
                data['nameToItemIndex'] = {}
                data['nameToMenuList'] = {}

            nameToItemIndex = data['nameToItemIndex']
            nameToMenuList = data['nameToMenuList']
            for child in block.childrenBlocks:
                if isinstance (child, MenuEntry):
                    """
                      Use menuLocation to look up the menu that
                    contains the item or menu
                    """
                    if child.menuLocation:
                        """
                          If you get an exception here, it's probably because
                        the name of menuLocation isn't the name of an existing
                        menu.
                        """
                        menu = nameToMenuList [child.menuLocation]
                    else:
                        menu = data['mainMenu']
                    
                    name = child.itsName
                    if child.operation == 'InsertBefore':
                        try:
                            index = menu.index (child.itemLocation)
                        except ValueError:
                            index = len (menu)
                        menu.insert (index, name)
                    elif child.operation == 'Replace':
                        menu[menu.index (child.itemLocation)] = name
                    elif child.operation == 'Delete':
                        """
                          If you get an exception here, it's probably because
                        you're trying to remove a menu item that doesn't exist.
                        """
                        menu.remove (child.itemLocation)
                    else:
                       assert (False)
                    
                    if child.operation != 'Delete':
                        # Shouldn't have items with the same name
                        assert not nameToItemIndex.has_key (name)  
                        nameToItemIndex[name] = child
                        if isinstance (child, Menu):
                            nameToMenuList[name] = []
            
        data = {}
        buildMenuList (startingAtBlock, data)
        
        frame = Globals.wxApplication.mainFrame
        if frame:
            menuBar = frame.GetMenuBar()
            if not menuBar:
                menuBar = wx.MenuBar()
                frame.SetMenuBar(menuBar)
            """
              The actual work of setting the menus is done by installMenu
            """
            self.installMenu (data['mainMenu'], menuBar, data)
    rebuildMenus = classmethod (rebuildMenus)


    def installMenu (cls, menuList, wxMenuObject, data):
        nameToItemIndex = data['nameToItemIndex']
        oldMenuList = cls.getMenuItems (wxMenuObject)

        for index in xrange (len (menuList)):
            menuItemName = menuList [index]
            menuItem = nameToItemIndex [menuItemName]
            try:
                oldItem = oldMenuList.pop(0)
            except IndexError:
                oldItem = None

            wxMenuItem = menuItem.renderMenuEntry (wxMenuObject, index, oldItem)
            if isinstance (menuItem, Menu):
                nameToMenuList = data['nameToMenuList']
                cls.installMenu (nameToMenuList[menuItemName], wxMenuItem, data)

            if wxMenuItem != oldItem:
                menuItem.setMenuItem (wxMenuObject, wxMenuItem, oldItem, index)

        for oldItem in oldMenuList:
            index += 1
            cls.deleteItem (wxMenuObject, index, oldItem)
    installMenu = classmethod (installMenu)

    """
      wxWindows doesn't implement convenient menthods for dealing
    with menus, so we'll write our own: getMenuItems, deleteItem
    getItemTitle, and setMenuItem
    """
    def getMenuItems (cls, wxMenuObject):
        """
          Returns a list of wxMenuItems in wxMenuObject, which can
        be either a menu or menubar
        """
        if isinstance (wxMenuObject, wx.MenuBar):
            menuList = []
            for index in xrange (wxMenuObject.GetMenuCount()):
                menuList.append (wxMenuObject.GetMenu (index))
        else:
            if isinstance (wxMenuObject, wx.MenuItem):
                wxMenuObject = wxMenuObject.GetSubMenu()
            assert isinstance (wxMenuObject, wx.Menu)
            menuList = wxMenuObject.GetMenuItems()

        return menuList
    getMenuItems = classmethod (getMenuItems)

    def deleteItem (cls, wxMenuObject, index, oldItem):
        """
          Deletes an item from a wxMenuObject, where wxMenuObject can
        be either a menu or menubar. Unfortunately, wxWindows requires
        that you pass the oldItem whenever wxMenuObject is a wx.Menu.
        """
        if isinstance (wxMenuObject, wx.Menu):
            wxMenuObject.DestroyItem (oldItem)
            pass
        else:
            assert isinstance (wxMenuObject, wx.MenuBar)
            oldMenu = wxMenuObject.Remove (index)
            oldMenu.Destroy()
    deleteItem = classmethod (deleteItem)
 
    def getItemTitle (cls, wxMenuObject, index, item):
        """
          Gets the title of the item at index in wxMenuObject, where
        wxMenuObject can be either a menu or menubar. Unfortunately,
        wxWindows requires that you pass the oldItem whenever
        wxMenuObject is a wx.Menu.
        """
        title = None
        if item:
            if isinstance (wxMenuObject, wx.Menu):
                id = item.GetId()
                title = wxMenuObject.GetLabel (id)
            else:
                assert isinstance (wxMenuObject, wx.MenuBar)
                title = wxMenuObject.GetLabelTop (index)
            return title
    getItemTitle = classmethod (getItemTitle)

    def setMenuItem (self, wxMenuObject, newItem, oldItem, index):
        """
          Sets an item in wxMenuObject, which can be either a menu or
        menubar with a new item. Unfortunately, wxWindows requires that
        you pass the oldItem whenever wxMenuObject is a wx.Menu and
        you're replacing the item.
        """
        if isinstance (wxMenuObject, wx.MenuBar):
            itemsInMenu = wxMenuObject.GetMenuCount()
            assert (index <= itemsInMenu)
            if index < itemsInMenu:
                oldMenu = wxMenuObject.Replace (index, newItem, self.title)
                assert oldMenu == oldItem
                oldMenu.Destroy()
            else:
                success = wxMenuObject.Append (newItem, self.title)
                assert success
        else:
            if isinstance (wxMenuObject, wx.MenuItem):
                wxMenuObject = wxMenuObject.GetSubMenu()
            assert isinstance (wxMenuObject, wx.Menu)

            itemsInMenu = wxMenuObject.GetMenuItemCount()
            assert (index <= itemsInMenu)
            if index < itemsInMenu:
                self.deleteItem (wxMenuObject, index, oldItem)
            if isinstance (newItem, wx.MenuItem):
                success = wxMenuObject.InsertItem (index, newItem)
                assert success
            else:
                wxMenuObject.InsertMenu (index, 0, self.title, newItem, self.helpString)


class MenuItem (MenuEntry):
    def renderMenuEntry(self, wxMenuObject, index, oldItem):
        if self.menuItemKind == "Separator":
            id = wx.ID_SEPARATOR
            kind = wx.ITEM_SEPARATOR
        else:
            """
              Menu items must have an event, otherwise they can't cause any action,
            nor can we use wxWindows api's to distinguish them from each other.
            """
            assert self.hasAttributeValue('event')
            id = Block.getWidgetID(self)
            if self.menuItemKind == "Normal":
                kind = wx.ITEM_NORMAL
            elif self.menuItemKind == "Check":
                kind = wx.ITEM_CHECK
            elif self.menuItemKind == "Radio":
                kind = wx.ITEM_RADIO
            else:
                assert (False)        
        if oldItem == None or oldItem.GetId() != id or oldItem.GetKind() != kind:
            title = self.title
            if len(self.accel) > 0:
                title = title + "\tCtrl+" + self.accel

            if isinstance (wxMenuObject, wx.Menu):
                newItem = wx.MenuItem (wxMenuObject, id, title, self.helpString, kind)
            else:
                assert isinstance (wxMenuObject, wx.MenuItem)
                submenu = wxMenuObject.GetSubMenu()
                assert submenu
                newItem = wx.MenuItem (None, id, title, self.helpString, kind, submenu)
            return newItem
        return oldItem


class Menu(MenuEntry):
    def renderMenuEntry(self, wxMenuObject, index, oldItem):
        title = self.getItemTitle (wxMenuObject, index, oldItem)
        if title != self.title:
            return wx.Menu()
        return oldItem

        
