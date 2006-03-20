from datetime import datetime
from i18n import OSAFMessageFactory as _
import PyICU
from TimeZone import formatTime

"""
General date/time utility functions

Herein lies: 
- The mechanism we use to naively compare datetimes that might or might not
  have timezones associated with them (see, I made a little joke there, using
  the word 'naively' in this context. Aren't you glad you read this comment?)

- Instances of the PyICU objects related to formatting and parsing date/time-
  related stuff using the current locale. (@@@ eventually, I'd guess that we'll
  have a method here to update these objects when the user changes the current
  locale on the fly...)

"""
  
def removeTypeError(f):
    def g(dt1, dt2):
        if isinstance(dt2, datetime) and isinstance(dt1, datetime):
            naive1 = (dt1.tzinfo is None)
            naive2 = (dt2.tzinfo is None)
            
            if naive1 != naive2:
                if naive1:
                    dt2 = dt2.replace(tzinfo=None)
                else:
                    dt1 = dt1.replace(tzinfo=None)
        return f(dt1, dt2)
    return g

__opFunctions = {
    'cmp': removeTypeError(lambda x, y: cmp(x, y)),
    'max': removeTypeError(lambda x, y: max(x, y)),
    'min': removeTypeError(lambda x, y: min(x, y)),
    '-':   removeTypeError(lambda x, y: x - y),
    '<':   removeTypeError(lambda x, y: x < y),
    '>':   removeTypeError(lambda x, y: x > y),
    '<=':  removeTypeError(lambda x, y: x <= y),
    '>=':  removeTypeError(lambda x, y: x >= y),
    '==':  removeTypeError(lambda x, y: x == y),
    '!=':  removeTypeError(lambda x, y: x != y)
}

def datetimeOp(dt1, operator, dt2):
    """
    This function is a workaround for some issues with
    comparisons of naive and non-naive C{datetimes}. Its usage
    is slightly goofy (but makes diffs easier to read):
    
    If you had in code::
    
        dt1 < dt2
        
    and you weren't sure whether dt1 and dt2 had timezones, you could
    convert this to::
    
       datetimeOp(dt1, '<', dt2)
       
    and not have to deal with the TypeError you'd get in the original code. 
   
    Similar conversions hold for other comparisons, '-', '>', '<=', '>=',
    '==', '!='. Also, there are functions with implied comparison; you can do::
   
       max(dt1, dt2) --> datetimeOp(dt1, 'max', dt2)
      
    and similarly for min, cmp.
    
    For more details (and why this is a kludge), see
    <http://wiki.osafoundation.org/bin/view/Journal/GrantBaillie20050809>
    """
    
    f = __opFunctions.get(operator, None)
    if f is None:
        raise ValueError, "Unrecognized operator '%s'" % (operator)
    return f(dt1, dt2)

class DatetimeFormatter(object):
    """This class works around some issues with timezone dependence of
    PyICU DateFormat objects; for details, see:

    <http://wiki.osafoundation.org/bin/view/Journal/GrantBaillie20050809>

    @ivar dateFormat: A C{PyICU.DateFormat} object, which we want to
      use to parse or format dates/times in a timezone-aware fashion.
    """
    def __init__(self, dateFormat):
        super(DatetimeFormatter, self).__init__()
        self.dateFormat = dateFormat
        
    def parse(self, string, referenceDate=None):
        """
        @param string: The date/time string to parse
        @type string: C{str} or C{unicode}

        @param referenceDate: Specifies what timezone to use when
            interpretting the parsed result.
        @type referenceDate: C{datetime}

        @return: C{datetime}
        
        @raises: ICUError or ValueError (The latter occurs because
            PyICU DateFormat objects sometimes claim to parse bogus
            inputs like "06/05/0506/05/05". This triggers an exception
            later when trying to create a C{datetime}).
        """

        tzinfo = None
        if referenceDate is not None:
            tzinfo = referenceDate.tzinfo
            
        if tzinfo is None:
            self.dateFormat.setTimeZone(PyICU.ICUtzinfo.getDefault().timezone)
        else:
            self.dateFormat.setTimeZone(tzinfo.timezone)
        
        timestamp = self.dateFormat.parse(string)
        
        if tzinfo is None:
            # We started with a naive datetime, so return one
            return datetime.fromtimestamp(timestamp)
        else:
            # Similarly, return a naive datetime
            return datetime.fromtimestamp(timestamp, tzinfo)
        
    def format(self, datetime):
        """
        @param datetime: The C{datetime} to format. If it's naive,
            its interpreted as being in the user's default timezone.

        @return: A C{unicode}
        
        @raises: ICUError
        """
        tzinfo = datetime.tzinfo
        if tzinfo is None: tzinfo = PyICU.ICUtzinfo.getDefault()
        self.dateFormat.setTimeZone(tzinfo.timezone)
        return unicode(self.dateFormat.format(datetime))

shortDateFormat = DatetimeFormatter(
    PyICU.DateFormat.createDateInstance(PyICU.DateFormat.kShort))
mediumDateFormat = DatetimeFormatter(
    PyICU.DateFormat.createDateInstance(PyICU.DateFormat.kMedium))
shortTimeFormat = DatetimeFormatter(
    PyICU.DateFormat.createTimeInstance(PyICU.DateFormat.kShort))
durationFormat = PyICU.SimpleDateFormat(_(u"H:mm"))

symbols = PyICU.DateFormatSymbols()
weekdayNames = symbols.getWeekdays()
monthNames = symbols.getMonths()

def weekdayName(when):
    # Get the name of the day for this datetime.
    # Convert python's weekday (Mon=0 .. Sun=6) to PyICU's (Sun=1 .. Sat=7).
    wkDay = ((when.weekday() + 1) % 7) + 1
    return unicode(weekdayNames[wkDay])
    
# We want to build hint strings like "mm/dd/yy" and "hh:mm PM", but we don't 
# know the locale-specific ordering of these fields. Format a date with 
# distinct values, then replace the resulting string's pieces with text. 
# (Some locales use 4-digit years, some use two, so we'll handle both.)
sampleDate = unicode(shortDateFormat.format(datetime(2003,10,30))
                     .replace(u"2003", _(u"yyyy"))
                     .replace(u"03", _(u"yy"))
                     .replace(u"10", _(u"mm"))
                     .replace(u"30", _(u"dd")))
sampleTime = unicode(shortTimeFormat.format(datetime(2003,10,30,11,45))
                     .replace("11", _(u'hh'))
                     .replace("45", _(u'mm')))
