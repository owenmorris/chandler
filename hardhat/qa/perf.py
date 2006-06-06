#!/usr/bin/env python
# vi:ts=2 sw=2 nofen

__author__       = "Mike Taylor <bear@code-bear.com>"
__contributors__ = []
__copyright__    = "Copyright (c) 2004,2005 Mike Taylor"
__license__      = "BSD"
__version__      = "1.0"
__svn__          = "$Id$"


import sys, os, string, datetime, time, math
import ConfigParser, optparse

try:
    from pychart import *
    theme.get_options()
    theme.use_color = 1
    theme.scale_factor = 2
    theme.reinitialize()
    
    doChart = True
except ImportError:
    doChart = False
    raise # Comment this out if you don't care about graphs

    
def drawGraph(data, platforms, filename, size=(132, 132), xLabel='Revision'):
    """
    Draw a picture in png format.
    
    @param data:     Format: [(x1, winy1, osxy1, linuxy1, acceptabley1), ...]
    @param platforms:Platforms tuple
    @param filename: A PNG filename (so it should end in '.png').
    """
    if not doChart or len(data) < 1:
        return False

    def ticX(data):
        return int(len(data)/10) + 1

    myCanvas = canvas.init(filename, format='png')

    myXAxis = axis.X(format='/a-45/hL%s',
                     tic_interval = ticX(data),
                     label=xLabel)
    myYAxis = axis.Y(#tic_interval = ticY,
                     label='Seconds')

    myArea = area.T(x_coord=category_coord.T(data, 0),
                    size=size, # about 480x420 image w/ default settings
                    x_axis=myXAxis,
                    y_axis=myYAxis,
                    y_range=(0, None))

    col = 1
    if 'win' in platforms:
        myArea.add_plot(line_plot.T(label='win',
                                    data=data,
                                    ycol=col,
                                    line_style=line_style.darkseagreen,
                                    tick_mark=tick_mark.circle3))
        col += 1
    if 'osx' in platforms:
        myArea.add_plot(line_plot.T(label='osx',
                                    data=data,
                                    ycol=col,
                                    line_style=line_style.red_dash1,
                                    tick_mark=tick_mark.square))
        col += 1
    if 'linux' in platforms:
        myArea.add_plot(line_plot.T(label='linux',
                                    data=data,
                                    ycol=col,
                                    line_style=line_style.darkblue_dash2,
                                    tick_mark=tick_mark.tri))
        col += 1
    myArea.add_plot(line_plot.T(label='acceptable',
                                data=data,
                                ycol=col,
                                line_style=line_style.black_dash2,
                                tick_mark=tick_mark.default))

    myArea.draw(myCanvas)
    
    return True

# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560/index_txt
def unique(s):
    """
    Return a list of the elements in s, but without duplicates.

    For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
    unique("abcabc") some permutation of ["a", "b", "c"], and
    unique(([1, 2], [2, 3], [1, 2])) some permutation of
    [[2, 3], [1, 2]].

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic
    time.
    """

    n = len(s)
    if n == 0:
        return []

    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()

    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]

    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u

def platforms2GraphData(platforms, acceptable):
    """
    Convert the platforms structure and acceptable value into a list of
    tuples needed by drawGraph function.
    
    @return: [(x1, winy1, osxy1, linuxy1, acceptabley1), ...], (win, osx, linux)
    """
    ret = []
    
    osMedians = {'win': {}, 'osx': {}, 'linux': {}}
    
    def median(values):
        """
        Return the median of the values, but ignore 0s as they signify
        a non-value. Also, None is returned if the median would be 0, because
        None is a special value that is ignored by PyChart.
        """
        if len(values) == 0:
            median = None
        else:
            values = [x for x in values if x != 0] # Skip 0s
            if len(values) == 0:
                median = None
            else:
                values.sort()
                median = values[len(values)/2]
        return median
    
    for platform in ('win', 'osx', 'linux'):
        i = 0
        lastRev = 0
        values = []

        for (time, rev) in platforms[platform]['timesRevs']:
            rev = int(rev)
            if rev != lastRev and lastRev != 0:
                osMedians[platform][lastRev] = median(values)
                values = [platforms[platform]['values'][i]]
            else:
                values.append(platforms[platform]['values'][i])
            i += 1
            lastRev = rev
        if  len(values) != 0: # Handle the last value separately
            osMedians[platform][rev] = median(values)
            
    # Find out which platforms have values other than None
    plats = ()
    revs = []
    for value in osMedians['win'].itervalues():
        if value is not None:
            plats += ('win',)
            revs.extend(osMedians['win'].keys())
            break
    for value in osMedians['osx'].itervalues():
        if value is not None:
            plats += ('osx',)
            revs.extend(osMedians['osx'].keys())
            break
    for value in osMedians['linux'].itervalues():
        if value is not None:
            plats += ('linux',)
            revs.extend(osMedians['linux'].keys())
            break

    revs = unique(revs)
    revs.sort()
        
    for rev in revs:
        item = (rev,)
        if 'win' in plats:
            item += (osMedians['win'].get(rev, None), )
        if 'osx' in plats:
            item += (osMedians['osx'].get(rev, None), )
        if 'linux' in plats:
            item += (osMedians['linux'].get(rev, None), )
        item += (acceptable, )
        ret.append(item)
    
    return ret, plats
    
                         
def colorDelta(current, prev, stdDev):
    """
    Return the color for the deltas.

    Changes are within std dev, no coloring:
    
    >>> colorDelta(1, 1, 0.01)
    'ok'
    >>> colorDelta(1.05, 1, 0.1)
    'ok'
    >>> colorDelta(1, 1.05, 0.1)
    'ok'
    
    Previous run had no result (0), so no coloring:
    
    >>> colorDelta(1, 0.0, 0.01)
    'ok'
    
    Current run had no result (0), so no coloring:
    
    >>> colorDelta(0, 1, 0.01)
    'ok'
    
    Significant improvement:
    
    >>> colorDelta(1, 2, 0.01)
    'good'

    More than 10% slowdown:
    
    >>> colorDelta(2, 1, 0.01)
    'alert'

    Less than 10% slowdown:
    
    >>> colorDelta(1.05, 1, 0.01)
    'warn'
    """
    if prev == 0 or current == 0:
        return 'ok'
    
    delta = prev - current
    
    if delta - stdDev > 0:
        return 'good'
    
    if delta + stdDev < 0:
        percentage = delta / prev * -1 # * -1 makes it positive
        if percentage < 0.1:
            return 'warn'
        
        return 'alert'
    
    return 'ok'


class perf:
  def __init__(self):
    self._app_path = os.getcwd()
    self._options  = { 'tbox_data':  '.',    # raw .perf files
                       'html_data':  '.',    # where to output generated .html
                       'perf_data':  '.',    # where to store processed data
                       'verbose':    False,
                       'debug':      False,
                       'cleanup':    False,  # remove .perf files when processed
                       'configfile': 'perf.cfg',
                       'section':    'base',
                       'warn':       2.0,    # range of values to control color of cells
                       'alert':      5.0,
                       'p_alert':    100.0, # percentage change to warn about (for summary only)
                       'delta_days': 30,    # how many days to include in detailed long history and graph
                     }

    self.loadConfiguration()

    self.verbose = self._options['verbose']

    self.SummaryTests = [('startup',                                             '#1 Startup'),
         ('new_event_from_file_menu_for_performance.event_creation',             '#2 New event (menu)'),
         ('new_event_by_double_clicking_in_the_cal_view_for_performance.double_click_in_the_calendar_view', '#3 New event (double click)'),
         ('test_new_calendar_for_performance.collection_creation',               '#4 New calendar'),
         ('importing_3000_event_calendar.import',                                '#5 Import 3k event calendar'),
         ('startup_with_large_calendar',                                         '#6 Startup with 3k event calendar'),
         ('creating_new_event_from_the_file_menu_after_large_data_import.event_creation', '#7 New event (menu) with 3k event calendar'),
         ('creating_a_new_event_in_the_cal_view_after_large_data_import.double_click_in_the_calendar_view', '#8 New event (double click) with 3k event calendar'),
         ('creating_a_new_calendar_after_large_data_import.collection_creation', '#9 New calendar with 3k event calendar'),
         ('switching_to_all_view_for_performance.switch_to_allview',             'Switch Views'),
         ('perf_stamp_as_event.change_the_event_stamp',                          'Stamp'),
         ('switching_view_after_importing_large_data.switch_to_allview',         'Switch Views with 3k event calendar'),
         ('stamping_after_large_data_import.change_the_event_stamp',             'Stamp with 3k event calendar'),
         ('scroll_calendar_one_unit.scroll_calendar_one_unit',                   'Scroll calendar with 3k event calendar'),
         ('scrolling_a_table.scroll_table_25_scroll_units',                      'Scroll table with 3k event calendar'),
         ('jump_from_one_week_to_another.jump_calendar_by_one_week',             'Jump calendar by one week with 3k event calendar'),
         ('overlay_calendar.overlay_calendar',                                   'Overlay calendar with 3k event calendar'),
         #('resize_app_in_calendar_mode.resize_app_in_calendar_mode',             'Resize calendar with 3k event calendar'),
        ]

      # all times are in seconds
    self.SummaryTargets = {'startup':                                           10, 
         'new_event_from_file_menu_for_performance.event_creation':             1,
         'new_event_by_double_clicking_in_the_cal_view_for_performance.double_click_in_the_calendar_view': 1,
         'test_new_calendar_for_performance.collection_creation':               1,
         'importing_3000_event_calendar.import':                                30,
         'startup_with_large_calendar':                                         10,
         'creating_new_event_from_the_file_menu_after_large_data_import.event_creation': 1,
         'creating_a_new_event_in_the_cal_view_after_large_data_import.double_click_in_the_calendar_view': 1,
         'creating_a_new_calendar_after_large_data_import.collection_creation': 1,
         'switching_to_all_view_for_performance.switch_to_allview':             1,
         'perf_stamp_as_event.change_the_event_stamp':                          1,
         'switching_view_after_importing_large_data.switch_to_allview':         1,
         'stamping_after_large_data_import.change_the_event_stamp':             1,
         'scroll_calendar_one_unit.scroll_calendar_one_unit':                   0.1,
         'scrolling_a_table.scroll_table_25_scroll_units':                      0.1,
         'jump_from_one_week_to_another.jump_calendar_by_one_week':             1,
         'overlay_calendar.overlay_calendar':                                   1,
         #'resize_app_in_calendar_mode.resize_app_in_calendar_mode':             0.1,
        }

    self.PerformanceTBoxes = ['p_win', 'p_osx', 'p_linux']

    if self._options['debug']:
      print 'Configuration Values:'
      for key in self._options:
        print '\t%s: [%r]' % (key, self._options[key])

  def colorTime(self, testName, testTime, stdDev):
        """
        Return the color for the test time.
    
        Times within std dev of acceptable, no coloring:
    
        >>> perf = perf() #doctest: +ELLIPSIS
        ...
        >>> perf.colorTime('perf_stamp_as_event', 1, 0.01)
        'ok'
        >>> perf.colorTime('perf_stamp_as_event', 1.05, 0.1)
        'ok'
        >>> perf.colorTime('perf_stamp_as_event', 0.95, 0.1)
        'ok'

        No result (0 time):
    
        >>> perf.colorTime('perf_stamp_as_event', 0.0, 0.1)
        'ok'

        Significantly better than acceptable:
    
        >>> perf.colorTime('perf_stamp_as_event', 0.95, 0.01)
        'good'
    
        Significantly slower than acceptable:
    
        >>> perf.colorTime('perf_stamp_as_event', 1.05, 0.01)
        'warn'
        >>> perf.colorTime('perf_stamp_as_event', 2.05, 0.1)
        'warn'
    
        Twice as slow as acceptable:
    
        >>> perf.colorTime('perf_stamp_as_event', 2.05, 0.01)
        'alert'
        """
        if testTime == 0:
            return 'ok'
        
        acceptable = self.SummaryTargets[testName]
        
        if testTime < (acceptable - stdDev):
            return 'good'
        
        if testTime > (2 * acceptable + stdDev):
            return 'alert'
        
        if testTime > (acceptable + stdDev):
            return 'warn'
    
        return 'ok'

  def loadConfiguration(self):
    items = { 'configfile': ('-c', '--config',   's', self._options['configfile'], '', ''),
              'verbose':    ('-v', '--verbose',  'b', self._options['verbose'],    '', ''),
              'debug':      ('-d', '--debug',    'b', self._options['debug'],      '', ''),
              'cleanup':    ('-x', '--cleanup',  'b', self._options['cleanup'],    '', ''),
              'tbox_data':  ('-t', '--tboxdata', 's', self._options['tbox_data'],  '', ''),
              'html_data':  ('-o', '--htmldata', 's', self._options['html_data'],  '', ''),
              'perf_data':  ('-p', '--perfdata', 's', self._options['perf_data'],  '', ''),
              'warn':       ('-w', '--warn',     'f', self._options['warn'],       '', ''),
              'alert':      ('-a', '--alert',    'f', self._options['alert'],      '', ''),
              'p_alert':    ('-P', '--p_alert',  'f', self._options['p_alert'],    '', ''),
            }

    parser = optparse.OptionParser(usage="usage: %prog [options]", version="%prog " + __version__)

    for key in items:
      (shortCmd, longCmd, optionType, defaultValue, environName, helpText) = items[key]

      if environName and os.environ.has_key(environName):
          defaultValue = os.environ[environName]

      if optionType == 'b':
          parser.add_option(shortCmd, longCmd, dest=key, action='store_true', default=defaultValue, help=helpText)
      else:
        if optionType == 'f':
          parser.add_option(shortCmd, longCmd, dest=key, type='float', default=defaultValue, help=helpText)
        else:
          parser.add_option(shortCmd, longCmd, dest=key, default=defaultValue, help=helpText)

    (options, self._args) = parser.parse_args()

    for key in items:
      self._options[key] = options.__dict__[key]

    config = ConfigParser.ConfigParser()

    if os.path.isfile(self._options['configfile']):
      config.read(self._options['configfile'])

      if config.has_section(self._options['section']):
        for (item, value) in config.items(self._options['section']):
          if self._options.has_key(item) and items.has_key(item):
            optionType = items[item][2]

            if optionType == 'b':
              self._options[item] = (string.lower(value) == 'true')
            else:
              if optionType == 'f':
                self._options[item] = float(value)
              else:
                self._options[item] = value
    else:
      print 'Unable to locate the configuration file %s' % self._options['configfile']
      sys.exit(0)

  def loadPerfData(self):
    if self._options['debug']:
      t = time.time()

    datafiles = {}
    perfs     = os.listdir(self._options['tbox_data'])

    if self.verbose:
      print 'Scanning %d files from %s' % (len(perfs), self._options['tbox_data'])

    for perf in perfs:
      if os.path.splitext(perf)[1] == '.perf':
        perffile  = os.path.join(self._options['tbox_data'], perf)

          # UGLY CODE ALERT!
          # currently the tests are run twice, once for debug and once for release
          # the following code skips the debug and processes only the release
          # *BUT* it does this by assuming that there are equal number lines for each part
          # UGLY CODE ALERT!

        lines = file(perffile).readlines()

        p = len(lines)

        if p > 0:
          # the .perf files are not named by the builder that created them
          # so we have to figure the name out during parsing and then use
          # that name later to archive the file to the appropriate tarball
          line      = lines[0]
          item      = string.split(string.lower(line[:-1]), '|')
          treename  = item[0]
          buildname = item[1].lower()

          if buildname in self.PerformanceTBoxes:
                # Performance tboxes only run release mode tests so will not have any
                # debug data so the starting point will be the first line instead of p / 2
              p = 0

              for line in lines[p:]:
                item = string.split(string.lower(line[:-1]), '|')

                  # each line of a .perf file has the following format
                  # treename | buildname | date | time | testname | svn rev # | time

                if not datafiles.has_key(buildname):
                  datafiles[buildname] = file(os.path.join(self._options['perf_data'], ('%s.dat' % buildname)), 'a')

                datafiles[buildname].write('%s\n' % string.join(item[2:], '|'))

        if self._options['cleanup']:
          os.remove(perffile)

    for key in datafiles:
      datafiles[key].close()

    if self._options['debug']:
      print 'Processed %d files in %d seconds' % (len(perfs), time.time() - t)

  def churnData(self):
    tests = {}
    today = datetime.datetime.today()

    startdate = '%04d%02d%02d' % (today.year, today.month, today.day)
    enddate   = '20010101'

    datfiles = os.listdir(self._options['perf_data'])

    if self.verbose:
      print 'Loading data files from %s' % self._options['perf_data']

    for filename in datfiles:
      (buildname, extension) = os.path.splitext(filename)

      if extension == '.dat':
        datafile  = os.path.join(self._options['perf_data'], filename)

        if self.verbose:
          print 'Processing file %s' % filename

        for line in file(datafile):
          try:
            (itemDate, itemTime, testname, revision, runtime) = string.split(string.lower(line[:-1]), '|')

            itemDateTime = datetime.datetime(int(itemDate[:4]), int(itemDate[4:6]), int(itemDate[6:8]), int(itemTime[:2]), int(itemTime[2:4]), int(itemTime[4:6]))

            delta = today - itemDateTime

            if delta.days < self._options['delta_days']:
              testname = string.strip(testname)
              hour     = itemTime[:2]

              try:
                runtime  = float(runtime)
              except ValueError:
                runtime = 0.0

                # only work with data that have positive runtimes
                # as all other values are from bogus/broken runs
              if runtime > 0.0:
                if itemDate < startdate:
                  startdate = itemDate

                if itemDate > enddate:
                  enddate = itemDate

                  # data points are put into test and date buckets
                  #   each test has a dictionary of builds
                  #   each build has a dictionary of dates
                  #   each date has a dictionary of times (hour resolution)
                  #   each time is a list of data points
                  # tests { testname: { build: { date: { hour: [ (testname, itemDateTime, delta.days, buildname, revision, runtime) ] }}}}

                if not tests.has_key(testname):
                  tests[testname] = {}

                testitem = tests[testname]

                if not testitem.has_key(buildname):
                  testitem[buildname] = {}

                builditem = testitem[buildname]

                if not builditem.has_key(itemDate):
                  builditem[itemDate] = {}

                dateitem = builditem[itemDate]

                if not dateitem.has_key(hour):
                  dateitem[hour] = []

                dateitem[hour].append((testname, itemDateTime, delta.days, buildname, hour, revision, runtime))

          except:
            print "Error processing line for file [%s] [%s]" % (filename, line[:-1])

    return (tests, startdate, enddate)

  def standardDeviation(self, values):
    count  = len(values)
    stdDev = 0.0
    mean   = 0.0
    s      = 0.0

    if count > 1:
        # algorithm is from http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance

      for n in xrange(1, count + 1):
        delta = values[n - 1] - mean
        mean  = mean + delta / float(n)
        s     = s + delta * (values[n - 1] - mean)

      var    = s / (n - 1)
      stdDev = math.sqrt(var)

    else:
      mean = values[0]

    return (stdDev, count, mean)

  def generateDetailPage(self, pagename, tests, startdate, enddate):
    # tests { testname: { build: { date: { hour: [ (testname, itemDateTime, delta.days, buildname, hour, revision, runs, total, average) ] }}}}

      # some 'constants' to make it easier to add items to the data structure
      # without having to track down all occurances of 7 to change it to 8 :)
    DP_REVISION = 5
    DP_RUNTIME  = 6

    indexpage  = []
    detailpage = []

    indexpage.append('<h1>Performance Standard Deviation for the previous %d days</h1>\n' % self._options['delta_days'])
    indexpage.append('<div id="summary">\n')
    indexpage.append('<p>From %s-%s-%s to %s-%s-%s<br/>\n' % (startdate[:4], startdate[4:6], startdate[6:8],
                                                              enddate[:4], enddate[4:6], enddate[6:8]))
    indexpage.append(time.strftime('<small>Generated %d %b %Y at %H%M %Z</small></p>', time.localtime()))

    detailpage.append('<h1>Performance Standard Deviation for the previous 7 days</h1>\n')
    detailpage.append('<div id="detail">\n')

    graphTests = self.SummaryTargets.keys()
    
    graphDict = {}
    
    for testkey in tests.keys():
      if testkey in graphTests:
          
        testitem = tests[testkey]

        indexpage.append('<h2 id="%s">%s</h2>\n' % (testkey, testkey))
        detailpage.append('<h2>%s</h2>\n' % testkey)

        k_builds = testitem.keys()
        k_builds.sort()
        k_builds.reverse()

        indexpage.append('<table>\n')
        indexpage.append('<colgroup><col class="build"></col><col></col><col class="size"></col><col class="avg"></col></colgroup>\n')
        indexpage.append('<tr><th></th><th></th><th colspan="2">Sample</th><th colspan="9">Difference of Sample Average to Prior Day (avg - pd)</th>')
        indexpage.append('<tr><th>Build</th><th>Std.Dev.</th><th>Count</th><th>Average</th><th>0</th><th>-1</th><th>-2</th><th>-3</th><th>-4</th><th>-5</th><th>-6</th><th>-7</th><th>-8</th></tr>\n')

        graphPlatform = {'win':{}, 'osx':{}, 'linux':{}}

        for buildkey in k_builds:
          builditem = testitem[buildkey]

            # make one pass thru to gather the data points
          values = []
          day_values = {}
                    
          for datekey in builditem.keys():
            dateitem = builditem[datekey]

            k_hours = dateitem.keys()
            k_hours.sort()

            date_values = []

            for hour in k_hours:
              for datapoint in dateitem[hour]:
                if self._options['debug']:
                  print "%s %s %s %s %f" % (testkey, buildkey, datekey, hour, datapoint[DP_RUNTIME])
                values.append(datapoint[DP_RUNTIME])
                date_values.append(datapoint[DP_RUNTIME])

            dv_count = len(date_values)
            dv_total = 0

            if dv_count > 0:
              for item in date_values:
                dv_total = dv_total + item

            day_values[datekey] = (dv_count, dv_total)

          (v, n, avg) = self.standardDeviation(values)

          if self._options['debug']:
            print "std.dev: %02.5f average: %02.3f count: %d" % (v, avg, n)

          tv_dates = []

            # now run thru again to gererate the html - but now we have averages to use for markup
          k_dates = builditem.keys()
          k_dates.sort()
          k_dates.reverse()

          detailpage.append('<h3 id="%s_%s">%s</h3>\n' % (testkey, buildkey, buildkey))
          detailpage.append('<p>Sample Average is %2.3f and std.dev is %2.3f</p>\n' % (avg, v))
          detailpage.append('<!-- avg: %02.5f count: %d stddev: %02.5f -->\n' % (avg, n, v))

          for datekey in k_dates:
            dateitem = builditem[datekey]

            dv_count, dv_total = day_values[datekey]
            if dv_count > 0:
              dv_avg = dv_total / dv_count
            else:
              dv_avg = dv_total

            if dv_avg <> 0:
              c_perc = (dv_avg - avg) / dv_avg
            else:
              c_perc = 0
            c_diff = avg - dv_avg

            graphPlatform[buildkey[2:]][datekey] = dv_avg
            
            tv_dates.append((datekey, dv_avg, c_perc, c_diff))

            detailpage.append('<h4>%s-%s-%s</h4>\n' % (datekey[:4], datekey[4:6], datekey[6:8]))
            detailpage.append('<p>%d items in days sample for an average of %2.3f' % (dv_count, dv_avg))
            detailpage.append('<table>\n')
            detailpage.append('<colgroup><col class="time"></col><col class="run"></col><col class="avg"></col></colgroup>\n')
            detailpage.append('<tr><th></th><th></th><th></th><th></th><th colspan="2">Change (Day)</th>')
            detailpage.append('<tr><th>Time</th><th>Run Time</th><th>Percent</th><th>Percent</th><th>Value</th></tr>\n')

            k_hours = dateitem.keys()
            k_hours.sort()

            for hour in k_hours:
              for datapoint in dateitem[hour]:
                s    = 'ok'
                perc = 0

                if avg > 0:
                  perc = abs((avg - datapoint[DP_RUNTIME]) / avg) * 100

                  if perc > 66:
                    s = 'alert'
                  else:
                    if perc > 33:
                      s = 'warn'

                if dv_avg <> 0:
                  c_perc = (dv_avg - datapoint[DP_RUNTIME]) / dv_avg
                c_diff = datapoint[DP_RUNTIME] - dv_avg

                detailpage.append('<tr><td>%02d:%02d:%02d</td><td class="%s">%02.3f</td>' \
                                  '<td class="number">%d</td><td class="number_left">%02.3f</td><td class="number">%02.3f</td></tr>\n' %
                                  (datapoint[1].hour, datapoint[1].minute, datapoint[1].second,
                                   s, datapoint[DP_RUNTIME], perc, c_perc, c_diff))
                detailpage.append('<!-- value: %02.5f count: %d avg: %02.5f %02.5f c_perc: %02.5f c_diff: %02.5f -->\n' %
                                  (datapoint[DP_RUNTIME], n, avg, perc, c_perc, c_diff))

            detailpage.append('</table>\n')

          if v > self._options['alert']:
            s = 'alert'
          else:
            if v > self._options['warn']:
              s = 'warn'
            else:
              s = 'ok'

          t  = ''
          dt = ''
          for item in tv_dates:
            dt += '<!-- datekey: %s dv_avg: %02.5f c_perc: %02.5f c_diff %02.5f -->\n' % (item)
            t  += '<td class="number_left">%02.3f</td>' % item[3]

          indexpage.append('<tr><td><a href="detail_%s_%s.html#%s_%s">%s</a></td><td class="%s" style="border-right: 2px;">%02.3f</td>' \
                           '<td class="number">%d</td><td class="number">%02.3f</td>%s</tr>\n' %
                           (startdate, enddate, testkey, buildkey, buildkey, s, v, n, avg, t))
          indexpage.append(dt)

        indexpage.append('</table>\n')
        
        graphDict[testkey] = graphPlatform
    
    def plat2data(graphPlatform, acceptable):
      dates = unique(graphPlatform['win'].keys() + \
                     graphPlatform['osx'].keys() + \
                     graphPlatform['linux'].keys())
      dates.sort()
      data = []
      for date in dates:
        data.append((date, 
                     graphPlatform['win'].get(date, None),
                     graphPlatform['osx'].get(date, None),
                     graphPlatform['linux'].get(date, None),
                     acceptable))

      return data
    
    
    detailfilename = 'detail_%s_%s.html' % (startdate, enddate)
    
    trendspage = ['<html><head><title>Performance trends for the last %d days</title></head>\n<body><h1>Performance trends for the last %d days</h1>' % (self._options['delta_days'], self._options['delta_days'])]
    trendspage.append('<p><a href="%s">Numerical trends</a></p>' % detailfilename)
    graphPlatforms = ('win', 'osx', 'linux') # We are assuming we get data for all in such a long period of time
    for (test, testDisplayName) in self.SummaryTests:
      graphPlatform = graphDict[test]
       
      #print  plat2data(graphPlatform, self.SummaryTargets[test])
      graphfilename = '%d_%s.png' % (self._options['delta_days'], test)
      graphfile = os.path.join(self._options['html_data'], graphfilename)
      drawGraph(plat2data(graphPlatform, self.SummaryTargets[test]),
                graphPlatforms,
                graphfile, 
                size=(264, 132), xLabel='Date')
      trendspage.append('<h2>%s</h2><img src="%s" alt="graph" title="%s">' % (testDisplayName, graphfilename, testDisplayName))

    trendspage.append('</body></html>')
    detailpage.append('</div>\n')
    indexpage.append('</div>\n')

    indexfile = file(os.path.join(self._options['html_data'], pagename), 'w')

    if os.path.isfile(os.path.join(self._options['perf_data'], 'index.html.header')):
      for line in file(os.path.join(self._options['perf_data'], 'index.html.header')):
        indexfile.write(line)

    for line in indexpage:
      indexfile.write(line)

    if os.path.isfile(os.path.join(self._options['perf_data'], 'index.html.footer')):
      for line in file(os.path.join(self._options['perf_data'], 'index.html.footer')):
        indexfile.write(line)

    indexfile.close()

    detailfile = file(os.path.join(self._options['html_data'], detailfilename), 'w')

    if os.path.isfile(os.path.join(self._options['perf_data'], 'detail.html.header')):
      for line in file(os.path.join(self._options['perf_data'], 'detail.html.header')):
        detailfile.write(line)

    for line in detailpage:
      detailfile.write(line)

    if os.path.isfile(os.path.join(self._options['perf_data'], 'detail.html.footer')):
      for line in file(os.path.join(self._options['perf_data'], 'detail.html.footer')):
        detailfile.write(line)

    detailfile.close()

    trendsfile = file(os.path.join(self._options['html_data'], 'trends.html'), 'w')

    for line in trendspage:
      trendsfile.write(line)

    trendsfile.close()


  def _generateSummaryDetailLine(self, platforms, testkey, enddate, testDisplayName, currentValue, previousValue):
      graph = []
      
      if testkey in self.SummaryTargets.keys():
        targetAvg = self.SummaryTargets[testkey]
      else:
        targetAvg = 0.0

      line  = '<tr><td><a href="detail_%s.html#%s" target="_new">%s</a></td>' % (enddate, testkey, testDisplayName)
      line += '<td class="number">%2.1fs</td>' % targetAvg

      for key in ['win', 'osx', 'linux']:
        current  = currentValue[key]
        previous = previousValue[key]
        revision = platforms[key]['revision']
        stdDev   = platforms[key]['stddev']

        c_diff = current - previous

        if previous <> 0:
          c_perc = (c_diff / previous) * 100
        else:
          c_perc = 0

        s         = colorDelta(current, previous, stdDev)
        timeClass = self.colorTime(testkey, current, stdDev)

        graph.append('%s | %s | %s | %s | %02.3f | %02.3f | %03.1f\n' % (enddate, key, testkey, revision, current, c_diff, c_perc))

        if self._options['debug']:
          print key, testkey, targetAvg, current, previous, c_perc, c_diff, s, stdDev

        line += '<td class="number%s">%2.2fs</td>' % (timeClass, current)
        line += '<td class="%s">%+3.0f%%</td>' % (s, c_perc)
        line += '<td class="%s">%+1.2fs</td>' % (s, c_diff)
        line += '<td>%01.2fs</td>' % stdDev
        #line += '<td>%0.2es</td>' % stdDev

      line += '</tr>\n'

      return (line, graph)

  def generateSummaryPage(self, pagename, tests, startdate, enddate):
    # tests { testname: { build: { date: { hour: [ (testname, itemDateTime, delta.days, buildname, hour, revision, runtime) ] }}}}

    # This code assumes that there will only be a single buildkey (i.e. tinderbox) for each platform

      # some 'constants' to make it easier to add items to the data structure
      # without having to track down all occurances of 7 to change it to 8 :)
    DP_DATETIME = 1
    DP_REVISION = 5
    DP_RUNTIME  = 6

    page   = []
    detail = []
    tbox   = []
    graph  = []

    revisions     = { 'osx':   ['', ''],
                      'linux': ['', ''],
                      'win':   ['', ''], }

    updates       = { 'osx':   '',
                      'linux': '',
                      'win':   ''
                    }

    currentValue  = { 'osx':   0,
                      'linux': 0,
                      'win':   0,
                    }

    previousValue = { 'osx':   0,
                      'linux': 0,
                      'win':   0,
                    }

    detail.append('<h1>Use Case Performance Detail</h1>\n')
    detail.append('<div id="detail">\n')
    detail.append('<p>Sample Date: %s-%s-%s<br/>\n' % (enddate[:4], enddate[4:6], enddate[6:8]))
    detail.append(time.strftime('<small>Generated %d %b %Y at %H%M %Z</small></p>', time.localtime()))

    for (testkey, testDisplayName) in self.SummaryTests:
      if testkey in tests.keys():
        testitem = tests[testkey]

        detail.append('<hr>\n')
        detail.append('<div class="section">\n')
        graphfile = 'day_%s.png' % testkey.replace('.', '_')
        detail.append('<img class="daygraph" src="%s" alt="graph">' % graphfile)
        detail.append('<h2 id="%s">%s</h2>\n' % (testkey, testDisplayName))

        platforms = { 'osx':   { 'stddev':   0,
                                 'avg':      0,
                                 'count':    0,
                                 'total':    0,
                                 'values':   [],
                                 'timesRevs':[],
                                 'revision': '' },
                      'linux': { 'stddev':   0,
                                 'avg':      0,
                                 'count':    0,
                                 'total':    0,
                                 'values':   [],
                                 'timesRevs':[],
                                 'revision': '' },
                      'win':   { 'stddev':   0,
                                 'avg':      0,
                                 'count':    0,
                                 'total':    0,
                                 'values':   [],
                                 'timesRevs':[],
                                 'revision': '' },
                    }

        for buildkey in self.PerformanceTBoxes:
          if buildkey in testitem.keys():
            builditem = testitem[buildkey]

            if 'osx' in buildkey:
              platformkey = 'osx'
            elif 'win' in buildkey:
              platformkey = 'win'
            else:
              platformkey = 'linux'

            platformdata = platforms[platformkey]

            k_dates = builditem.keys()
            k_dates.sort()
            k_dates.reverse()

            datekey  = k_dates[0]
            dateitem = builditem[datekey]

            k_hours = dateitem.keys()
            k_hours.sort()

            dv_total = 0
            revision = ''

            detail.append('\n<h3 id="%s_%s">%s</h3>\n' % (testkey, buildkey, buildkey))
            detail.append('<table>\n')
            detail.append('<tr><th>Run at</th><th>Rev #</th><th>Time</th><th>&Delta; %</th><th>&Delta; time</th></tr>\n')

            previous = 0
            
            for hour in k_hours:
              for datapoint in dateitem[hour]:
                current   = datapoint[DP_RUNTIME]
                revision  = datapoint[DP_REVISION]
                update    = datapoint[DP_DATETIME]
                dv_total += current

                platformdata['values'].append(current)
                platformdata['timesRevs'].append(('%02d:%02d:%02d' % (datapoint[1].hour, datapoint[1].minute, datapoint[1].second),
                                                  revision))

                c_diff = current - previous

                if previous <> 0:
                  c_perc = (c_diff / previous) * 100
                  deltaClass = colorDelta(current, previous, 0.02) # bogus std dev
                else:
                  c_perc = 0
                  deltaClass = 'ok'
                timeClass = self.colorTime(testkey, current, 0.02)# bogus std dev
                
                detail.append('<tr><td>%02d:%02d:%02d</td><td>%s</td><td class="number%s">%02.2fs</td><td class="%s">%+3.0f%%</td><td class="%s">%+1.2fs</td></tr>\n' %
                              (datapoint[1].hour, datapoint[1].minute, datapoint[1].second,
                               revision, timeClass, current, deltaClass, c_perc, deltaClass, c_diff))
                detail.append('<!-- revision %s runtime %02.5f -->\n' % (revision, current))

                if self._options['debug']:
                  print "%s %s %s %s %s %s %f" % (testDisplayName, platformkey, buildkey, datekey, hour, revision, current)
                
                previous = current

            (v, n, avg) = self.standardDeviation(platformdata['values'])

            #print "average: %02.5f count: %d stddev: %02.5f" % (avg, n, v)
            page.append('<!-- build: %s avg: %02.5fs count: %d stddev: %02.5fs -->\n' % (buildkey, avg, n, v))

            detail.append('</table>\n')
            detail.append('<p>%d items in days sample for an average of %02.2fs and a standard deviation of %02.2fs</p>\n' % (n, avg, v))

            platformdata['stddev']   = v
            platformdata['avg']      = avg
            platformdata['total']    = dv_total
            platformdata['count']    = n
            platformdata['revision'] = revision

            updates[platformkey] = update

            if len(k_hours) > 2:
              revisions[platformkey] = [revision, dateitem[k_hours[-2]][0][DP_REVISION]]
            else:
              revisions[platformkey] = [revision, revision]

            p = len(k_hours)
            if n > 1:
              currentValue[platformkey]  = dateitem[k_hours[p-1]][0][DP_RUNTIME]
              previousValue[platformkey] = dateitem[k_hours[p-2]][0][DP_RUNTIME]
            else:
              currentValue[platformkey]  = dateitem[k_hours[p-1]][0][DP_RUNTIME]
              previousValue[platformkey] = dateitem[k_hours[p-1]][0][DP_RUNTIME]

        (summaryline, graphdata) = self._generateSummaryDetailLine(platforms, testkey, enddate, testDisplayName, currentValue, previousValue)

        page.append(summaryline)
        tbox.append(summaryline)

        graph += graphdata
        
        (data, plats) = platforms2GraphData(platforms,
                                            self.SummaryTargets[testkey])
        #graphfile = 'day_%s.png' % testkey.replace('.', '_')
        if drawGraph(data, plats, os.path.join(self._options['html_data'],
                                               graphfile)):
            #detail.append('<img src="%s">' % graphfile)
            pass
        detail.append('</div>')
        
    page.append('</table>\n')
                                      
    page.append('<p>The Test name link will take you to the detail information that was \n')
    page.append('used to generate the summary numbers for that test<br/>\n')
    page.append('The original <a href="stddev.html">standard deviation page</a> shows the other test \n')
    page.append('data that is captured and the standard deviation data for the last 7 days</p>\n')

    page.append('</div>\n')

    detail.append('</div>\n')

    tbox.append('</table>\n</div>\n')

    pagefile = file(os.path.join(self._options['html_data'], pagename), 'w')

    pagefile.write('<h1>Use Case Performance Summary</h1>\n')
    pagefile.write('<div id="summary">\n')
    pagefile.write('<p>Sample Date: %s-%s-%s<br/>\n' % (enddate[:4], enddate[4:6], enddate[6:8]))
    pagefile.write(time.strftime('<small>Generated %d %b %Y at %H%M %Z</small></p>\n', time.localtime()))

    pagefile.write('<p>This is a summary of the performance totals</p>\n')
    pagefile.write('<p>The Median is calculated from the total number of \n')
    pagefile.write('test runs for the given day<br/>\n')
    pagefile.write('The &Delta; % is measured from the last Milestone.  \n')
    pagefile.write('All time values use seconds for the unit of measure</p>\n')
    pagefile.write('<p>Note: a negative &Delta; value means that the current \n')
    pagefile.write('median value is <strong>slower</strong> than the target value</p>\n')

    pagefile.write('<table>\n')
    pagefile.write('<tr><th></th>')
    pagefile.write('<th colspan="5">Windows (r %s)</th>' % revisions['win'][0])
    pagefile.write('<th colspan="5">OS X (r %s)</th>' % revisions['osx'][0])
    pagefile.write('<th colspan="5">Linux (r %s)</th></tr>\n' % revisions['linux'][0])
    pagefile.write('<tr><th>Test</th>')
    pagefile.write('<th>Target</th><th>time</th><th>&Delta; %</th><th>&Delta; time</th><th>std.dev</th>')
    pagefile.write('<th>Target</th><th>time</th><th>&Delta; %</th><th>&Delta; time</th><th>std.dev</th>')
    pagefile.write('<th>Target</th><th>time</th><th>&Delta; %</th><th>&Delta; time</th><th>std.dev</th></tr>\n')

    if os.path.isfile(os.path.join(self._options['perf_data'], 'index.html.header')):
      for line in file(os.path.join(self._options['perf_data'], 'index.html.header')):
        pagefile.write(line)

    for line in page:
      pagefile.write(line)

    if os.path.isfile(os.path.join(self._options['perf_data'], 'index.html.footer')):
      for line in file(os.path.join(self._options['perf_data'], 'index.html.footer')):
        pagefile.write(line)

    pagefile.close()

    graphfile = file(os.path.join(self._options['html_data'], 'graph_%s.dat' % (enddate)), 'w')

    for line in graph:
      graphfile.write(line)

    graphfile.close()

    detailfile = file(os.path.join(self._options['html_data'], 'detail_%s.html' % (enddate)), 'w')

    if os.path.isfile(os.path.join(self._options['perf_data'], 'detail.html.header')):
      for line in file(os.path.join(self._options['perf_data'], 'detail.html.header')):
        detailfile.write(line)

    for line in detail:
      detailfile.write(line)

    if os.path.isfile(os.path.join(self._options['perf_data'], 'detail.html.footer')):
      for line in file(os.path.join(self._options['perf_data'], 'detail.html.footer')):
        detailfile.write(line)

    detailfile.close()

    tboxfile = file(os.path.join(self._options['html_data'], 'tbox.html'), 'w')

    if os.path.isfile(os.path.join(self._options['perf_data'], 'tbox.html.header')):
      for line in file(os.path.join(self._options['perf_data'], 'tbox.html.header')):
        tboxfile.write(line)

    tbox.append('<p>')
    latestUpdate = {}
    for key in ['win', 'osx', 'linux']:
      update = updates[key]
      month  = getattr(update, 'month', None)
      day    = getattr(update, 'day', None)
      hour   = getattr(update, 'hour', None)
      minute = getattr(update, 'minute', None)
      if month is not None and day is not None and hour is not None \
          and minute is not None:
        tbox.append('%s: %d/%02d %d:%02d<br>' % (key, month, day, hour, 
                                                    minute))
        s               = '%02d%02d%02d%02d' % (month, day, hour, minute)
        latestUpdate[s] = '%d/%02d %d:%02d' % (month, day, hour, minute)
      else:
        tbox.append('%s: Unknown<br>' % key)
    tbox.append('</p>')

    keys = latestUpdate.keys()
    keys.reverse()
    latest = latestUpdate[keys[0]]

    tboxfile.write('<div id="tbox">\n')
    tboxfile.write('<table cellspacing="1">\n')
    tboxfile.write('<tr><th rowspan="2">Test (<a href="%s" target="_new">trends</a>)<br/>Latest results as of %s</th><th rowspan="2">0.6<br/>Target</th>' % ('trends.html', latest))
    tboxfile.write('<th colspan="4">Windows (r %s vs %s)</th>' % (revisions['win'][0], revisions['win'][1]))
    tboxfile.write('<th colspan="4">OS X (r %s vs %s)</th>' % (revisions['osx'][0], revisions['osx'][1]))
    tboxfile.write('<th colspan="4">Linux (r %s vs %s)</th></tr>\n' % (revisions['linux'][0], revisions['linux'][1]))
    tboxfile.write('<tr>')
    tboxfile.write('<th>time</th><th>&Delta; %</th><th>&Delta; time</th><th>std.dev</th>')
    tboxfile.write('<th>time</th><th>&Delta; %</th><th>&Delta; time</th><th>std.dev</th>')
    tboxfile.write('<th>time</th><th>&Delta; %</th><th>&Delta; time</th><th>std.dev</th></tr>\n')

    for line in tbox:
      tboxfile.write(line)

    if os.path.isfile(os.path.join(self._options['perf_data'], 'tbox.html.footer')):
      for line in file(os.path.join(self._options['perf_data'], 'tbox.html.footer')):
        tboxfile.write(line)

    tboxfile.close()


  def generatePerfDetailPage(self, pagename, tests, startdate, enddate):
    # tests { testname: { build: { date: { hour: [ (testname, itemDateTime, delta.days, buildname, hour, revision, runtime) ] }}}}

      # some 'constants' to make it easier to add items to the data structure
      # without having to track down all occurances of 7 to change it to 8 :)
    DP_REVISION = 5
    DP_RUNTIME  = 6

    page = []

    page.append('<h1>Performance Detail Summary</h1>\n')
    page.append('<div id="detail">\n')
    page.append('<p>Sample Date: %s-%s-%s to %s-%s-%s<br/>\n' % (startdate[:4], startdate[4:6], startdate[6:8],
                                                                 enddate[:4], enddate[4:6], enddate[6:8]))
    page.append(time.strftime('<small>Generated %d %b %Y at %H%M %Z</small></p>', time.localtime()))

    for (testkey, testDisplayName) in self.SummaryTests:
      if testkey in tests.keys():
        testitem = tests[testkey]

        page.append('<h2 id="%s">%s: %s</h2>\n' % (testkey, testDisplayName, testkey))

        for buildkey in self.PerformanceTBoxes:
          if buildkey in testitem.keys():
            builditem = testitem[buildkey]

            if 'osx' in buildkey:
              platformkey = 'osx'
            elif 'win' in buildkey:
              platformkey = 'win'
            else:
              platformkey = 'linux'

            page.append('<h3>%s</h3>' % platformkey)
            page.append('<table>\n')
            page.append('<tr><th>Time</th><th>Rev #</th><th>Run Time</th><th>&Delta; %</th><th>&Delta; Time</th></tr>\n')

            previousRevision = ''
            previousTime     = 0

            details = []

            k_dates = builditem.keys()
            k_dates.sort()

            for datekey in k_dates:
              dateitem = builditem[datekey]

              k_hours = dateitem.keys()
              k_hours.sort()

              for hour in k_hours:
                for datapoint in dateitem[hour]:
                  revision = datapoint[DP_REVISION]
                  current  = datapoint[DP_RUNTIME]

                  if previousTime == 0:
                    previousTime = current

                  c_diff = current - previousTime

                  if previousTime <> 0:
                    c_perc = (c_diff / previousTime) * 100
                  else:
                    c_perc = 0

                  s         = colorDelta(current, previousTime, 0.2)
                  timeClass = self.colorTime(testkey, current, 0.2)

                    #Time     | Rev # | Run Time | &Delta; % | &Delta; time
                    #======================================================
                    #00:43:49 | 7846  | 0.02s    |           |
                    #01:32:02 | 7856  | 0.01s    | -50%      | -0.01s

                  line =  '<tr><td>%02d:%02d:%02d</td><td>%s</td>' % (datapoint[1].hour,
                                                                      datapoint[1].minute,
                                                                      datapoint[1].second, revision)
                  line += '<td class="number%s">%2.2fs</td>' % (timeClass, current)
                  line += '<td class="%s">%+3.0f%%</td>' % (s, c_perc)
                  line += '<td class="%s">%+1.2fs</td>' % (s, c_diff)
                  line += '</tr>\n'

                  details.append(line)

                  previousTime     = current
                  previousRevision = revision

            details.reverse()
            page += details

            page.append('</table>\n')
                                      
    page.append('</div>\n')

    pagefile = file(os.path.join(self._options['html_data'], pagename), 'w')

    if os.path.isfile(os.path.join(self._options['perf_data'], 'index.html.header')):
      for line in file(os.path.join(self._options['perf_data'], 'index.html.header')):
        pagefile.write(line)

    for line in page:
      pagefile.write(line)

    if os.path.isfile(os.path.join(self._options['perf_data'], 'index.html.footer')):
      for line in file(os.path.join(self._options['perf_data'], 'index.html.footer')):
        pagefile.write(line)

    pagefile.close()


  def generateOutput(self, tests, startdate, enddate):
    self.generateDetailPage('stddev.html', tests, startdate, enddate)
    self.generateSummaryPage('index.html', tests, startdate, enddate)
    self.generatePerfDetailPage('perfdetail.html', tests, startdate, enddate)

  def process(self):
      # check for new .perf files
    self.loadPerfData()

      # process stored data
    (tests, startdate, enddate) = self.churnData()

      # generate html
    self.generateOutput(tests, startdate, enddate)

if __name__ == "__main__":
  p = perf()
  p.process()
