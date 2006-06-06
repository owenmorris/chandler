from Styles import CharacterStyle, ColorStyle, Style
from Block import Block as __Block
from application import schema
import wx


from Block import (
    RectangularChild, BlockEvent, NewItemEvent, ChoiceEvent, ColorEvent,
    KindParameterizedEvent, AddToSidebarEvent, EventList, debugName,
    getProxiedItem, WithoutSynchronizeWidget, IgnoreSynchronizeWidget
)

from ContainerBlocks import (
    BoxContainer, FrameWindow, LayoutChooser, ScrolledContainer,
    SplitterWindow, TabbedContainer, ViewContainer
)

from BranchPoint import BranchPointDelegate, BranchPointBlock, BranchSubtree

from Views import View

from ControlBlocks import (
    AEBlock, Button, ContentItemDetail,
    ContextMenu, ContextMenuItem, EditText, HTML, ItemDetail,
    ReminderTimer, StaticText, StatusBar, Timer, Tree, PresentationStyle, Column
)

from Table import (
    Table, wxTable, GridCellAttributeEditor
)

from MenusAndToolbars import (
    DynamicBlock, DynamicChild, DynamicContainer, Menu, MenuBar, MenuItem,
    RefCollectionDictionary, Toolbar, ToolbarItem
)

from ColumnHeaderBlocks import (ColumnHeader) 

from PimBlocks import (FocusEventHandlers)

def installParcel(parcel, oldName=None):

    # Block Events instances.  Applicaiton specific events should not
    # be located here.  Instead put them in a View in your
    # application. Also don't put any references to application
    # specific parcels here.

    EventList.update(parcel, 'GlobalEvents',
                     eventsForNamedLookup=[
        BlockEvent.template('Undo', 'FocusBubbleUp').install(parcel),
        
        BlockEvent.template('Cut', 'FocusBubbleUp',
                            commitAfterDispatch=True).install(parcel),

        BlockEvent.template('SelectAll', 'FocusBubbleUp').install(parcel),

        BlockEvent.template('PrintPreview',
                            'ActiveViewBubbleUp').install(parcel),

        BlockEvent.template('Remove',
                            'FocusBubbleUp',
                            commitAfterDispatch=True).install(parcel),

        BlockEvent.template('Clear',
                            'FocusBubbleUp',
                            commitAfterDispatch=True).install(parcel),

        BlockEvent.template('Paste',
                            'FocusBubbleUp',
                            commitAfterDispatch=True).install(parcel),

        BlockEvent.template('Print',
                            'ActiveViewBubbleUp').install(parcel),

        BlockEvent.template('Copy', 'FocusBubbleUp',
                            commitAfterDispatch=True).install(parcel),

        BlockEvent.template('Redo', 'FocusBubbleUp').install(parcel),

        BlockEvent.template('Quit', 'ActiveViewBubbleUp').install(parcel),

        BlockEvent.template('About', 'ActiveViewBubbleUp').install(parcel),

        BlockEvent.template('Close', 'ActiveViewBubbleUp').install(parcel),

        BlockEvent.template('Open', 'ActiveViewBubbleUp').install(parcel),

        BlockEvent.template('Preferences',
                            'ActiveViewBubbleUp').install(parcel),

        BlockEvent.template('SelectItemsBroadcast',
                            'BroadcastInsideMyEventBoundary',
                            methodName='onSelectItemsEvent').install(parcel),
        
        BlockEvent.template('SetContents',
                            'BroadcastInsideMyEventBoundary').install(parcel),
        
        BlockEvent.template('Rename', 'FocusBubbleUp').install(parcel),

        BlockEvent.template('EnterPressed',
                            'BroadcastInsideMyEventBoundary').install(parcel),
    ])

    # A few specific styles

    CharacterStyle.update(parcel, "TextStyle", fontFamily="DefaultUIFont")

    CharacterStyle.update(parcel, "BigTextStyle",
        fontFamily="DefaultUIFont", fontSize = 15, fontStyle = "bold",
    )
    CharacterStyle.update(parcel, "LabelStyle", fontFamily="DefaultUIFont")

    CharacterStyle.update(parcel, "SummaryHeaderStyle",
        fontFamily="DefaultUIFont", fontStyle = "bold",
    )

    CharacterStyle.update(parcel, "SummaryRowStyle", fontFamily="DefaultUIFont")

    CharacterStyle.update(parcel, "SidebarRowStyle", fontFamily="DefaultUIFont", fontSize=12)
