#   Copyright (c) 2004-2007 Open Source Applications Foundation
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

"""
Dialog for editing custom recurrence, weekly and monthly.
"""

import wx
import re

from PyICU import DateFormatSymbols
from osaf.pim.calendar.Recurrence import RecurrenceRule
from osaf.framework.blocks.calendar.CalendarUtility import GregorianCalendarInstance
import calendar
from dateutil import rrule
from i18n import ChandlerMessageFactory as _

def parse_rrule(rule):
    """
    Parse the given C{rrule}, returning a 3-element C{tuple}:

    element 0: C{true_rep}: A C{boolean}: That indicates if this rule can be
                represented exactly in the UI. In practice, this is used to
                pop up a confirmation dialog before editing.
    element 1: C{canonical}: A C{dict} of keywords you can use to initialize
                a C{dateutil.rrule.rrule}. 
    element 2: C{passthru}: A C{dict} of keywords that the UI ignores, but
                won't result in data loss when you edit. Examples include
                C{'until'}, C{'byhour'}. C{EditRecurrence} includes these
                values in the returned C{dict}.
    """
    
    true_rep = True
    canonical = {}
    passthru = {}
    
    if rule._count:
        # We don't support COUNT rules
        true_rep = False
    
    wkst = rule._wkst
    if wkst != calendar.firstweekday(): # sic (rrule inserts this automatically)
        passthru['wkst'] = wkst

    for attr in "hour", "minute", "second":
        # rrule creates these automatically, so bypass the automatically
        # set values.
        val = getattr(rule, '_by' + attr, None)
        # default value is a 1-element tuple with value
        # matching _dtstart.
        if val and val != (getattr(rule._dtstart, attr),):
            passthru['by' + attr] = val

    for attr in 'until',:
        val = getattr(rule, '_' + attr, None)
        if val is not None:
            passthru[attr] = val

    canonical.update(interval=rule._interval)
    

    # _byweekday: tuple of ints
    # _bynweekday: tuple of (day, n) ints
    # We combine these into a tuple of rrule.weekday objects

    # Only support of BYSETPOS is in the "alternate byweekday rule "below,
    # and we only support a single value here.
    bysetposException = (
        len(rule._byweekday or ()) == 1 == len(rule._bysetpos or ()))

    byweekday = []
    
    if rule._bynweekday:
        if len(rule._bynweekday) > 1:
            true_rep = False
        elif rule._bynweekday[0][1] not in (1, 2, 3, 4, -1):
            true_rep = False
        byweekday.extend(rrule.weekday(*t) for t in rule._bynweekday)

    if bysetposException:
        byweekday.append(rrule.weekday(rule._byweekday[0], rule._bysetpos[0]))
    elif rule._byweekday and rule._byweekday != (rule._dtstart.weekday(),):
        byweekday.extend(rrule.weekday(day) for day in rule._byweekday)
        
    if byweekday:
        canonical.update(byweekday=tuple(byweekday))

    if (rule._bysetpos and not bysetposException):
        true_rep = False

    if rule._bymonth and rule._bymonth != (rule._dtstart.month,):
        canonical.update(bymonth=rule._bymonth)

    # rule._bymonthday == days of month counted from start
    # rule._bynmonthday == days of month counted from end (unsupported)
    bymonthday = rule._bymonthday + rule._bynmonthday
    if bymonthday and bymonthday != (rule._dtstart.day,):
        canonical.update(bymonthday=tuple(sorted(bymonthday)))

    if rule._bynmonthday:
        # We only support -1 for _bynmonthday
        if not all(day == -1 for day in rule._bynmonthday):
            true_rep = False

    # rule._byweekno (unsupported)
    if rule._byweekno:
        true_rep = False
        canonical.update(byweekno=rule._byweekno)

    if rule._byyearday:
        true_rep = False
        canonical.update(byyearday=rule._byyearday)

    canonical.update(freq=rule._freq)
    
    customKeys = set(canonical.keys()) - set(['freq', 'interval'])
    if rule._freq == rrule.YEARLY:
        if customKeys - set(['bymonth', 'byweekday']):
            true_rep = False
    elif rule._freq == rrule.MONTHLY:
        # For monthly, we support exactly one of bymonthday and
        # byweekday
        if len(customKeys) > 1:
            true_rep = False
        elif customKeys - set(['bymonthday', 'byweekday']):
             true_rep = False
         # Note, not supporting multiple _bynweekday is handled earlier
    elif rule._freq == rrule.WEEKLY:
        if customKeys - set(['byweekday']):
            true_rep = False
    elif rule._freq == rrule.DAILY:
        if customKeys:
            true_rep = False
    else:
        # We don't support HOURLY/MINUTELY/SECONDLY
        true_rep = False

    return true_rep, canonical, passthru


def EditRecurrence(ruleOrEvent, start=None, parent=None):
    """
    Top-level call to edit a C{dateutil.rrule}. Currently, this does this by
    bringing up a modal dialog, but this could eventually be done via some
    kind of popup window.
    
    @param ruleOrEvent: The C{rrule} you want to edit. This can be specified
                        as a C{osaf.pim.EventStamp} instance, in which case
                        C{rrule} information is extracted from the event's
                        rruleset.
                        
                        If the rule ends up being C{None}, the dialog will
                        pick default values (weekly, on C{start}'s day of
                        the week.
    @type ruleOrEvent: C{dateutil.rrule.rrule}, C{osaf.pim.EventStamp}
    
    @type start: For testing purposes, the C{dtstart} to supply to
                 C{dateutil}. Defaults to C{datetime.now()} at the time
                 of the call.
    @type start: C{datetime.datetime}
                        
    @param parent: The wx parent for the attached dialog.
    @type parent: C{None} or C{wx.Window}
    
    @return: C{None} if the user cancels editing, else a C{dict} of
             values you can pass to the C{dateutil.rrule.rrule} constructor.
    @rtype: dict
    """
    
    if ruleOrEvent is None or isinstance(ruleOrEvent, rrule.rrule):
        rule = ruleOrEvent
    else:
        rruleset = ruleOrEvent.rruleset
        start = ruleOrEvent.getMaster().startTime
    
        if rruleset and rruleset.rrules:
            first = rruleset.rrules.first()
            rule = first.createDateUtilFromRule(start)
        else:
            rule = None

    # Save away values in rule that we're not going to edit

    if rule is None:
        if start is None:
            start = datetime.datetime.now()
        true_rep = True
        passthru = {}
        canonical = {}
    else:
        true_rep, canonical, passthru = parse_rrule(rule)
        
        if not true_rep:
            confirm = wx.MessageBox(_(
u"""Currently, Chandler does not support editing this recurrence rule.

If you continue to edit, you will lose the current recurrence rule.
"""), style=wx.OK|wx.CANCEL|wx.CENTER|wx.ICON_WARNING, parent=parent)

            if confirm == wx.ID_CANCEL:
                return None

    dialog = CustomDialog(parent, -1)
    dialog.setupUI(canonical)
    
    if parent:
        dialog.CenterOnParent()
    else:
        dialog.CenterOnScreen()
    
    try:
        if dialog.ShowModal() == wx.ID_OK:
            result = dict(dialog.GetResult())
            
            if result == canonical:
                # No change!
                return None
            result.update(passthru)
            return result
        else:
            return None
    finally:
        dialog.Destroy()

def split_format(inputStr):
    results = []
    lastReturned = 0
    buf = ""
    
    for match in re.finditer(r"(%%)|%\(([^(]+)\)s", inputStr):
        buf += inputStr[lastReturned:match.start()]
        lastReturned = match.end()

        if match.groups()[0] is not None:
            # Match for %%
            buf += "%"
        else:
            results.append(buf)
            buf = ""
            results.append(match.groups()[1])
    buf += inputStr[lastReturned:]
    results.append(buf)
    
    return results


def LayoutTextWithControls(parent, format, **kw):
    """
    Utility function that returns a horizontal wx.Sizer containing
    text and controls laid out to a python %-style format string. This helps
    avoid issues with unlocalizable UIs. For example, if you called
    
    LayoutTextWithControls(None, "This is text: %(text)s",
                           text=wx.TextCtrl(None, -1, "Hi"))

    the returned horizontal sizer would contain a C{wx.StaticText} containing
    "This is text: ", followed by the above C{wx.TextCtrl}. (In practice, you
    would pass in a real widget for parent, of course).
    
    @param parent: The parent for any {wx.StaticText} objects this function
                   creates.
    @type format: L{wx.Window}
    
    @param format: The %-format style str. The only supported formats
        for now are of the form %()s -- the usual format for localized
        strings.
    @type format: C{basestring}

    @param kw: Values in C{kw} are treated as items that can be added to
        the returned Sizer. So, they should either be wx.Sizer instances

    @param rtype: L{wx.Sizer}
    """
    box = wx.BoxSizer(wx.HORIZONTAL)
    prefix = kw.get('prefix')
    
    splitFormat = split_format(format)
    
    while splitFormat:
        text = splitFormat.pop(0)
        
        if text:
            # possible for text to be empty if two %(...)s strings
            # are adjacent, or if format starts with %(...)s string.
            if prefix is not None:
                ctrl = prefix
                ctrl.SetLabel(text)
                prefix = None
            else:
                ctrl = wx.StaticText(parent, -1, text)
            box.Add(ctrl, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)

        if splitFormat:
            argName = splitFormat.pop(0)
            control = kw[argName] # Will raise KeyError if missing,
                                  # which is probably good.
            box.Add(control, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)

    return box


# These first utility functions convert rrule format. They're functions
# to make them easy to test.

def _rr_weekday_to_gui(rweekday):
    """Given r 0=Mon, ... value, returns 0 based GUI i18n index"""
    # figure the day in sun=1 units
    sun1 = rweekday + 2
    if sun1 == 8: sun1 = 1
    fdow = GregorianCalendarInstance.getFirstDayOfWeek()  ## sun1 units
    return (7 + sun1 - fdow) % 7
    
def extractGuiWeekdays(d):
    """Returns [0, 3, 6] list of gui indexes from rrule bynweekday or
       byweekday or [] if not found."""
    weekdays = d.get('byweekday')
    if weekdays:
        return sorted([_rr_weekday_to_gui(wd.weekday) for wd in weekdays])
    else:
        return []
    
def extractGuiByWeekday(d):
    """Returns [(2, -1)] list (day, onthe) or [] if not found."""
    weekdays = d.get('byweekday')
    if weekdays:
        return sorted((_rr_weekday_to_gui(wd.weekday), wd.n)
                            for wd in weekdays if wd.n)
    else:
        return []

def extractGuiByDay(d):
    """Returns [day1, day2, ...] for BYMONTHDAY entries"""
    days = d.get('bymonthday')
    return days if days else []

def extractGuiByMonth(d):
    """Returns [month1, month2, ...] for BYMONTH entries"""
    months = d.get('bymonth')
    return months if months else []

def extractIsDaily(d):
    """True if daily"""
    return d['freq'] == rrule.DAILY

def extractIsWeekly(d):
    """True if weekly"""
    return d['freq'] == rrule.WEEKLY

def extractIsMonthly(d):
    """True if monthly"""
    return d['freq'] == rrule.MONTHLY

def extractIsYearly(d):
    """True if yearly"""
    return d['freq'] == rrule.YEARLY

def extractInterval(d):
    """Returns int interval"""
    return d['interval']

def _gui_weekday_to_rr(i):
    """
    Given zero based i from the GUI, which is i18n first day based,
    translate to the rrule int for that day. Inverse of
    L{_rr_weekday_to_gui}
    """
    ## now this is a sun=1 encoding of the day that's positive
    sun1 = i + GregorianCalendarInstance.getFirstDayOfWeek()
    
    ## rrule array is fixed['mon', 'tue', ...], so, er, figure out math
    ## sun=1 yields 6
    ## mon=2 yields 0
    ## tue=3 yields 1
    return rrule.weekdays[(sun1 + 5) % 7]

    
class CustomDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        kw.setdefault('title', _(u'Custom Recurring Event'))
        super(CustomDialog, self).__init__(*args, **kw)
        
        # Create actual stuff
        
        ## Outermost sizer
        outer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(outer)
        
        ## Every XXX Day(s)/Week(s)/Month(s)/Year(s)
        self.ctrl_freq = wx.Choice(self, -1, (100, 50), choices=[_(u'Day(s)'), _(u'Week(s)'), _(u'Month(s)'), _(u'Year(s)')])
        self.ctrl_freq.SetSelection(1) # weekly by default
        self.ctrl_freq.Bind(wx.EVT_CHOICE, self.OnChoice)
        
        self.ctrl_interval = wx.SpinCtrl(self, -1, min=1, max=30000, initial=1)

        sizer = LayoutTextWithControls(
                    self,
                    _(u"Every %(how_often)s %(frequency)s"),
                    how_often=self.ctrl_interval,
                    frequency=self.ctrl_freq)
        outer.Add(sizer, 0, wx.ALL, 5)
        
        ## 1. Daily (actually empty)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox_daily = vbox
        outer.Add(vbox, 0, wx.LEFT|wx.RIGHT, 12)

        ## 2. Weekly
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox_weekly = vbox
        outer.Add(vbox, 0, wx.LEFT|wx.RIGHT, 12)
        
        ## Pick Days
        vbox.Add(wx.StaticText(self, -1, _(u"On the following day(s):")))
        box = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(box)
        days = self._getDayNames()
        self.ctrl_daytoggles = []  # keep ptr to toggles
        for i in range(len(days)):
            toggle = wx.ToggleButton(self, -1, days[i], size=(40,-1))
            self.ctrl_daytoggles.append(toggle)
            box.Add(toggle, 0, wx.TOP|wx.BOTTOM, 5)


        ## 3. Monthly
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox_monthly = vbox
        outer.Add(vbox, 0, wx.LEFT|wx.RIGHT, 12)

        ## Monthly/Choices
        self.ctrl_monthly_byweek = wx.RadioButton(self, -1, "", style=wx.RB_GROUP)
        (sizer,
        self.ctrl_onthe,
        self.ctrl_ontheday) = self.createByWeekdayUI(self.ctrl_monthly_byweek)
        vbox.Add(sizer)

        line = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL)
        vbox.Add(line, 0, wx.GROW|wx.BOTTOM|wx.TOP, 5)
        
        ## Grid of days of the month
        self.ctrl_monthly_byday = wx.RadioButton(self, -1, _(u"On the &following day(s):"))
        vbox.Add(self.ctrl_monthly_byday)
        self.ctrl_monthday_toggles = []
        sizer = wx.GridBagSizer(hgap=0, vgap=0)
        for daynum in xrange(1, 32):
            toggle = wx.ToggleButton(self, -1, u"%d" % (daynum,), size=(30, 30))
            position = (daynum - 1)//7, (daynum - 1)%7
            sizer.Add(toggle, position)
            self.ctrl_monthday_toggles.append((daynum, toggle))

        toggle = wx.ToggleButton(self, -1, _(u"last"), size=(30, 30))
        self.ctrl_monthday_toggles.append((-1, toggle))
        sizer.Add(toggle, (4, 5), wx.GBSpan(1, 2), flag=wx.EXPAND)
        vbox.Add(sizer, 0, wx.ALL, 12)
        

        ## 4. Yearly
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox_yearly = vbox
        outer.Add(vbox, 0, wx.LEFT|wx.RIGHT, 12)
        
        vbox.Add(wx.StaticText(self, -1, _(u"In the following month(s):")),
                 0, wx.BOTTOM, 5)
        
        ## Grid of month names
        monthNames = self._getMonthNames()
        numCols = 4
        numRows = numCols * (len(monthNames) + numCols - 1)/numCols
        monthsSizer = wx.GridSizer(rows=numRows, cols=numCols, hgap=0, vgap=0)
        
        self.ctrl_monthtoggles = []
        for month in monthNames:
            toggle = wx.ToggleButton(self, -1, month, size=(45, 45))
            self.ctrl_monthtoggles.append(toggle)
            monthsSizer.Add(toggle, 0, 0)
        vbox.Add(monthsSizer, 1, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT, 12)
        vbox.AddSpacer(5)

        ## Choice of day of the month
        self.ctrl_year_byday = wx.CheckBox(self, -1, "")
        (sizer,
        self.ctrl_year_weekno,
        self.ctrl_year_dayname) = self.createByWeekdayUI(self.ctrl_year_byday)
        vbox.Add(sizer)

        line = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL)
        outer.Add(line, 0, wx.GROW|wx.BOTTOM|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        self.ctrl_ok = btn
        btn.SetDefault()
        btnsizer.AddButton(btn)
        
        self.ctrl_ok.Bind(wx.EVT_BUTTON, self.OnOk)
        
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        outer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.GROW|wx.ALL, 5)
        
        # Start out in weekly mode
        self.showPane(1)
        outer.Fit(self)

    def setupUI(self, d):
        if not d:
            # Set up defaults for non-recurring events
            d = { 'freq':rrule.WEEKLY, 'interval':1 }

        # Try to pre-set the weekly toggles and the monthly choice
        # based on days in the current rule.
        
        days = extractGuiWeekdays(d)
        # set all the toggles
        for i in days:
            self.ctrl_daytoggles[i].SetValue(True)
        # set the first one in monthly
        if days:
            self.ctrl_ontheday.SetSelection(days[0])
            self.ctrl_year_dayname.SetSelection(days[0])

        interval = extractInterval(d)
        self.ctrl_interval.SetValue(interval)

        tuples = extractGuiByWeekday(d)
        self.ctrl_onthe.SetSelection(0)
        self.ctrl_year_weekno.SetSelection(0)

        self.ctrl_monthly_byweek.Value = self.ctrl_year_byday.Value = bool(tuples)
        if tuples:
            self.ctrl_monthly_byweek.Value = self.ctrl_year_byday.Value = True
            (day, onthe) = tuples[0]  # we use the first one, though there could be more
            for index in xrange(self.ctrl_onthe.GetCount()):
                if self.ctrl_onthe.GetClientData(index) == onthe:
                    self.ctrl_onthe.SetSelection(index)
                    break
            for index in xrange(self.ctrl_year_weekno.GetCount()):
                if self.ctrl_year_weekno.GetClientData(index) == onthe:
                    self.ctrl_year_weekno.SetSelection(index)
                    break
            self.ctrl_ontheday.SetSelection(day)
            self.ctrl_year_dayname.SetSelection(day)
        else:
            self.ctrl_monthly_byday.Value = True

        days = extractGuiByDay(d)
        for daynum, button in self.ctrl_monthday_toggles:
            button.Value = (daynum in days)
        
        months = extractGuiByMonth(d)
        for index, button in enumerate(self.ctrl_monthtoggles):
            button.Value = (index + 1 in months)

        if extractIsDaily(d):
            self.showPane(0)  # we're daily
            self.ctrl_freq.SetSelection(0)
        elif extractIsWeekly(d):
            # NOP, we're weekly by default
            pass
        elif extractIsMonthly(d):
            self.showPane(2)  # we're monthly
            self.ctrl_freq.SetSelection(2)
        elif extractIsYearly(d):
            self.showPane(3) # we're yearly
            self.ctrl_freq.SetSelection(3)

    def _getDayNames(self, short=True):
        symbols = DateFormatSymbols()
        days = symbols.getShortWeekdays() if short else symbols.getWeekdays()
        firstDay = GregorianCalendarInstance.getFirstDayOfWeek()
        
        daynames = []
        for day in xrange(7):
            actualDay = ((day + firstDay - 1) % 7)
            daynames.append(days[actualDay + 1])
        return daynames

    def _getMonthNames(self, short=True):
        symbols = DateFormatSymbols()
        return symbols.getShortMonths() if short else symbols.getMonths()
    
    def getByWeekdayFromUI(self, weeknoChoice, weekdayChoice):
        """
        Given a C{wx.Choice} objects for week number and weekday,
        return a value suitable for passing in to C{dateutil.rrule.byweekday}.
        
        @param weeknoChoice: Week number UI (first/second/third/fourth/last)
        @type weeknoChoice: C{wx.Choice}
        
        @param weekdayChoice: Day of week UI (Sunday/ .../ Saturday)
        @type weekdayChoice: C{wx.Choice}
        
        @rtype: C{list}
        """
        # See createByWeekdayUI() below; GetClientData returns
        # the actual data for the selected item in weeknoChoice
        index = weeknoChoice.GetSelection()
        weekno = weeknoChoice.GetClientData(index)
        weekday = _gui_weekday_to_rr(weekdayChoice.GetSelection())
        
        # technically, our UI only allows a single value, whereas in
        # principle there could 
        return [weekday(weekno)]

    def createByWeekdayUI(self, prefix):
        """
        Create dropdowns for "nth day of week" GUI.
        
        returns a 3-element tuple of:
        
        sizer
        week number control: wx.Choice containing first, second, ..., last
        weekday control: wx.Choice containing Sunday ... Saturday
        """
        weeknoCtrl = wx.Choice(self, -1, (100, 50))
        
        # We use ClientData to convey the actual value to be returned
        for label, data in (
            (_(u"first"), 1),
            (_(u"second"), 2),
            (_(u"third"), 3),
            (_(u"fourth"), 4),
            (_(u"last"), -1),
        ):
            weeknoCtrl.Append(label, data)
        weekdayCtrl = wx.Choice(self, -1, (100, 50), choices=self._getDayNames(False))
        sizer = LayoutTextWithControls(self,
                    _(u"O&n the %(which_week)s %(weekday)s"),
                    which_week=weeknoCtrl,
                    weekday=weekdayCtrl,
                    prefix=prefix,
                )
        return sizer, weeknoCtrl, weekdayCtrl
        
    def showPane(self, pick):
        # pick 0 for daily, 1 for weekly, 2 for monthly
        self.vbox_daily.ShowItems(pick == 0)
        self.vbox_weekly.ShowItems(pick == 1)
        self.vbox_monthly.ShowItems(pick == 2)
        self.vbox_yearly.ShowItems(pick == 3)
        self.ctrl_freq.SetFocus()
        self.Fit()

    def OnChoice(self, event):
        self.showPane(self.ctrl_freq.GetSelection())
        
    def OnOk(self, event):
        """Checks text field entry on ok button."""
        try:
            val = self.ctrl_interval.GetValue()
            
            if (val > 0):
                event.Skip()  # allow ok to go through
                return
                
        except:
            pass  # do nothing
        
        # Otherwise fall through to here, put up error message,
        # and since we did not Skip(), the Ok button fails.
        # Thus confirming the magical nature of Skip().
        wx.MessageBox(_(u'For "Every ..." needs integer like 1, 2, 3'),
                      _(u'Warning'), parent=self)
        
        
    def GetResult(self):
        '''
         Returns rruleArgs dict for custom daily, weekly, and  monthly cases.
         e.g.
           daily, every other day
           {'freq': DAILY, 'interval': 2}
           weekly, Every 2 weeks, mon wed:
           {'freq': WEEKLY, 'interval': 2, 'wkst': SU, 'byweekday': [MO, WE]}
           monthly, last sat:
           {freq': MONTHLY, 'interval': 1, 'byweekday': [SA(-1)]}
        '''
        rruleArgs = {}
        selection = self.ctrl_freq.GetSelection()
        rruleArgs['interval'] = int(self.ctrl_interval.GetValue())
        if selection == 0:
            rruleArgs['freq'] = rrule.DAILY
        elif selection == 1:
            rruleArgs['freq'] = rrule.WEEKLY
            byweekday =  [  # map each index in Gui to rrule const
                _gui_weekday_to_rr(index)
                for index, toggle in enumerate(self.ctrl_daytoggles)
                if toggle.GetValue()
            ]
            if byweekday:
                rruleArgs['byweekday'] = tuple(byweekday)
        elif selection == 2:
            rruleArgs['freq'] = rrule.MONTHLY
            if self.ctrl_monthly_byday.Value:
                bymonthday = [daynum for daynum, button in self.ctrl_monthday_toggles if button.Value]
                if bymonthday:
                    rruleArgs['bymonthday'] = tuple(bymonthday)

            if self.ctrl_monthly_byweek.Value:
                byweekday = self.getByWeekdayFromUI(self.ctrl_onthe,
                                                    self.ctrl_ontheday)
                if byweekday:
                    rruleArgs['byweekday'] = tuple(byweekday)
        else:
            rruleArgs['freq'] = rrule.YEARLY
            bymonth = [index + 1 for index, button in enumerate(self.ctrl_monthtoggles) if button.Value]
            if bymonth:
                rruleArgs['bymonth'] = tuple(bymonth)

            if self.ctrl_year_byday.Value:
                byweekday = self.getByWeekdayFromUI(self.ctrl_year_weekno,
                                                    self.ctrl_year_dayname)
                if byweekday:
                    rruleArgs['byweekday'] = tuple(byweekday)
            
        return rruleArgs

if __name__ == "__main__":
    import sys
    from vobject.icalendar import RecurringComponent, VEvent
    import datetime
    
    app = wx.PySimpleApp()

    for rruleText in sys.argv[1:] or (None,):
        if rruleText:
            rule = rrule.rrulestr(rruleText)
        else:
            rule = None
    
        result = EditRecurrence(rule)
        print 'Result: %s' % (result,)

        if result is not None:
            # Let's use vobject to print out the icalendar form of the
            # rule
            rule = rrule.rrule(**result)
            vobject_event = RecurringComponent()
            vobject_event.behavior = VEvent
            # vobject_event.rruleset will be unhappy if we don't have a
            # dtstart
            vobject_event.add('dtstart').value = datetime.date.today()
            rruleset = rrule.rruleset()
            rruleset.rrule(rule)
            vobject_event.rruleset=rruleset
            # ok, now we're ready to serialize (we strip off the trailing '\r\n')
            output = vobject_event.rrule_list[0].serialize().strip()
            print 'ICS output: %s' % (output,)
