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


allPlatforms = ('win', 'osx', 'linux')
    
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
    linesAndTicks = ((None, None), # because col begins from 1
                     (line_style.darkseagreen, tick_mark.circle3),
                     (line_style.red_dash1, tick_mark.square),
                     (line_style.darkblue_dash2, tick_mark.tri))
    for p in allPlatforms:
        if p in platforms:
            myArea.add_plot(line_plot.T(label=p,
                                        data=data,
                                        ycol=col,
                                        line_style=linesAndTicks[col][0],
                                        tick_mark=linesAndTicks[col][1]))
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

def platforms2GraphData(platforms, acceptable):
    """
    Convert the platforms structure and acceptable value into a list of
    tuples needed by drawGraph function.
    
    @return: [(x1, winy1, osxy1, linuxy1, acceptabley1), ...], (win, osx, linux)
    """
    ret = []
    
    osMedians = {}
    
    for platform in allPlatforms:
        i = 0
        lastRev = 0
        values = []
        osMedians[platform] = {}

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
    for p in allPlatforms:
        for value in osMedians[p].itervalues():
            if value is not None:
                plats += (p,)
                revs.extend(osMedians[p].keys())
                break

    revs = unique(revs)
    revs.sort()
        
    for rev in revs:
        item = (rev,)
        for p in allPlatforms:
            if p in plats:
                item += (osMedians[p].get(rev, None), )
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
                       'delta_days': 30,    # how many days to include in detailed long history and graph
                     }

    self.loadConfiguration()

    self.verbose = self._options['verbose']

    # all lower case test name  
    # target time in seconds
    # official test name
    self.testTimeName = (
        ('startup',                                                             10, '#1 Startup'),
        ('new_event_from_file_menu_for_performance.event_creation',             1,  '#2 New event (menu)'),
        ('new_event_by_double_clicking_in_the_cal_view_for_performance.double_click_in_the_calendar_view', 1, '#3 New event (double click)'),
        ('test_new_calendar_for_performance.collection_creation',               1, '#4 New calendar'),
        ('importing_3000_event_calendar.import',                                30, '#5 Import 3k event calendar'),
        ('startup_with_large_calendar',                                         10, '#6 Startup with 3k event calendar'),
        ('creating_new_event_from_the_file_menu_after_large_data_import.event_creation', 1, '#7 New event (menu) with 3k event calendar'),
        ('creating_a_new_event_in_the_cal_view_after_large_data_import.double_click_in_the_calendar_view', 0.5, '#8 New event (double click) with 3k event calendar'),
        ('creating_a_new_calendar_after_large_data_import.collection_creation', 1, '#9 New calendar with 3k event calendar'),
        ('switching_to_all_view_for_performance.switch_to_allview',             1, 'Switch Views'),
        ('perf_stamp_as_event.change_the_event_stamp',                          1, 'Stamp'),
        ('switching_view_after_importing_large_data.switch_to_allview',         1, 'Switch Views with 3k event calendar'),
        ('stamping_after_large_data_import.change_the_event_stamp',             0.5, 'Stamp with 3k event calendar'),
        ('scroll_calendar_one_unit.scroll_calendar_one_unit',                   0.1, 'Scroll calendar with 3k event calendar'),
        ('scrolling_a_table.scroll_table_25_scroll_units',                      0.1, 'Scroll table with 3k event calendar'),
        ('jump_from_one_week_to_another.jump_calendar_by_one_week',             0.1, 'Jump calendar by one week with 3k event calendar'),
        ('overlay_calendar.overlay_calendar',                                   1, 'Overlay calendar with 3k event calendar'),
        ('switch_calendar.switch_calendar',                                     1, 'Switch calendar with 3k event calendar'),
        #('perflargedatasharing.publish',                                        2.5, 'Publish calendar with 3k event calendar'),
        #('perflargedatasharing.subscribe',                                      2.5, 'Subscribe to calendar with 3k event calendar'),
        #('resize_app_in_calendar_mode.resize_app_in_calendar_mode',             0.1, 'Resize calendar with 3k event calendar'),
        )

    self.PerformanceTBoxes = ['p_' + platform for platform in allPlatforms]

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
        
        for (test, targetTime, name) in self.testTimeName:
          if test == testName:
            acceptable = targetTime
            break
        
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

  def generateTrendsLongdetailPages(self, tests, startdate, enddate):
    # tests { testname: { build: { date: { hour: [ (testname, itemDateTime, delta.days, buildname, hour, revision, runs, total, average) ] }}}}

      # some 'constants' to make it easier to add items to the data structure
      # without having to track down all occurances of 7 to change it to 8 :)
    DP_REVISION = 5
    DP_RUNTIME  = 6

    detailpage = []

    detailpage.append('<h1>Performance details for the previous %d days</h1>\n' % self._options['delta_days'])
    detailpage.append('<div id="detail">\n')

    graphDict = {}
    
    for (testkey, targetTime, testDisplayName) in self.testTimeName:
        testitem = tests[testkey]

        detailpage.append('<h2 id="%s">%s</h2>\n' % (testkey, testDisplayName))

        k_builds = testitem.keys()
        k_builds.sort()
        k_builds.reverse()

        graphPlatform = {}
        for p in allPlatforms:
          graphPlatform[p] = {}

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

            day_values[datekey] = (dv_count, dv_total, date_values)

          (v, n, avg) = self.standardDeviation(values)
          med = median(values) or 0.0

          if self._options['debug']:
            print "std.dev: %02.5f average: %02.3f count: %d" % (v, avg, n)

          tv_dates = []

            # now run thru again to gererate the html - but now we have averages to use for markup
          k_dates = builditem.keys()
          k_dates.sort()
          k_dates.reverse()

          detailpage.append('<h3 id="%s_%s">%s</h3>\n' % (testkey, buildkey, buildkey))
          detailpage.append('<p>Median is %2.3f and Sample Average is %2.3f and std.dev is %2.3f</p>\n' % (med, avg, v))

          for datekey in k_dates:
            dateitem = builditem[datekey]

            dv_count, dv_total, date_values = day_values[datekey]
            if dv_count > 0:
              dv_avg = dv_total / dv_count
            else:
              dv_avg = dv_total

            if dv_avg <> 0:
              c_perc = (dv_avg - avg) / dv_avg
            else:
              c_perc = 0
            c_diff = avg - dv_avg

            graphPlatform[buildkey[2:]][datekey] = median(date_values) or 0.0
            
            tv_dates.append((datekey, dv_avg, c_perc, c_diff))
            
            detailpage.append('<h4>%s-%s-%s</h4>\n' % (datekey[:4], datekey[4:6], datekey[6:8]))
            detailpage.append('<p>%d items in days sample for an average of %2.3f, median %2.3f' % (dv_count, dv_avg, graphPlatform[buildkey[2:]][datekey]))
            detailpage.append('<table>\n')
            detailpage.append('<tr><th>Time</th><th>Rev</th><th>Run Time</th><th>&Delta; %</th><th>&Delta; times</th></tr>\n')

            k_hours = dateitem.keys()
            k_hours.sort()

            lastDatapoint = None

            previousTime = 0
            for hour in k_hours:
              for datapoint in dateitem[hour]:

                current  = datapoint[DP_RUNTIME]

                if previousTime == 0:
                  previousTime = current

                c_diff = current - previousTime

                if previousTime != 0:
                  c_perc = (c_diff / previousTime) * 100
                else:
                  c_perc = 0

                s         = colorDelta(current, previousTime, 0.2)
                timeClass = self.colorTime(testkey, current, 0.2)

                #Time     | Rev # | Run Time | &Delta; % | &Delta; time
                #======================================================
                #00:43:49 | 7846  | 0.02s    |           |
                #01:32:02 | 7856  | 0.01s    | -50%      | -0.01s

                rev = datapoint[DP_REVISION]

                if lastDatapoint is not None and \
                   lastDatapoint[DP_REVISION] != rev:
                  # Create Bonsai URL since there was a revision change
                  bonsaiURL = 'http://bonsai.osafoundation.org/svnquery.cgi?treeid=default&module=all&branch=trunk&branchtype=match&sortby=Date&date=explicit&mindate=%4d-%02d-%02d+%02d:%02d:%02d&maxdate=%4d-%02d-%02d+%02d:%02d:%02d&repository=/svn/chandler' % \
                    (lastDatapoint[1].year, lastDatapoint[1].month, lastDatapoint[1].day, lastDatapoint[1].hour, lastDatapoint[1].minute, lastDatapoint[1].second,
                     datapoint[1].year, datapoint[1].month, datapoint[1].day, datapoint[1].hour, datapoint[1].minute, datapoint[1].second)
                  detailpage.append('<tr><td><a href="%s">%02d:%02d:%02d</a></td>' % \
                                    (bonsaiURL, datapoint[1].hour, datapoint[1].minute, datapoint[1].second))
                else:
                  detailpage.append('<tr><td>%02d:%02d:%02d</td>' % \
                                    (datapoint[1].hour, datapoint[1].minute, datapoint[1].second))
                
                detailpage.append('<td>%s</td><td class="number%s">%02.2fs</td>' \
                                  '<td class="%s">%+3.0f%%</td><td class="%s">%+1.2fs</td></tr>\n' %
                                  (rev, timeClass, current, s, c_perc, s, c_diff))
                                
                lastDatapoint = datapoint
                previousTime  = current

            detailpage.append('</table>\n')

        graphDict[testkey] = graphPlatform
    
    def plat2data(graphPlatform, acceptable):
      keys = []
      for p in allPlatforms:
          keys += graphPlatform[p].keys()
      dates = unique(keys)
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
    for (test, targetTime, testDisplayName) in self.testTimeName:
      graphPlatform = graphDict[test]
       
      #print  plat2data(graphPlatform, targetTime)
      graphfilename = '%d_%s.png' % (self._options['delta_days'], test)
      graphfile = os.path.join(self._options['html_data'], graphfilename)
      drawGraph(plat2data(graphPlatform, targetTime),
                allPlatforms,
                graphfile, 
                size=(264, 132), xLabel='Date')
      trendspage.append('<h2><a href="%s#%s">%s</a></h2><img src="%s" alt="graph" title="%s">' % (detailfilename, test, testDisplayName, graphfilename, testDisplayName))

    trendspage.append('</body></html>')
    detailpage.append('</div>\n')

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
      
      for (test, targetTime, testName) in self.testTimeName:
        if test == testkey:
            targetAvg = targetTime
            break
      else:
        targetAvg = 0.0

      line  = '<tr><td><a href="detail_%s.html#%s" target="_new">%s</a></td>' % (enddate, testkey, testDisplayName)
      line += '<td class="number">%2.1fs</td>' % targetAvg

      for key in allPlatforms:
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

  def generateTboxDaydetailDatPages(self, tests, startdate, enddate):
    # tests { testname: { build: { date: { hour: [ (testname, itemDateTime, delta.days, buildname, hour, revision, runtime) ] }}}}

    # This code assumes that there will only be a single buildkey (i.e. tinderbox) for each platform

      # some 'constants' to make it easier to add items to the data structure
      # without having to track down all occurances of 7 to change it to 8 :)
    DP_DATETIME = 1
    DP_REVISION = 5
    DP_RUNTIME  = 6

    detail = []
    tbox   = []
    graph  = []

    revisions = {}
    updates = {}
    currentValue = {}
    previousValue = {}
    for p in allPlatforms:
      revisions[p] = ['', '']
      updates[p] = ''
      currentValue[p] = 0
      previousValue[p] = 0

    detail.append('<h1>Performance details for the day</h1>\n')
    detail.append('<div id="detail">\n')
    detail.append('<p>Sample Date: %s-%s-%s<br/>\n' % (enddate[:4], enddate[4:6], enddate[6:8]))
    detail.append(time.strftime('<small>Generated %d %b %Y at %H%M %Z</small></p>', time.localtime()))

    for (testkey, targetTime, testDisplayName) in self.testTimeName:
      if testkey in tests.keys():
        testitem = tests[testkey]

        detail.append('<hr>\n')
        detail.append('<div class="section">\n')
        graphfile = 'day_%s.png' % testkey.replace('.', '_')
        detail.append('<img class="daygraph" src="%s" alt="graph">' % graphfile)
        detail.append('<h2 id="%s">%s</h2>\n' % (testkey, testDisplayName))

        platforms = {}
        for p in allPlatforms:
            platforms[p] = { 'stddev':   0,
                             'avg':      0,
                             'count':    0,
                             'total':    0,
                             'values':   [],
                             'timesRevs':[],
                             'revision': '' }

        for buildkey in self.PerformanceTBoxes:
          if buildkey in testitem.keys():
            builditem = testitem[buildkey]

            for p in allPlatforms:
              if p in buildkey:
                platformkey = p

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
            previousRevision = None
            lastDatapoint = None
            
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
                
                if previousRevision is not None and previousRevision != revision:
                  bonsaiURL = 'http://bonsai.osafoundation.org/svnquery.cgi?treeid=default&module=all&branch=trunk&branchtype=match&sortby=Date&date=explicit&mindate=%4d-%02d-%02d+%02d:%02d:%02d&maxdate=%4d-%02d-%02d+%02d:%02d:%02d&repository=/svn/chandler' % \
                    (lastDatapoint[1].year, lastDatapoint[1].month, lastDatapoint[1].day, lastDatapoint[1].hour, lastDatapoint[1].minute, lastDatapoint[1].second,
                     datapoint[1].year, datapoint[1].month, datapoint[1].day, datapoint[1].hour, datapoint[1].minute, datapoint[1].second)                  
                  detail.append('<tr><td><a href="%s">%02d:%02d:%02d</a></td>' %
                                (bonsaiURL, datapoint[1].hour, datapoint[1].minute, datapoint[1].second))
                else:
                  detail.append('<tr><td>%02d:%02d:%02d</td>' %
                                (datapoint[1].hour, datapoint[1].minute, datapoint[1].second))

                detail.append('<td>%s</td><td class="number%s">%02.2fs</td><td class="%s">%+3.0f%%</td><td class="%s">%+1.2fs</td></tr>\n' %
                              (revision, timeClass, current, deltaClass, c_perc, deltaClass, c_diff))

                if self._options['debug']:
                  print "%s %s %s %s %s %s %f" % (testDisplayName, platformkey, buildkey, datekey, hour, revision, current)
                
                previous = current
                previousRevision = revision
                lastDatapoint = datapoint

            (v, n, avg) = self.standardDeviation(platformdata['values'])

            #print "average: %02.5f count: %d stddev: %02.5f" % (avg, n, v)

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

        tbox.append(summaryline)

        graph += graphdata
        
        (data, plats) = platforms2GraphData(platforms,
                                            targetTime)
        #graphfile = 'day_%s.png' % testkey.replace('.', '_')
        if drawGraph(data, plats, os.path.join(self._options['html_data'],
                                               graphfile)):
            #detail.append('<img src="%s">' % graphfile)
            pass
        detail.append('</div>')
        
    detail.append('</div>\n')

    tbox.append('</table>\n</div>\n')

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
    for key in allPlatforms:
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
    tboxfile.write('<tr><th rowspan="2">Test (<a href="%s" target="_new">trends</a>)<br/>Latest results as of %s</th><th rowspan="2">0.7<br/>Target</th>' % ('trends.html', latest))
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

  def generateOutput(self, tests, startdate, enddate):
    self.generateTrendsLongdetailPages(tests, startdate, enddate)
    self.generateTboxDaydetailDatPages(tests, startdate, enddate)

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
