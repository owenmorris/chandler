__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import Block as Block
import logging
import wx
from repository.item.Item import Item
import os


class RefCollectionDictionary(Item):
    """
      Provides dictionary access to a reference collection attribute 
    L{RefList<repository.item.RefCollections.RefList>}.
    The attribute that contains the reference collection is determined
    through attribute indirection using the collectionSpecifier attribute.
    The "itsName" property of the items in the reference collection
    is used for the dictionary lookup by default.  You can override
    the name accessor if you want to use something other than
    itsName to key the items in the collection.
    """
    def __init__(self, *args, **kwds):
        super(RefCollectionDictionary, self).__init__(*args, **kwds)
        # ensure that the collectionSpecifier exists
        if not self.hasLocalAttributeValue(self.getCollectionSpecifier()):
            self.setAttributeValue(self.getCollectionSpecifier(), [])
        
    def itemNameAccessor(self, item):
        """
        Name accessor used for RefCollectionDictionary
        subclasses can override this method if they want to
        use something other than the itsName property to 
        determine item names.
        
        @param item: the item whose name we want.
        @type item: C{item}
        @return: a C{immutable} for the key into the collection
        """
        return item.itsName or item.itsUUID.str64()
    
    def getCollectionSpecifier(self):
        """
        determines which attribute to use for the
        collectionSpecifier.
        subclasses can override this method if they want to
        use something other than collectionSpecifier, 
        which is typlically set up to redirect to the actual
        attribute that contains the collection.
        @return: a C{String} for the name of the collection attribute
        """
        return 'collectionSpecifier' # should be a redirectTo attribute

    def _index(self, key):
        """
        returns a tuple with the item refered to by the key, and the collection
        @param key: the key used for lookup into the ref collection.
        @type key: C{immutable}, typically C{String} or C{int}
        @return: a C{Tuple} containing C{(item, collection)} or raises an exception if not found.
        """
        coll = self.getAttributeValue(self.getCollectionSpecifier())
        if isinstance (key, int):
            if key >= 0:
                i = coll.first ()
                next = coll.next
            else:
                i = coll.last ()
                next = coll.previous
                key = -key
            for index in xrange (key):
                i = next (i)
        else:
            i = coll.getByAlias(key)
        return (i, coll)
        
    def index(self, key):
        """
        returns the item refered to by the key
        @param key: the key used for lookup into the ref collection.
        @type key: C{immutable}, typically C{String}
        @return: C{item} if found, or C{None} if not found.
        """
        try:
            i, coll = self._index(key)
            return i
        except KeyError:
            return None
        
    def __iter__(self):
        """
        Returns an iterator to the collection attribute.
        """
        return iter(self.getAttributeValue(self.getCollectionSpecifier()))
 
    def __len__(self):
        """
        @return: C{int} length of the collection attribute.
        """
        # In case our collection doesn't exist return zero
        try:
            return len(self.getAttributeValue(self.getCollectionSpecifier()))
        except AttributeError:
            return 0
    
    def has_key(self, key):
        """
        @param key: the key used for lookup into the ref collection.
        @type key: C{immutable}, typically C{String}
        @return: C{True} if found, or {False} if not found.
        """
        return self.index(key) != None
                                      
    def __contains__(self, item):
        """
        @param item: an item to find in the ref collection.
        @type key: C{item}
        @return: C{True} if found, or {False} if not found.
        """
        coll = self.getAttributeValue(self.getCollectionSpecifier())
        return coll.get(item.itsUUID) != None
    
    def __getitem__(self, key):
        """
        return the item associated with the key from the ref collection attribute
        @param key: the key used for lookup into the ref collection.
        @type key: C{immutable}, typically C{String}
        @return: C{item} if found, or raises an exception.
        """
        return self._index(key)[0]
    
    def __setitem__(self, key, value):
        """
        replace the item associated with the key from the ref collection attribute.
        Note that the new item may have a different key, but it will be placed
        in the same position in the ref collection, and the keyed item will be removed.
        @param key: the key used for position lookup into the ref collection.
        @type key: C{immutable}, typically C{String}
        @param value: the C{item} to place into the ref collection.
        @type value: C{item}
        """
        itemIndex, coll = self._index(key) # find the keyed item
        self.insert(itemIndex, value) # insert before
        if itemIndex is not None:
            coll.remove(itemIndex) # remove keyed original
            
    def insert(self, index, item):
        """
        Insert item before index in our ref collection.
        @param index: the position used for insertion into the ref collection.
        @type index: C{item} that exists in the ref collection, or C{None} to append.
        @param item: the C{item} to insert before C{index} in the ref collection.
        @type item: C{item}
        """
        # 
        coll = self.getAttributeValue(self.getCollectionSpecifier())
        coll.append(item, alias=self.itemNameAccessor(item))
        if index is not None:
            prevItem = coll.previous(index)
            coll.placeItem(item, prevItem) # place after the previous item
            
    def __delitem__(self, key):
        """
        Delete the keyed item from our ref collection.
        @param key: the key used for item location in the ref collection.
            Throws an exception if there is no item associated with the key.
        @type key: C{immutable}, typically C{String}
        """
        itemIndex, coll = self._index(key)
        coll.remove(itemIndex)

    def __str__ (self):
        barList = []
        coll = self.getAttributeValue(self.getCollectionSpecifier())
        for entry in coll:
            barList.append (entry.itsName or entry.itsUUID.str64())
        return str (barList)

class DynamicBlock(Item):
    """
      Mixin class for any Dynamic Block, both DynamicContainers
    and DynamicChild blocks.
    You should mix this class into a Block
    """
    def isDynamicChild (self):
        return False

    def isDynamicContainer (self):
        return False

    def appendDynamicBlocks (self, blockList):
        """
          Uniquely insert all dynamic blocks recursively to blockList
        preserving the order of the items.
        Note that items need to be inserted at the beginning, because
        we are scanning the tree from the bottom up, and tend to find
        the dynamic additions first, and the static definitions last.
        We want the static definitions to come first because the dynamic
        additions override them.
        """
        try:
            isContainer = self.isDynamicContainer ()
        except AttributeError:
            pass
        else:
            try:
                i = blockList.index (self)
            except ValueError:
                blockList.insert (0, self)
            else:
                blockList[i:i+1] = (self,)
            if isContainer:
                for child in self.childrenBlocks:
                    child.appendDynamicBlocks (blockList)
    
    def buildDynamicList (self):
        """
          Build a list of dynamic blocks found starting at self,
        moving up through the static hierarchy, and tunnelling down inside
        all dynamic branches found.
        We need all Dynamic Containers, and all Dynamic Children
        that have an itemLocation specified.
        @Return: the list of all Dynamic Blocks.
        """
        blockList = []
        block = self
        while block is not None:
            for child in block.childrenBlocks:
                try:
                    child.appendDynamicBlocks (blockList)
                except AttributeError:
                    pass
            block = block.parentBlock
        return blockList

    def rebuildContainers(self, containers):
        """
          Scan for dynamic containers, registering them in the containers list.
        Returns the block list of all dynamic blocks found.
        @param containers: the containers dictionary.
        @type containers: C{dict} to put all DynamicContainer blocks into.
        @Return: the list of all Dynamic Blocks.
        """
        blockList = self.buildDynamicList ()
        for block in blockList:
            if block.isDynamicContainer ():
                # initialize dynamic children starting with the static hierarchy
                block.populateFromStaticChildren ()
                containers [block.blockName] = block
        return blockList
                                       
    def rebuildChildren(self, containers, blockList):
        """
          Scan for dynamic children, find their parent, and attach them
        appropriately to the parent.dynamicChildren attribute.
        @param containers: the containers dictionary.
        @type containers: C{dict} to put all DynamicContainer blocks into.
        @param blockList: the list of all Dynamic blocks to consider.
        @type blockList: C{list} of DynamicBlock objects.
        """
        for child in blockList:
            # pick up children
            if child.isDynamicChild ():
                """
                  Use location to look up the container that
                contains the entry or container
                
                  If you get an exception here, it's probably because
                the name of the location isn't the name of an existing
                bar.
                  Use 'MenuBar' for the Menu Bar.
                    """
                try:
                    locationName = child.location
                except AttributeError:
                    locationName = child.parentBlock.blockName
                bar = containers [locationName]
                
                if child.operation == 'InsertBefore':
                    # Shouldn't have items with the same name, unless they are the same
                    if __debug__:
                        if not child in bar:
                            if bar.has_key (child.blockName):
                                logging.warning ("%s already has a %s named %s" % (bar.blockName, child.blockName, child.blockName))
                    # find its position (or None) and insert there (or at the end)
                    i = bar.index (child.itemLocation)
                    bar.insert (i, child)
                elif child.operation == 'Replace':
                    bar[child.itemLocation] = child
                elif child.operation == 'Delete':
                    """
                      If you get an exception here, it's probably because
                    you're trying to remove a bar item that doesn't exist.
                    """
                    del bar[child.itemLocation]
                else:
                   assert (False)

    def synchronizeDynamicBlocks (self):
        """
           synchronizeDynamicBlocks rebuilds the dynamic
        container hierarchy based on the blocks it finds in
        a root section of the static block hierarchy and then
        calls synchronizeWidget on each container.  Dynamic
        associations between blocks are done by blockName, 
        which must be unique.  Upon exit all DynamicContainer
        blocks found will have references to all dynamicChildren
        found, and those blocks will have an inverse reference
        to their dynamicParent.

          The rebuild is done starting at the specified block,
        moving up to the parentBlock, repeating this process
        until reaching the root of the hierarchy.  If we find
        any dynamic block at any point in the traversal we 
        scan down through all of its children recursively
        as long as dynamic blocks are found.
        
          DynamicContainers and their dynamicChildren are 
        identified by their itemName rather than their UUIDs,
        to make it easy for third party parcels to add menus. 
        This requires all container names to be unique
        and all names of dynamicChildren to be unique within
        their container.  

        @param self: the starting block for the scan.
        @type self: C{DynamicBlock}
        """

        containers = {}
        """
          Rebuild the dynamic container hierarchy.
        First establish all containers, then insert their children
        so the block declarations can be order-independent.
        """
        allDynamic = self.rebuildContainers (containers)
        self.rebuildChildren (containers, allDynamic)

        """
          Now that the we have the new dynamic structure, 
        update the blocks that have changed and call synchronizeWidget on them
        so they know to redraw.
        """
        for bar in containers.values():
            """
            Can't call synchronizeWidget because IgnoreSynchronizeWidget
            is true because we're in Tab's synchronizeWidget.
            """
            try:
                barWidget = bar.widget
            except AttributeError:
                pass
            else:
                bar.widget.wxSynchronizeWidget()

        # Since menus have changed, we need to reissue UpdateUI events
        wx.GetApp().needsUpdateUI = True

class DynamicChild (DynamicBlock):
    # Abstract mixin class used to detect DynamicChild blocks
    def isDynamicChild (self):
        return True

class DynamicContainer(RefCollectionDictionary, DynamicBlock):
    """
      A block whose children are built dynamically, when the
    Active View changes.
    This list of children is in "dynamicChildren" and the
    back pointer is in "dynamicParent".
    """

    def itemNameAccessor(self, item):
        """
          Use blockName for the accessor
        """
        return item.blockName
    
    def isDynamicContainer (self):
        return True

    def populateFromStaticChildren (self):
        # copy our static children as a useful starting point
        self.dynamicChildren.clear ()
        for block in self.childrenBlocks:
            self[block.blockName] = block

    def ensureDynamicChildren (self):
        """
          Make sure we have a DynamicChildren hierarchy, since all my
        subclasses use that hierarchy when they synchronize.
        If there is no DynamicChildren built, then initialize it from
        the childrenBlocks hierarchy.
        """
        try:
            children = len (self.dynamicChildren)
        except AttributeError:
            children = 0
        if not children:
            self.populateFromStaticChildren ()

class wxMenuItem (wx.MenuItem):
    def __init__(self, style, *arguments, **keywords):
        # unpack the style arguments, wx expects them separately
        arguments = style + arguments
        super (wxMenuItem, self).__init__ (*arguments, **keywords)

    def __cmp__ (self, other):
        """
          Shouldn't be needed, but wxWidgets will return it's internal
        wx.MenuItem when you ask for a menu item, instead of the wxMenuItem
        subclass that we supply to wx.  So we use this compare to test if 
        the two instances are really the same thing.
        @@@DLD - remove when wx.MenuItem subclasses are returned by wx.
        """
        try:
            if self.this == other.this:
                return 0
            else:
                return -1
        except AttributeError:
            raise NotImplementedError

    def wxSynchronizeWidget(self):
        # placeholder in case Menu Items change
        pass
    
    def CalculateWXStyle(cls, block):
        parentWidget = block.dynamicParent.widget
        if block.menuItemKind == "Separator":
            id = wx.ID_SEPARATOR
            kind = wx.ITEM_SEPARATOR
            style = (parentWidget, id, "", "", kind, None)
        else:
            id = Block.Block.getWidgetID(block)
            if block.menuItemKind == "Normal":
                kind = wx.ITEM_NORMAL
            elif block.menuItemKind == "Check":
                kind = wx.ITEM_CHECK
            elif block.menuItemKind == "Radio":
                kind = wx.ITEM_RADIO
            else:
                assert (False)        
            title = block.title
            if len (block.accel) > 0:
                title = title + '\t' + block.accel
            
            """
              When inserting ourself into a MenuItem, we must actually
            insert ourself into the submenu of that MenuItem.
            """
            if isinstance (parentWidget, wxMenu):
                style = (parentWidget, id, title, block.helpString, kind, None)
            else:
                assert isinstance (parentWidget, wxMenuItem)
                submenu = block.GetSubMenu()
                assert submenu
                style = (None, id, title, block.helpString, kind, submenu)
        return style
    CalculateWXStyle = classmethod(CalculateWXStyle)
    
    def setMenuItem (self, newItem, oldItem, index):
        subMenu = self.GetSubMenu()
        assert isinstance (subMenu, wxMenu)
        subMenu.setMenuItem(newItem, oldItem, index)
        
    def getMenuItems(self):
        wxMenuObject = self.GetSubMenu()
        assert isinstance (wxMenuObject, wxMenu)
        return wxMenuObject.GetMenuItems()

class wxMenu(wx.Menu):
    def __init__(self, *arguments, **keywords):
        super (wxMenu, self).__init__ (*arguments, **keywords)

    def wxSynchronizeWidget(self):
        self.blockItem.synchronizeItems()

    def __del__(self):
        for child in self.blockItem.childrenBlocks:
            try:
                widget = child.widget
            except AttributeError:
                pass
            else:
                if isinstance (widget, wx.MenuItem):
                    Block.Block.wxOnDestroyWidget (widget)
        Block.Block.wxOnDestroyWidget (self)
            
    def __cmp__ (self, other):
        """
          CPIA and wxWidgets have different ideas about how submenus work.
        In CPIA a menu can appear in the menu bar, or inside another menu.
        In wxWidgets, only a MenuItem can appear in a Menu, and you have to
        get the "subMenu" out of the MenuItem to deal with it as a Menu.
        This method lets us compare a CPIA wxMenu widget with a wx.MenuItem
        and they will be the same if the wx.MenuItem has the right subMenu.
        """
        # self is a CPIA wxMenu.  "other" could be a wx.MenuItem
        try:
            # the menu is in the sub-menu of the item
            subMenu = other.GetSubMenu ()
        except AttributeError:
            pass # wasn't a wx.MenuItem
        else:
            # check if it actually had a submenu
            if subMenu is not None:
                other = subMenu # use the submenu for the compare
        if self is other:
            return 0 # they matched
        else:
            return -1

    """
      wxWindows doesn't implement convenient methods for dealing
    with menus, so we'll write our own: getMenuItems, removeItem
    getItemTitle, and setMenuItem
    """
    def getMenuItems (self):
        return self.GetMenuItems()
    
    def getItemTitle (self, index, item):
        id = item.GetId()
        title = self.GetLabel (id)
        return title
    
    def removeItem (self, index, oldItem):
        self.RemoveItem (oldItem)
            
    def setMenuItem (self, newItem, oldItem, index):
        # set the menu item, replacing an old one if specified
        # the widget stays attached to the block until the block is destroyed
        itemsInMenu = self.GetMenuItemCount()
        assert (index <= itemsInMenu)
        if oldItem is not None:
            assert index < itemsInMenu, "index out of range replacing menu item"
            self.removeItem (index, oldItem)
        if isinstance (newItem.widget, wxMenuItem):
            success = self.InsertItem (index, newItem.widget)
            assert success, "error inserting menu item"
            """
              Disable menus by default. If they have an event then they will
            be enabled by an UpdateUIEvent or our command dispatch in Application.py
            """
            self.Enable (newItem.widget.GetId(), False)
        else:
            self.InsertMenu (index, 0, newItem.title, newItem.widget, newItem.helpString)
        
class wxMenuBar (wx.MenuBar):
    def Destroy(self):
        """
          We need to override Destroy to remove the MenuBar from mainFrame.
        We don't need to call wxOnDestroyWidget since wxMenuBar is a subclass of
        wxWindow, which sends a EVT_WINDOW_DESTROY which ends up calling wxOnDestroyWidget
        for us.
          Overriding __del__ doesn't work here since calling SetMenuBar (None) when the
        menuBar is being destroyed causes the application to crash -- probably because
        wxWidgets tries to access the MenuBar when it's almost already deleted. Overriding
        Destroy catches the menuBar before it's deleted instead of just before it's disposed.
        """
        self.blockItem.getFrame().SetMenuBar(None)
        super (wxMenuBar, self).Destroy()

    def wxSynchronizeWidget(self):
        self.blockItem.synchronizeItems()

    """
      wxWindows doesn't implement convenient menthods for dealing
    with menus, so we'll write our own: getMenuItems, removeItem
    getItemTitle, and setMenuItem
    """
    def getMenuItems (self):
        menuList = []
        for index in xrange (self.GetMenuCount()):
            menuList.append (self.GetMenu (index))
        return menuList
        
    def getItemTitle (self, index, item):
        title = wxMenuObject.GetLabelTop (index)
        return title
    
    def removeItem (self, index, oldItem):
        oldMenu = self.Remove (index)
        
    def setMenuItem (self, newItem, oldItem, index):
        itemsInMenu = self.GetMenuCount()
        assert (index <= itemsInMenu)
        title = newItem.title
        # operating within the current list?
        if index < itemsInMenu:
            # check if the new item is already installed, and remove it first
            if newItem.widget in self.getMenuItems (): # invokes wxMenu.__cmp__
                self.removeItem (index, newItem.widget)
            # if there's an old item present, replace it, else just insert
            if oldItem is not None:
                oldMenu = self.Replace (index, newItem.widget, title)
                assert oldMenu is oldItem
            else:
                self.Insert (index, newItem.widget, title)
        else:
            # beyond list, add to the end
            success = self.Append (newItem.widget, title)
            assert success

class MenuItem (Block.Block, DynamicChild):
    def instantiateWidget (self):
        # We'll need a dynamicParent's widget in order to instantiate
        try:
            if isinstance(self.dynamicParent.widget, wxMenu):
                return wxMenuItem(style=wxMenuItem.CalculateWXStyle(self))
        except AttributeError:
            return None
        
class MenuBar (Block.Block, DynamicContainer):
    def instantiateWidget (self):
        self.ensureDynamicChildren ()
        widget = wxMenuBar()
        self.getFrame().SetMenuBar(widget)
        return widget


    def synchronizeItems(self):
        """
          Install the menus into supplied menu list, and submenus
        into their menu items.
        Used for both Menus and MenuBars.
        """
        menuList = self.widget.getMenuItems () # keep track of menus here
        
        index = 0 # cur menu item index
        # for each new menu
        for menuItem in self.dynamicChildren:
            # ensure that the menuItem has been instantiated
            if not hasattr (menuItem, "widget"):
                # @@@DLD - use framework block/widget linkage
                menuItem.widget = menuItem.instantiateWidget()
                menuItem.widget.blockItem = menuItem
                menuItem.widget.wxSynchronizeWidget()

            # get the current item installed in the menu, if any
            try:
                curItem = menuList.pop(0)
            except IndexError:
                curItem = None

            # current and new items match?
            if curItem is None or menuItem.widget != curItem: # invokes our __cmp__

                # is the new item already somewhere in our menu?
                if menuItem.widget in menuList: # invokes our __cmp__
                    # yes, rip out existing items till we get to our new item
                    while menuItem.widget != curItem:
                        self.widget.removeItem (index, curItem)
                        curItem = menuList.pop(0)
                        # until we get to the matching item
                else:
                    # no, we're inserting a new item
                    self.widget.setMenuItem (menuItem, None, index)
                    if curItem is not None:
                        menuList.insert (0, curItem) # put the cur item back, we didn't use it
            index += 1

        # remove any remaining items in the menu
        for oldItem in menuList:
            self.widget.removeItem (index, oldItem)
            index += 1

class Menu (MenuBar, DynamicChild):
    def instantiateWidget (self):
        self.ensureDynamicChildren ()
        return wxMenu()
    
"""  
Toolbar classes
"""

class wxToolbar (Block.ShownSynchronizer, wx.ToolBar):
    def __init__(self, *arguments, **keywords):
        super (wxToolbar, self).__init__ (*arguments, **keywords)
        # keep track of ToolbarItems so we can tell when/how they change in synchronize
        self.toolItemList = [] # non-persistent list
        self.toolItems = 0
        
    def wxSynchronizeWidget(self):
        super (wxToolbar, self).wxSynchronizeWidget()
        self.SetToolBitmapSize((self.blockItem.toolSize.width, self.blockItem.toolSize.height))
        self.SetToolSeparation(self.blockItem.separatorWidth)

        try:
            colorStyle = self.blockItem.colorStyle
        except AttributeError:
            pass
        else:
            self.SetBackgroundColour(colorStyle.backgroundColor.wxColor())
            self.SetForegroundColour(colorStyle.foregroundColor.wxColor())

        # first time synchronizing this bar?
        dynamicChildren = self.blockItem.dynamicChildren
        rebuild = False
        if self.toolItems != 0:
            # no, check if anything has changed in this toolbar
            if len(dynamicChildren) != len(self.toolItemList):
                rebuild = True
            else:
                i = 0
                for item in dynamicChildren:
                    if item is not self.toolItemList[i]:
                        rebuild = True
                        break
                    i += 1
            
            if rebuild:
                # For now, we just blow away the old toolbar, and build a new one
                for i in xrange(self.toolItems):
                    block = self.toolItemList[i]
                    block.onDestroyWidget () # notify the world about the tool's destruction
                    self.DeleteToolByPos(0)
                self.toolItemList = []
                self.toolItems = len (dynamicChildren)
                # shallow copy the children list
                for child in dynamicChildren:
                    if rebuild:
                        child.render ()
                    self.toolItemList.append (child)

        # draw the bar, and we're done.
        self.Realize()
        

class wxToolbarItem (wx.ToolBarToolBase):
    """
    Toolbar Tool Widget.

    ToolbarItems are a CPIA concept, that are roughly equivalent to the
    wx object ToolbarTool.  In CPIA, ToolbarItems are children of Toolbars,
    (both regular childrenBlocks and dynamicChildren).  But in wxWidgets,
    a ToolbarTool is not a child of the Toolbar, instead it's added to
    the Toolbar with a special method call (either DoAddTool or AddControl).
    Because of this, destroying the Toolbar won't automatically destroy
    the widgets associated with each ToolbarItem since they are not
    children of the Toolbar from the wx perspective.  Luckily, about the
    only time we destroy the Toolbar is when we call wxSynchronizeWidget
    on it, so we can handle it specially.  At that time we explicitly 
    call the onDestroy method on each ToolbarItem to unhook that
    block from its widget. 
    """
    def wxSynchronizeWidget(self):
        """
          Currently, we only synchronize radio buttons, eventually we
        need to synchronize other kinds, e.g. Text, Combo, and Choice types
        """
        block = self.blockItem
        if block.toolbarItemKind == "Radio":
            try:
                selected = block.selected
            except AttributeError:
                pass
            else:
                if selected:
                    self.GetToolBar().ToggleTool (self.GetId(), True)
        pass

    def IsShown (self):
        # Since wx.ToolbarTools are not real widgets, they don't support IsShown,
        #  so we'll provide a stub for CPIA.
        return True
    
    def OnSetTextEvent (self, event):
        """
          wxToolbarItems don't properly handle setting the text of buttons, on
        updateUIEvents, so we'll handle it here with the method OnSetTextEvent.
        """
        self.SetLabel (event.GetText())
        self.GetToolBar().Realize()

    def OnToolEvent (self,event):
        """
          Persist state of ToolbarItems. Currently limited to radio buttons,
        eventually we need to synchronize other kinds, e.g. Text, Combo, and
        Choice types
        """
        block = self.blockItem
        if block.toolbarItemKind == "Radio":
            children = [child for child in block.parentBlock.childrenBlocks]
            blockIndex = children.index (block)
            """
              Unselect all the items in the radio group before this toolbar item
            """
            index = blockIndex - 1
            while index >= 0 and children [index].toolbarItemKind == "Radio":
                children [index].selected = False
                index -= 1
            """
              Select this toolbar item
            """
            children [blockIndex].selected = True
            """
              Unselect all the items in the radio group after this toolbar item
            """
            index = blockIndex + 1
            while index < len (children) and children [index].toolbarItemKind == "Radio":
                children [index].selected = False
                index += 1
        event.Skip()


class Toolbar (Block.RectangularChild, DynamicContainer):
    def instantiateWidget (self):
        self.ensureDynamicChildren ()
        # @@@DLD - remove this workaround for previous wxWidgets issues
        heightGutter = 9
        if self.buttonsLabeled:
            heightGutter += 14
        toolbar = wxToolbar(self.parentBlock.widget, 
                         Block.Block.getWidgetID(self),
                         wx.DefaultPosition,
                         (-1, self.toolSize.height+heightGutter),
                         style=self.calculate_wxStyle())
        # set the tool bitmap size right away
        toolbar.SetToolBitmapSize((self.toolSize.width, self.toolSize.height))
        return toolbar
    
    def calculate_wxStyle (self):
        style = wx.TB_HORIZONTAL
        if self.buttons3D:
            style |= wx.TB_3DBUTTONS
        else:
            style |= wx.TB_FLAT
        if self.buttonsLabeled:
            style |= wx.TB_TEXT
        return style
    
            
class ToolbarItem (Block.Block, DynamicChild):
    """
      Button (or other control) that lives in a Toolbar.
    """
    def instantiateWidget (self):
        def getBitmaps (self):
            bitmap = wx.GetApp().GetImage (self.bitmap)
            try:
                disabledBitmapName = self.disabledBitmap
            except AttributeError:
                disabledBitmap = wx.NullBitmap
            else:
                disabledBitmap = wx.GetApp().GetImage (disabledBitmapName)
            return bitmap, disabledBitmap

        # can't instantiate ourself without a toolbar
        try:
            theToolbar = self.dynamicParent.widget
        except AttributeError:
            return None
        
        tool = None
        id = Block.Block.getWidgetID(self)
        self.toolID = id
        if (self.toolbarItemKind == 'Button' or
            self.toolbarItemKind == 'Radio'):

            bitmap, disabledBitmap = getBitmaps (self)
            if self.toggle:
                theKind = wx.ITEM_CHECK
            elif self.toolbarItemKind == 'Radio':
                theKind = wx.ITEM_RADIO
            else:
                theKind = wx.ITEM_NORMAL
            
            tool = theToolbar.DoAddTool (id,
                                        self.label,
                                        bitmap,
                                        disabledBitmap,
                                        kind = theKind,
                                        shortHelp=self.title,
                                        longHelp=self.helpString)
            tool.__class__ = wxToolbarItem
            theToolbar.Bind (wx.EVT_TOOL, tool.OnToolEvent, id=id)            
        elif self.toolbarItemKind == 'Separator':
            theToolbar.AddSeparator()
        elif self.toolbarItemKind == 'Check':
            theKind = wx.ITEM_CHECK
            bitmap, disabledBitmap = getBitmaps (self)
            tool = theToolbar.DoAddTool (id,
                                        self.label,
                                        bitmap,
                                        disabledBitmap,
                                        kind = theKind,
                                        shortHelp=self.title,
                                        longHelp=self.helpString)
            tool.SetName(self.title)
            theToolbar.AddControl (tool)
        elif self.toolbarItemKind == 'Text':
            tool = wx.TextCtrl (theToolbar, id, "", 
                               wx.DefaultPosition, 
                               wx.Size(300,-1), 
                               wx.TE_PROCESS_ENTER)
            tool.SetName(self.title)
            theToolbar.AddControl (tool)
            tool.Bind(wx.EVT_TEXT_ENTER, wx.GetApp().OnCommand, id=id)
        elif self.toolbarItemKind == 'Combo':
            proto = self.prototype
            choices = proto.choices
            tool = wx.ComboBox (theToolbar,
                            -1,
                            proto.selection, 
                            wx.DefaultPosition,
                            (proto.minimumSize.width, proto.minimumSize.height),
                            proto.choices)            
            theToolbar.AddControl (tool)
            tool.Bind(wx.EVT_COMBOBOX, wx.GetApp().OnCommand, id=id)
            tool.Bind(wx.EVT_TEXT, wx.GetApp().OnCommand, id=id)
        elif self.toolbarItemKind == 'Choice':
            proto = self.prototype
            choices = proto.choices
            tool = wx.Choice (theToolbar,
                            -1,
                            wx.DefaultPosition,
                            (proto.minimumSize.width, proto.minimumSize.height),
                            proto.choices)            
            theToolbar.AddControl (tool)
            tool.Bind(wx.EVT_CHOICE, wx.GetApp().OnCommand, id=id)
        elif __debug__:
            assert False, "unknown toolbarItemKind"
        
        if tool is not None and tool.__class__ != wxToolbarItem:
            # convert this object from a wx.ToolBarTool to a wxToolBarItem,
            # so we can call methods on that widget class.
            assert tool.__class__ is wx.ToolBarToolBase, "wx ToolBarTool class mismatch with ToolbarItem"
            tool.__class__ = wxToolbarItem
        return tool

