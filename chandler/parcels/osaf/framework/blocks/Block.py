__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from repository.item.Item import Item
from chandlerdb.util.UUID import UUID
import wx
import logging


class Block(Item):
    def __init__(self, *arguments, **keywords):
        super (Block, self).__init__ (*arguments, **keywords)

    def Post (self, event, arguments):
        """
          Events that are posted by the block pass along the block
        that sent it.
        """
        try:
            try:
                stackedArguments = event.arguments
            except AttributeError:
                pass
            arguments ['sender'] = self
            event.arguments = arguments
            Globals.mainView.dispatchEvent (event)
        finally:
            try:
                event.arguments = stackedArguments
            except UnboundLocalError:
                delattr (event, 'arguments')

    def PostEventByName (self, eventName, args):
        assert self.eventNameToItemUUID.has_key (eventName), "Event name " + eventName + " not found"
        list = self.eventNameToItemUUID [eventName]
        self.Post (Globals.repository.find (list [0]), args)

    eventNameToItemUUID = {}           # A dictionary mapping event names to event UUIDS
    blockNameToItemUUID = {}           # A dictionary mapping rendered block names to block UUIDS

    def addToNameToItemUUIDDictionary (theClass, list, dictionary):
        for item in list:
            try:
                name = item.blockName
            except AttributeError:
                pass
            else:
                try:
                    list = dictionary [name]
                except KeyError:
                    dictionary [name] = [item.itsUUID, 1]
                else:
                    list [1] = list [1] + 1 #increment the reference count
    addToNameToItemUUIDDictionary = classmethod (addToNameToItemUUIDDictionary)

    def removeFromNameToItemUUIDDictionary (theClass, list, dictionary):
        for item in list:
            try:
                name = item.blockName
            except AttributeError:
                pass
            else:
                list = dictionary [name]
                if list [0] == item.itsUUID:
                    list [1] = list [1] - 1 #decrement the reference count
                    if list [1] == 0:
                        del dictionary [name]
    removeFromNameToItemUUIDDictionary = classmethod (removeFromNameToItemUUIDDictionary)

    def render (self):
        try:
            instantiateWidgetMethod = getattr (type (self), "instantiateWidget")
        except AttributeError:
            pass
        else:
            oldIgnoreSynchronizeWidget = Globals.wxApplication.ignoreSynchronizeWidget
            Globals.wxApplication.ignoreSynchronizeWidget = True
            try:
                widget = instantiateWidgetMethod (self)
            finally:
                Globals.wxApplication.ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget
            """
              Store a non persistent pointer to the widget in the block. Store a pointer to
            the block in the widget. Undo all this when the widget is destroyed.
            """

            if widget:
                Globals.wxApplication.needsUpdateUI = True
                assert self.itsView.isRefCounted(), "respoitory must be opened with refcounted=True"
                self.widget = widget
                widget.blockItem = self
                """
                  After the blocks are wired up, call OnInit if it exists.
                """
                try:
                    method = getattr (type (widget), "OnInit")
                except AttributeError:
                    pass
                else:
                    method (widget)
                """
                  For those blocks with contents, we need to subscribe to notice changes
                to items in the contents.
                """
                try:
                    contents = self.contents
                except AttributeError:
                    pass
                else:
                    try:
                        subscribeMethod = getattr (type (contents), "subscribe")
                    except AttributeError:
                        pass
                    else:
                        subscribeMethod (contents, self, "onCollectionChanged")
                """
                  Add events to name lookup dictionary.
                """
                try:
                    eventsForNamedDispatch = self.eventsForNamedDispatch
                except AttributeError:
                    pass
                else:
                    self.addToNameToItemUUIDDictionary (eventsForNamedDispatch,
                                                        self.eventNameToItemUUID)
                self.addToNameToItemUUIDDictionary ([self],
                                                    self.blockNameToItemUUID)

                try:
                    method = getattr (type (self.widget), 'Freeze')
                except AttributeError:
                    pass
                else:
                    method (self.widget)

                for child in self.childrenBlocks:
                    child.render()

                """
                  After the blocks are wired up give the window a chance
                to synchronize itself to any persistent state.
                """
                oldIgnoreSynchronizeWidget = Globals.wxApplication.ignoreSynchronizeWidget
                Globals.wxApplication.ignoreSynchronizeWidget = False
                try:
                    self.synchronizeWidget()
                finally:
                    Globals.wxApplication.ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget

                try:
                    method = getattr (type (self.widget), 'Thaw')
                except AttributeError:
                    pass
                else:
                    method (self.widget)

    def unRender (self):
        for child in self.childrenBlocks:
            child.unRender()
        if hasattr (self, 'widget') and not isinstance (self.widget, wx.ToolBarToolBase):
            try:
                member = getattr (type(self.widget), 'Destroy')
            except AttributeError:
                pass
            else:
                wx.CallAfter (member, self.widget)


    def onCollectionChanged (self, action):
        """
          When our item collection has changed, we need to synchronize
        """
        self.synchronizeWidget()

    IdToUUID = []               # A list mapping Ids to UUIDS
    UUIDtoIds = {}              # A dictionary mapping UUIDS to Ids

    MINIMUM_WX_ID = 2500
    MAXIMUM_WX_ID = 4999

    def onDestroyWidget (self):
        """
          Called just before a widget is destroyed. It is the opposite of
        instantiateWidget.
        """
        try:
            contents = self.contents
        except AttributeError:
            pass
        else:
            try:
                unsubscribe = getattr (type (contents), "unsubscribe")
            except AttributeError:
                pass
            else:
                unsubscribe (contents, self)
        try:
            eventsForNamedDispatch = self.widget.eventsForNamedDispatch
        except AttributeError:
            pass
        else:
            self.removeFromNameToItemUUIDDictionary (eventsForNamedDispatch,
                                                     self.eventNameToItemUUID)
        self.removeFromNameToItemUUIDDictionary ([self],
                                                 self.blockNameToItemUUID)

        delattr (self, 'widget')
        assert self.itsView.isRefCounted(), "respoitory must be opened with refcounted=True"
            
        Globals.wxApplication.needsUpdateUI = True

    def widgetIDToBlock (theClass, wxID):
        """
          Given a wxWindows Id, returns the corresponding Chandler block
        """
        return Globals.repository.find (theClass.IdToUUID [wxID - theClass.MINIMUM_WX_ID])
 
    widgetIDToBlock = classmethod (widgetIDToBlock)

    def getWidgetID (theClass, object):
        """
          wxWindows needs a integer for a id. Commands between
        wxID_LOWEST and wxID_HIGHEST are reserved. wxPython doesn't export
        wxID_LOWEST and wxID_HIGHEST, which are 4999 and 5999 respectively.
        Passing -1 for an ID will allocate a new ID starting with 0. So
        I will use the range starting at 2500 for our events.
          Use IdToUUID to lookup the Id for a event's UUID. Use UUIDtoIds to
        lookup the UUID of a block that corresponds to an event id -- DJA
        """
        UUID = object.itsUUID
        try:
            id = Block.UUIDtoIds [UUID]
        except KeyError:
            length = len (Block.IdToUUID)
            Block.IdToUUID.append (UUID)
            id = length + Block.MINIMUM_WX_ID
            assert (id <= Block.MAXIMUM_WX_ID)
            assert not Block.UUIDtoIds.has_key (UUID)
            Block.UUIDtoIds [UUID] = id
        return id
    getWidgetID = classmethod (getWidgetID)

    def getFocusBlock (theClass):
        focusWindow = wx.Window_FindFocus()
        while (focusWindow):
            try:
                return focusWindow.blockItem
            except AttributeError:
                focusWindow = focusWindow.GetParent()
        return Globals.mainView
    getFocusBlock = classmethod (getFocusBlock)

    def onShowHideEvent(self, event):
        self.isShown = not self.isShown
        self.synchronizeWidget()
        self.parentBlock.synchronizeWidget()

    def onShowHideEventUpdateUI(self, event):
        event.arguments['Check'] = self.isShown

    def onModifyContentsEvent(self, event):
        operation = event.operation

        # 'collection' is an item collection that we want our new view
        # to contain
        collection = event.arguments.get('collection', None)

        # we'll put the copies in //userdata
        userdata = Globals.repository.findPath('//userdata')

        for item in event.items:
            if event.copyItems:
                copies = { } # This will contain all the copied items
                item = item.copy(parent=userdata, cloudAlias='default',
                 copies=copies)

                # Return the newly created view back to the caller:
                event.arguments ['view'] = item

                if collection is not None:
                    untitledItemCollection = item.contents
                    
                    for copy in untitledItemCollection.contentsOwner:
                        copy.contents = collection

            if operation == 'toggle':
                try:
                    index = self.contents.index (item)
                except ValueError:
                    operation = 'add'
                else:
                    operation = 'remove'
            method = getattr (type(self.contents), operation)
            method (self.contents, item)

    def synchronizeWidget (self):
        """
          synchronizeWidget's job is to make the wxWidget match the state of
        the data persisted in the block. There's a tricky problem that occurs: Often
        we add a handler to the wxWidget of a block to, for example, get called
        when the user changes the selection, which we use to update the block's selection
        and post a selection item block event. It turns out that while we are in
        synchronizeWidget, changes to the wxWidget cause these handlers to be
        called, and in this case we don't want to post an event. So we wrap calls
        to synchronizeWidget and set a flag indicating that we're inside
        synchronizeWidget so the handlers can tell when not to post selection
        changed events. We use this flag in other similar situations, for example,
        during shutdown to ignore events caused by the framework tearing down wxWidgets.
        """
        try:
            method = getattr (type (self.widget), 'wxSynchronizeWidget')
        except AttributeError:
            pass
        else:
            if not Globals.wxApplication.ignoreSynchronizeWidget:
                oldIgnoreSynchronizeWidget = Globals.wxApplication.ignoreSynchronizeWidget
                Globals.wxApplication.ignoreSynchronizeWidget = True
                try:
                    method (self.widget)
                finally:
                    Globals.wxApplication.ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget

class ShownSynchronizer:
    """
    A mixin that handles isShown-ness: Make sure my visibility matches my block's.
    """
    def wxSynchronizeWidget(self):
        if self.blockItem.isShown != self.IsShown():
            self.Show (self.blockItem.isShown)
    
class wxRectangularChild (ShownSynchronizer, wx.Panel):
    def __init__(self, *arguments, **keywords):
        super (wxRectangularChild, self).__init__ (*arguments, **keywords)

    def CalculateWXBorder(self, block):
        border = 0
        spacerRequired = False
        for edge in (block.border.top, block.border.left, block.border.bottom, block.border.right):
            if edge != 0:
                if border == 0:
                    border = edge
                elif border != edge:
                    spacerRequired = False
                    break
        """
          wxWindows sizers only allow borders with the same width, or no width, however
        blocks allow borders of different sizes for each of the 4 edges, so we need to
        simulate this by adding spacers. I'm postponing this case for Jed to finish, and
        until then an assert will catch this case. DJA
        """
        assert not spacerRequired
        
        return int (border)
    CalculateWXBorder = classmethod(CalculateWXBorder)

    def CalculateWXFlag (theClass, block):
        if block.alignmentEnum == 'grow':
            flag = wx.GROW
        elif block.alignmentEnum == 'growConstrainAspectRatio':
            flag = wx.SHAPED
        elif block.alignmentEnum == 'alignCenter':
            flag = wx.ALIGN_CENTER
        elif block.alignmentEnum == 'alignTopCenter':
            flag = wx.ALIGN_TOP
        elif block.alignmentEnum == 'alignMiddleLeft':
            flag = wx.ALIGN_LEFT
        elif block.alignmentEnum == 'alignBottomCenter':
            flag = wx.ALIGN_BOTTOM
        elif block.alignmentEnum == 'alignMiddleRight':
            flag = wx.ALIGN_RIGHT
        elif block.alignmentEnum == 'alignTopLeft':
            flag = wx.ALIGN_TOP | wx.ALIGN_LEFT
        elif block.alignmentEnum == 'alignTopRight':
            flag = wx.ALIGN_TOP | wx.ALIGN_RIGHT
        elif block.alignmentEnum == 'alignBottomLeft':
            flag = wx.ALIGN_BOTTOM | wx.ALIGN_LEFT
        elif block.alignmentEnum == 'alignBottomRight':
            flag = wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT

        # @@@ Temporary solution to allow for borders on a single side
        numBordersSpecified = 0
        if block.border.top != 0:
            flag |= wx.TOP
            numBordersSpecified += 1
        if block.border.left != 0:
            flag |= wx.LEFT
            numBordersSpecified += 1
        if block.border.bottom != 0:
            flag |= wx.BOTTOM
            numBordersSpecified += 1
        if block.border.right != 0:
            flag |= wx.RIGHT
            numBordersSpecified += 1
        if numBordersSpecified > 1:
            flag |= wx.ALL

        return flag
    CalculateWXFlag = classmethod(CalculateWXFlag)    
    

class RectangularChild (Block):
    def DisplayContextMenu(self, position, data):
        try:
            self.contextMenu
        except:
            return
        else:
            self.contextMenu.displayContextMenu(self.widget, position, data)
                
        
class BlockEvent(Item):

    def includePolicyMethod(self, items, references, cloudAlias):
        """ Method for handling an endpoint's byMethod includePolicy """

        # Determine if we are a global event
        events = Globals.repository.findPath("//parcels/osaf/framework/blocks/Events")
        if self.itsParent is events:
            # Yes, global: don't copy me
            references[self.itsUUID] = self
            return []

        # No, not global: copy me
        items[self.itsUUID] = self
        return [self]

    
class DetailBlock(Block):
    def instantiateWidget (self):
        return wxRectangularChild (self.parentBlock.widget)

    def SetChildBlock (self):
        newView = self.detailViewCache.GetViewForItem (self.contents)
        children = iter (self.childrenBlocks)
        try:
            oldView = children.next()
        except StopIteration:
            oldView = None
        if not newView is oldView:
            self.childrenBlocks = []

            if not oldView is None:
                oldView.unRender()

            if not newView is None:
                self.childrenBlocks.append (newView)
                """
                  It's surprising the amount of work necessary to create an event --
                  all because it's an Item
                """
                parent = Globals.repository.findPath ('//userdata')
                kind = Globals.repository.findPath('//parcels/osaf/framework/blocks/BlockEvent')
                event = BlockEvent (None, parent, kind)
                event.arguments = {'item':self.contents}
                newView.onSelectItemEvent (event)
                event.delete()

                newView.render()

                sizer = wx.BoxSizer (wx.HORIZONTAL)
                self.widget.SetSizer (sizer)

                sizer.Add (newView.widget,
                           newView.stretchFactor, 
                           wxRectangularChild.CalculateWXFlag (newView), 
                           wxRectangularChild.CalculateWXBorder (newView))
                self.widget.Layout()

    def onSelectItemEvent (self, event):
        self.contents = event.arguments['item']
        self.SetChildBlock()

class DetailViewCache (Item):
    def GetViewForItem (self, item):
        view = None
        if not item is None:
            kindUUID = item.itsUUID
            try:
                viewUUID = self.kindUUIDToViewUUID [kindUUID]
            except KeyError:
                kindString = str (item.itsKind.itsName)
                try:
                    name = {"MailMessage":"EmailRootTemplate",
                            "CalendarEvent":"CalendarRootTemplate"} [kindString]
                except KeyError:
                    pass
                else:
                    template = Globals.repository.findPath ("//parcels/osaf/framework/blocks/detail/" + name)
                    view = template.copy (parent = Globals.repository.findPath ("//userdata"),
                                          cloudAlias="default")
                    self.kindUUIDToViewUUID [kindUUID] = view.itsUUID
            else:
                view = Globals.repository.findUUID (viewUUID)
        return view
