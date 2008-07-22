#   Copyright (c) 2003-2008 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import wx
import wx.grid
from i18n import ChandlerMessageFactory as _
import datetime
import bisect

#import application.Globals as Globals
from osaf.pim.calendar.TimeZone import TimeZoneInfo, olsonizeTzinfo
import PyICU

def pickTimeZone(view, changeDefaultTZ=False):
    dlg = TimeZoneChooser(view)
    ret = dlg.ShowModal()
    if ret == wx.ID_OK:
        table = dlg.grid.table
        wellKnowns = table.info.wellKnownIDs

        def getInsertIndex(name):
            insertIndex = 0
            offset = getOffset(view.tzinfo.getInstance(name))
            for n in wellKnowns:
                test_offset = getOffset(view.tzinfo.getInstance(n))
                if offset < test_offset:
                    break
                insertIndex += 1

            return insertIndex

        newTZ = None
        newTZname = None
        rows = dlg.grid.GetSelectedRows()
        if len(rows) > 0:
            name = table.GetValue(rows[0], colData['name']['display'])
            # the separator row is empty, so if that row is selected, it's
            # equivalent to having nothing selected
            if name != '':
                newTZ = view.tzinfo.getInstance(name)
                newTZname = name
                if name not in wellKnowns:
                    wellKnowns.insert(getInsertIndex(name), name)
                if changeDefaultTZ and newTZ != table.info.default:
                    table.info.default = newTZ


        # pick a new default TZ if the default should be removed, because
        # attempting to remove the default from wellKnowns doesn't work
        if (newTZname is None and changeDefaultTZ and 
            table.info.default.tzid in table.changed):
            newdefault = None
            for tzid in wellKnowns:
                if tzid not in table.changed:
                    newdefault = tzid
                    break
            if newdefault is not None:
                table.info.default = view.tzinfo.getInstance(newdefault)
            else:
                avoidRemoving = table.info.default.tzid

        # if this dialog isn't changing the default timezone, don't allow
        # the current default to be removed from the well-known list
        avoidRemoving = table.info.default.tzid if not changeDefaultTZ else None
                
        for name, valChanged in table.changed.iteritems():
            if valChanged and name != newTZname:
                if name in wellKnowns:
                    if name != avoidRemoving:
                        wellKnowns.remove(name)
                else:
                    wellKnowns.insert(getInsertIndex(name), name)

        dlg.Destroy()
        return newTZ
    
    else:
        dlg.Destroy()
        return None



# We define _() here so that the wellKnownIDs
# strings below are picked up for translation by
# pygettext.py.

factory = _
from i18n import NoTranslationMessageFactory
_ = NoTranslationMessageFactory

TIMEZONE_SHORT_LIST = [_(u'Pacific/Honolulu'),
                       _(u'America/Anchorage'),
                       _(u'America/Los_Angeles'),
                       _(u'America/Denver'),
                       _(u'America/Chicago'),
                       _(u'America/New_York'),
                       _(u'World/Floating'),
                       _(u'Europe/London'),
                       _(u'Europe/Paris'),
                       _(u'Asia/Shanghai'),
                       _(u'Asia/Calcutta'),
                       _(u'Australia/Sydney')]

_ = factory

# data about each named column
colData = {
            # L10N: A header for a column that displays Timezone names
            'name'    : { 'display' : 0, 'sort' : 1, 'header' : _(u'Name'),
                          'wxType' : wx.grid.GRID_VALUE_STRING },
            # L10N: A header for a column that displays the Timezone
            #       offset from GMT
            'offset'  : { 'display' : 1, 'sort' : 0, 'header' : _(u'Offset'),
                          'wxType' : wx.grid.GRID_VALUE_STRING },
            # L10N: A header for a column that displays a checkbox
            #       indicating whether or not the user wants Chandler to
            #       make this Timezone available for creating Events.
            'checked' : { 'display' : 2, 'sort' : 2, 'header' : _(u'Shown'),
                          'wxType' : wx.grid.GRID_VALUE_BOOL }}

displayColToNameMap = dict( (colData[key]['display'], key) for key in colData )

class TimeZoneChooser(wx.Dialog):
    """
    Display a dialog with a table containing the union of TIMEZONE_SHORT_LIST
    and TimeZoneInfo.wellKnownIDs, plus optionally all PyICU timezones, with
    check boxes to choose which timezones should be considered well known (and 
    thus displayed).
    
    """
    def __init__(self, view):
        self.view = view
        self.changed = {}

        title = _(u"Use Time Zones")
        wx.Dialog.__init__(self, id=-1, name=u'TimeZoneChooser',
                           parent=None,
                           style=wx.DIALOG_MODAL | wx.DEFAULT_DIALOG_STYLE,
                           title=title)
        
        self.grid = CustTableGrid(self, view)
        
        self.viewAll = wx.CheckBox(self, -1, _(u"&View all time zones"))
        self.Bind(wx.EVT_CHECKBOX, self.ToggleTable, self.viewAll)
        
        buttonSizer = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)

        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        bottomSizer.Add(self.viewAll, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        bottomSizer.Add(buttonSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        
        self.box = box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.grid, 0, wx.EXPAND | wx.ALL, 5)
        box.Add(bottomSizer)
        self.SetSizer(box)

        box.Fit(self)

        self.Layout()
        self.CenterOnScreen()
        
    def ToggleTable(self, event):
        """Show or hide the long list of timezones."""
        self.grid.table.setRows(event.IsChecked())


class TimezoneTable(wx.grid.PyGridTableBase):
    def __init__(self, view, grid):
        wx.grid.PyGridTableBase.__init__(self)
        self.view = view
        self.grid = grid
        self.info = TimeZoneInfo.get(self.view)
        self.changed = {}
        self.unexpandedSize = -1
        self.setRows()

    def GetNumberCols(self):
        return len(colData)
    
    def GetNumberRows(self):
        return len(self.data)
    
    def GetValue(self, row, col):
        if row == self.unexpandedSize:
            #empty buffer row
            return ''

        colName = displayColToNameMap[col]
        sortedColumn = colData[colName]['sort']
        value = self.data[row][sortedColumn]
        
        if colName == 'checked':
            nameColumn  = colData['name']['sort']
            name = self.data[row][nameColumn]
            # ^ is XOR, note that int(True) == 1
            return value ^ self.changed.get(name, 0)
        elif colName == 'offset':
            delta = datetime.timedelta(hours=abs(value))
            data = {}
            data['hours']   =  delta.seconds / 3600
            data['minutes'] = (delta.seconds % 3600) / 60
            if value < 0:
                return " -%(hours)02d:%(minutes)02d" % data
            else:
                return "  %(hours)02d:%(minutes)02d" % data

        else:
            return value

    def Toggle(self, row):
        if row == self.unexpandedSize:
            return # ignore the buffer row
        nameColumn  = colData['name']['sort']
        name = self.data[row][nameColumn]
        self.changed[name] = not self.changed.get(name, False)

    def GetColLabelValue(self, col):
        return colData[displayColToNameMap[col]]['header']

    def GetTypeName(self, row, col):
        return colData[displayColToNameMap[col]]['wxType']

    def setRows(self, expanded = False):
        """Create self.data, rows with columns in sort order.
        
        Reordering to sort order allows bisect.insort to do binary search
        sorted insertion for us.
        
        If expanded is set, all column

        """
        if not hasattr(self, 'data'):
            rows = []
            for name in self.info.wellKnownIDs:
                offset = getOffset(self.view.tzinfo.getInstance(name))
                bisect.insort(rows, [offset, name, 1])
            for name in TIMEZONE_SHORT_LIST:
                if name not in self.info.wellKnownIDs:
                    offset = getOffset(self.view.tzinfo.getInstance(name))
                    bisect.insort(rows, [offset, name, 0])
            self.data = rows
            self.unexpandedSize = len(rows)
        else:
            oldSize = len(self.data)
            if not expanded:
                self.data = self.data[:self.unexpandedSize]
            elif len(self.data) == self.unexpandedSize:
                self.data.append( [] ) # start with an empty buffer row
                rows = [ ]
                for name in PyICU.TimeZone.createEnumeration():
                    if name not in self.info.wellKnownIDs and \
                       name not in TIMEZONE_SHORT_LIST:
                        offset = getOffset(self.view.tzinfo.getInstance(name))
                        bisect.insort(rows, [offset, name, 0])
                self.data.extend(rows)
                
            self.ResetGrid(oldSize)

    def ResetGrid(self, oldNumRows):
        """
        Call this to update the grid if rows and columns have been added or 
        deleted.
        """
        grid = self.grid
        grid.BeginBatch()
        
        new = self.GetNumberRows()
        delmsg = wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED
        addmsg = wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED

        if new < oldNumRows:
            msg = wx.grid.GridTableMessage(self, delmsg, new, oldNumRows - new)
            grid.ProcessTableMessage(msg)
        elif new > oldNumRows:
            msg = wx.grid.GridTableMessage(self, addmsg, new - oldNumRows)
            grid.ProcessTableMessage(msg)
            msg = wx.grid.GridTableMessage(self,
                                      wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
            grid.ProcessTableMessage(msg)

        grid.EndBatch()

        grid.AdjustScrollbars()
        grid.ForceRefresh()


testtime = datetime.datetime(2006, 1, 1)

def getOffset(tzinfo):
    offset = tzinfo.utcoffset(testtime)
    sign = 1
    if offset.days < 0:
        sign = -1
    return sign * abs(offset).seconds / 3600.0
    

class CustTableGrid(wx.grid.Grid):
    def __init__(self, parent, view):
        wx.grid.Grid.__init__(self, parent, -1)

        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnColLeftClick)

        self.table = TimezoneTable(view, self)
        self.SetTable(self.table, True, wx.grid.Grid.SelectRows)
        
        # setting selection mode to SelectRows doesn't remove the cell cursor,
        # so set the selection pen to width 0
        self.SetCellHighlightPenWidth(0)
        self.SetCellHighlightROPenWidth(0)
        

        attr = wx.grid.GridCellAttr()

        nameCol = colData['name']['display']
        offsetCol = colData['offset']['display']
        checkedCol = colData['checked']['display']
        
        attr.SetReadOnly(True)
        self.SetColAttr(nameCol, attr)
        self.SetColAttr(offsetCol, attr)
        
        attr = wx.grid.GridCellAttr()
        attr.SetAlignment(wx.ALIGN_CENTER, -1)
        self.SetColAttr(checkedCol, attr)

        self.SetColSize(nameCol, 200)
        self.ScaleColumn(nameCol, True)
        #self.SetColSize(offsetCol, 100)
        #self.SetColSize(checkedCol, 50)
        self.AutoSizeColumn(offsetCol)
        self.AutoSizeColumn(checkedCol)
        
        self.ScaleWidthToFit(True)

        self.SetRowLabelSize(0)
        self.SetColLabelSize(18)
        self.SetMargins(0,0)

        self.EnableDragRowSize(False)

        self.Layout()


    def OnCellLeftClick(self, evt):
        self.SelectRow(evt.GetRow())
        checkedCol = colData['checked']['display']
        if evt.GetCol() == checkedCol:
            self.table.Toggle(evt.GetRow())
            if not self.table.GetValue(evt.GetRow(), checkedCol):
                self.ClearSelection()
    
    def OnColLeftClick(self, evt):
        pass

TIMEZONE_OTHER_FLAG = -1

def buildTZChoiceList(view, control, selectedTZ=None):
    """
    Take a wx.Choice control and a timezone to select.  Populate the control
    with the appropriate timezones, plus a More option, whose value is
    TIMEZONE_OTHER_FLAG.

    Default selection is view.tzinfo.default.
    
    """
    control.Clear()
    selectIndex = -1
    info = TimeZoneInfo.get(view)
    if selectedTZ is None:
        selectedTZ = olsonizeTzinfo(view, view.tzinfo.default)
    canonicalTimeZone = info.canonicalTimeZone(selectedTZ)

    # rebuild the list of choices
    for name, zone in info.iterTimeZones():
        if canonicalTimeZone == zone:
            selectIndex = control.Append(name, clientData=selectedTZ)
        else:
            control.Append(name, clientData=zone)

    # Always add the More option
    control.Append(_(u"More..."),
                   clientData=TIMEZONE_OTHER_FLAG)

    if selectIndex is -1:
        control.Insert(unicode(selectedTZ), 0, clientData=selectedTZ)
        selectIndex = 0
        
    if selectIndex != -1:
        control.Select(selectIndex)
