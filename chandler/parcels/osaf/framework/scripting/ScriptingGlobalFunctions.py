__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Provide Scripting Global Functions """
import wx
import logging
import osaf.framework.blocks.Block as Block
import application.Globals as Globals
from repository.item.Item import Item

_logger = logging.getLogger('CPIA Script')
_logger.setLevel(logging.INFO)

# Functions that return a named block
def FindNamedBlock(blockName):
    block = Block.Block.findBlockByName(blockName)
    if not block:
        _logger.warning("Can't find block named %s" % blockName)
    return block

def Sidebar():
    return FindNamedBlock("Sidebar")

def SummaryView():
    return FindNamedBlock("TableSummaryView")

def CalendarView():
    return FindNamedBlock("CalendarSummaryView")

def DetailView():
    return FindNamedBlock("DetailView")

def StartTime():
    # The Start time edit field of the Detail View
    return FindNamedBlock("EditCalendarStartTime")

def EndTime():
    # The End time edit field of the Detail View
    return FindNamedBlock("EditCalendarEndTime")

"""
Special functions, including wxWidgets-related operations

All attributes in this file get added to the builtin module
for script execution, except for ones that start with "_".
"""
def Focus(block):
    # Set the input focus to the given block
    try:
        widget = block.widget
    except AttributeError:
        _logger.warning("Can't set focus to block %s" % block)
    else:
        widget.SetFocus()

def SidebarSelect(itemOrName):
    """ Select the item in the Sidebar """
    # can pass in an item or a name
    if isinstance(itemOrName, Item):
        params = {'item':itemOrName}
    else:
        params = {'itemName':itemOrName}
    Globals.mainViewRoot.postEventByName ('RequestSelectSidebarItem', params)
    Focus(Sidebar())

def SummaryViewSelect(item):
    # Tell the ActiveView to select our item
    Globals.mainViewRoot.postEventByName ('SelectItemBroadcastInsideActiveView', {'item':item})
    Focus(SummaryView())

"""
TO BE DONE
* Type(<string>) function to take the string and tell wx
    to act like the user typed it in.
    (Could add modifier flags using optional parameters)
* Look at Select(item) method on Block, for SummaryView,
    Sidebar, etc.  I think Table.GotoItem() method or something
    like that might work.
* RunScript(<script> | <scriptNameString>) - run a script
* Click(<location>) should be possible.
"""
