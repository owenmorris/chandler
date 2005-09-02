from DocumentTypes import RectType, ColorType, SizeType, PositionType

from Styles import CharacterStyle, ColorStyle, Style
from Block import Block as __Block

from Block import (
    RectangularChild, TrunkSubtree, BlockEvent, ChoiceEvent,
    KindParameterizedEvent, ModifyContentsEvent, EventList
)

from ContainerBlocks import (
    BoxContainer, FrameWindow, LayoutChooser, ScrolledContainer,
    SplitterWindow, TabbedContainer, ViewContainer
)

from Trunk import TrunkDelegate, TrunkParentBlock
from Views import View

from ControlBlocks import (
    AEBlock, Button, CheckBox, Choice, ComboBox, ContentItemDetail,
    ContextMenu, ContextMenuItem, EditText, HTML, ItemDetail, List, RadioBox,
    ReminderTimer, StaticText, StatusBar, Table, Timer, Tree, PresentationStyle
)

from MenusAndToolbars import (
    DynamicBlock, DynamicChild, DynamicContainer, Menu, MenuBar, MenuItem,
    RefCollectionDictionary, Toolbar, ToolbarItem
)

from ColumnHeaderBlocks import (ColumnHeader) 

from PimBlocks import (Sendability)

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

        BlockEvent.template('SendShareItem',
                            'FocusBubbleUp').install(parcel),

        # It's possible that Clear and Remove should be the same event,
        # contextually applied to either text or items. For now, I'm trying
        # them separately. --stearns
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

        BlockEvent.template('New', 'ActiveViewBubbleUp',
                            commitAfterDispatch=True).install(parcel),

        BlockEvent.template('Open', 'ActiveViewBubbleUp').install(parcel),

        BlockEvent.template('Preferences',
                            'ActiveViewBubbleUp').install(parcel),

        BlockEvent.template('SelectWeek',
                            'BroadcastEverywhere').install(parcel),
        
        BlockEvent.template('SelectedDateChanged',
                            'BroadcastEverywhere').install(parcel),
        
        BlockEvent.template('SelectItemBroadcast',
                            'BroadcastInsideMyEventBoundary',
                            methodName='onSelectItemEvent').install(parcel),
        
        BlockEvent.template('SelectItemBroadcastInsideActiveView',
                            'BroadcastInsideActiveViewEventBoundary',
                            methodName='onSelectItemEvent').install(parcel),
        BlockEvent.template('SetContents',
                            'BroadcastInsideMyEventBoundary').install(parcel),
        
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

    ColorStyle.update(parcel, "WhiteBackground",
        backgroundColor = ColorType(255,255,255,0)
    )

