#!/usr/bin/env python
# vi:ts=2 sw=2 nofen

__author__       = "Mike Taylor <bear@code-bear.com>"
__contributors__ = []
__copyright__    = "Copyright (c) 2004,2005 Mike Taylor"
__license__      = "BSD"
__version__      = "1.0"
__svn__          = "$Id$"


import sys, os, string, datetime, time, math
import tarfile
import ConfigParser, optparse

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
                     }

    self.loadConfiguration()

    self.verbose = self._options['verbose']

    self.SummaryTests = [#('', '#1 Startup'),
                         ('new_event_from_file_menu_for_performance',                      '#2 New event (menu)'),
                         ('new_event_by_double_clicking_in_the_cal_view_for_performance',  '#3 New event (double click)'),
                         ('test_new_calendar_for_performance',                             '#4 New calendar'),
                         ('importing_3000_event_calendar',                                 '#5 Import 3000 event calendar'),
                         #('', '#6'),
                         ('Creating_new_event_from_the_File_Menu_after_large_data_import', '#7 New event (menu) with 3000 event calendar'),
                         ('Creating_a_new_event_in_the_Cal_view_after_large_data_import',  '#8 New event (double click) with 3000 event calendar'),
                         ('Creating_a_new_calendar_after_large_data_import',               '#9 New calendar with 3000 event calendar'),
                         ('switching_to_all_view_for_performance',                         'Switch Views'),
                         ('perf_stamp_as_event',                                           'Stamp'),
                         ('Switching_view_after_importing_large_data',                     'Switch Views with 3000 event calendar'),
                         ('Stamping_after_large_data_import',                              'Stamp with 3000 event calendar'),
                        ]

      # all times are in seconds
    self.SummaryTargets = {#'': 10, 
                           'new_event_from_file_menu_for_performance':                      1,
                           'new_event_by_double_clicking_in_the_cal_view_for_performance':  1,
                           'test_new_calendar_for_performance':                             1,
                           'importing_3000_event_calendar':                                 30,
                           #'': 1,
                           'creating_new_event_from_the_file_menu_after_large_data_import': 1,
                           'creating_a_new_event_in_the_cal_view_after_large_data_import':  1,
                           'creating_a_new_calendar_after_large_data_import':               1,
                           'switching_to_all_view_for_performance':                         1,
                           'perf_stamp_as_event':                                           1,
                           'Switching_view_after_importing_large_data':                     1,
                           'Stamping_after_large_data_import':                              1,
                          }

    self.PerformanceTBoxes = ['p_win', 'p_osx', 'p_linux']

    if self._options['debug']:
      print 'Configuration Values:'
      for key in self._options:
        print '\t%s: [%r]' % (key, self._options[key])

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
      print 'loading %s' % self._options['configfile']

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
    tarfiles  = {}

    perfs = os.listdir(self._options['tbox_data'])

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
          buildname = item[1]

            # another hack - check to see if the buildname is one of the performance
            # only tboxes.  They only run release mode tests so will not have any
            # debug data so the starting point will be the first line
          if buildname.lower().startswith('p_'):
            p = 0
          else:
            p = p / 2

          print '%s: %d %d' % (buildname, len(lines), p)

          for line in lines[p:]:
            item = string.split(string.lower(line[:-1]), '|')

              # each line of a .perf file has the following format
              # treename | buildname | date | time | testname | svn rev # | run count | total time | average time

            if not datafiles.has_key(buildname):
              datafiles[buildname] = file(os.path.join(self._options['perf_data'], ('%s.dat' % buildname)), 'a')

              tarname = os.path.join(self._options['perf_data'], '%s.tar' % buildname)

              if os.path.isfile(tarname):
                tarfiles[buildname] = tarfile.open(tarname, 'a')
              else:
                tarfiles[buildname] = tarfile.open(tarname, 'w')

            datafiles[buildname].write('%s\n' % string.join(item[2:], '|'))

          if tarfiles.has_key(buildname):
            tarfiles[buildname].add(perffile)

        if self._options['cleanup']:
          os.remove(perffile)

    for key in datafiles:
      datafiles[key].close()

    for key in tarfiles:
      tarfiles[key].close()

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
          (itemDate, itemTime, testname, revision, runs, total, average) = string.split(string.lower(line[:-1]), '|')

          itemDateTime = datetime.datetime(int(itemDate[:4]), int(itemDate[4:6]), int(itemDate[6:8]), int(itemTime[:2]), int(itemTime[2:4]), int(itemTime[4:6]))

          delta = today - itemDateTime

          if delta.days < 8:
            testname = string.strip(testname)
            hour     = itemTime[:2]
            runs     = int(runs)
            total    = float(total)
            average  = float(average)

            if itemDate < startdate:
              startdate = itemDate

            if itemDate > enddate:
              enddate = itemDate

              # data points are put into test and date buckets
              #   each test has a dictionary of builds
              #   each build has a dictionary of dates
              #   each date has a dictionary of times (hour resolution)
              #   each time is a list of data points
              # tests { testname: { build: { date: { hour: [ (testname, itemDateTime, delta.days, buildname, revision, runs, total, average) ] }}}}

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

            dateitem[hour].append((testname, itemDateTime, delta.days, buildname, hour, revision, runs, total, average))

    return (tests, startdate, enddate)

  def variance(self, values):
    n   = len(values)
    v   = 0
    avg = 0

    if n > 1:
      sum = 0

        # algorithm is from http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        # first pass to calculate average of all data points
        # Note: Code modified on 3 Oct 2005 from the original based on a code review by
        #       Philippe and Grant as they both pointed out the single pass method and
        #       Philippe pointed out an error in my implementation that was causing
        #       erronious results

      for item in values:
          avg = avg + item
          sum = sum + item*item

      avg = avg / n
      x   = (sum - n*avg*avg) / n*n

      if x < 0:
          x = abs(x)

      v = math.sqrt(x)

    else:
      avg = values[0]

    return (v, n, avg)


  def generateVarianceDetailPage(self, pagename, tests, startdate, enddate):
    # tests { testname: { build: { date: { hour: [ (testname, itemDateTime, delta.days, buildname, hour, revision, runs, total, average) ] }}}}

      # some 'constants' to make it easier to add items to the data structure
      # without having to track down all occurances of 7 to change it to 8 :)
    DP_REVISION = 5
    DP_RUNS     = 6
    DP_TOTAL    = 7
    DP_AVERAGE  = 8

    indexpage  = []
    detailpage = []

    indexpage.append('<h1>Performance Variance for the previous 7 days</h1>\n')
    indexpage.append('<div id="summary">\n')
    indexpage.append('<p>From %s-%s-%s to %s-%s-%s<br/>\n' % (startdate[:4], startdate[4:6], startdate[6:8],
                                                              enddate[:4], enddate[4:6], enddate[6:8]))
    indexpage.append(time.strftime('<small>Generated %d %b %Y at %H%M %Z</small></p>', time.localtime()))

    detailpage.append('<h1>Performance Variance for the previous 7 days</h1>\n')
    detailpage.append('<div id="detail">\n')

    for testkey in tests.keys():
      if testkey <> 'totals:':
        testitem = tests[testkey]

        indexpage.append('<h2>%s</h2>\n' % testkey)
        detailpage.append('<h2>%s</h2>\n' % testkey)

        k_builds = testitem.keys()
        k_builds.sort()
        k_builds.reverse()

        indexpage.append('<table>\n')
        indexpage.append('<colgroup><col class="build"></col><col></col><col class="size"></col><col class="avg"></col></colgroup>\n')
        indexpage.append('<tr><th></th><th></th><th colspan="2">Sample</th><th colspan="9">Difference of Sample Average to Prior Day (avg - pd)</th>')
        indexpage.append('<tr><th>Build</th><th>Variance</th><th>Count</th><th>Average</th><th>0</th><th>-1</th><th>-2</th><th>-3</th><th>-4</th><th>-5</th><th>-6</th><th>-7</th><th>-8</th></tr>\n')

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
                #print "%s %s %s %s %f" % (testkey, buildkey, datekey, hour, datapoint[DP_AVERAGE])
                values.append(datapoint[DP_AVERAGE])
                date_values.append(datapoint[DP_AVERAGE])

            dv_count = len(date_values)
            dv_total = 0

            if dv_count > 0:
              for item in date_values:
                dv_total = dv_total + item

            day_values[datekey] = (dv_count, dv_total)

          (v, n, avg) = self.variance(values)

          #print "variance: %02.5f average: %02.3f count: %d" % (v, avg, n)

          tv_dates = []

            # now run thru again to gererate the html - but now we have averages to use for markup
          k_dates = builditem.keys()
          k_dates.sort()
          k_dates.reverse()

          detailpage.append('<h3 id="%s_%s">%s</h3>\n' % (testkey, buildkey, buildkey))
          detailpage.append('<p>Sample Average is %2.3f and variance is %2.3f</p>\n' % (avg, v))
          detailpage.append('<!-- avg: %02.5f count: %d var: %02.5f -->\n' % (avg, n, v))

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

            tv_dates.append((datekey, dv_avg, c_perc, c_diff))

            detailpage.append('<h4>%s-%s-%s</h4>\n' % (datekey[:4], datekey[4:6], datekey[6:8]))
            detailpage.append('<p>%d items in days sample for an average of %2.3f' % (dv_count, dv_avg))
            detailpage.append('<table>\n')
            detailpage.append('<colgroup><col class="time"></col><col class="run"></col><col class="avg"></col></colgroup>\n')
            detailpage.append('<tr><th></th><th></th><th></th><th></th><th colspan="2">Change (Day)</th>')
            detailpage.append('<tr><th>Time</th><th>Runs</th><th>Average</th><th>Percent</th><th>Percent</th><th>Value</th></tr>\n')

            k_hours = dateitem.keys()
            k_hours.sort()

            for hour in k_hours:
              for datapoint in dateitem[hour]:
                s    = 'ok'
                perc = 0

                if avg > 0:
                  perc = abs((avg - datapoint[DP_AVERAGE]) / avg) * 100

                  if perc > 66:
                    s = 'alert'
                  else:
                    if perc > 33:
                      s = 'warn'

                if dv_avg <> 0:
                  c_perc = (dv_avg - datapoint[DP_AVERAGE]) / dv_avg
                c_diff = datapoint[DP_AVERAGE] - dv_avg

                detailpage.append('<tr><td>%02d:%02d:%02d</td><td class="number_left">%d</td><td class="%s">%02.3f</td>' \
                                  '<td class="number">%d</td><td class="number_left">%02.3f</td><td class="number">%02.3f</td></tr>\n' %
                                  (datapoint[1].hour, datapoint[1].minute, datapoint[1].second,
                                   datapoint[DP_RUNS], s, datapoint[DP_AVERAGE], perc, c_perc, c_diff))
                detailpage.append('<!-- value: %02.5f count: %d avg: %02.5f %02.5f c_perc: %02.5f c_diff: %02.5f -->\n' %
                                  (datapoint[DP_AVERAGE], n, avg, perc, c_perc, c_diff))

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

    detailfile = file(os.path.join(self._options['html_data'], 'detail_%s_%s.html' % (startdate, enddate)), 'w')

    if os.path.isfile(os.path.join(self._options['perf_data'], 'detail.html.header')):
      for line in file(os.path.join(self._options['perf_data'], 'detail.html.header')):
        detailfile.write(line)

    for line in detailpage:
      detailfile.write(line)

    if os.path.isfile(os.path.join(self._options['perf_data'], 'detail.html.footer')):
      for line in file(os.path.join(self._options['perf_data'], 'detail.html.footer')):
        detailfile.write(line)

    detailfile.close()


  def _generateSummaryDetailLine(self, platforms, testkey, enddate, testDisplayName, previousTargets):
      line  = '<tr><td><a href="detail_%s.html#%s" target="_new">%s</a></td>' % (enddate, testkey, testDisplayName)
      graph = []
      
      if testkey in self.SummaryTargets.keys():
        targetAvg = self.SummaryTargets[testkey]
      else:
        targetAvg = 0.0

      for key in ['win', 'osx', 'linux']:
        avg      = platforms[key]['avg'] * 60 # convert to seconds
        revision = platforms[key]['revision']
        variance = platforms[key]['var']

        previous = previousTargets[key] * 60 #convert to seconds

        c_diff = previous - avg

        if previous <> 0:
          c_perc = (c_diff / previous) * 100
        else:
          c_perc = 0

#If the result falls within the standard deviation (m5-std dev < current
#< m5+std dev), don't color the results. After all, we don't really know
#if it is a real change or just noise.
#
#If the test has gotten faster than the std dev limit, color it green.
#If the test has gotten slower, but less than 10%, color it orange.
#If the test has gotten slower by more than 10%, color it red.

        if ((previous - variance) < avg) and (avg < (previous + variance)):
          s = 'ok'
        else:
          if c_perc < 0.0:
            if abs(c_perc) > self._options['p_alert']:
              s = 'alert'
            else:
              s = 'warn'
          else:
              if c_perc > 10.0:
                  s = 'good'
              else:
                  s = 'ok'

        graph.append('%s | %s | %s | %s | %02.3f | %02.3f | %03.1f\n' % (enddate, key, testkey, revision, avg, c_diff, c_perc))

        #print key, testkey, targetAvg, avg, c_perc, c_diff, s, variance

        line += '<td class="number">%2.0fs</td>' % targetAvg
        line += '<td class="number">%2.2fs</td>' % avg
        line += '<td class="%s">%+3.0f%%</td>' % (s, c_perc)
        line += '<td class="%s">%+1.2fs</td>' % (s, c_diff)
        line += '<td>%01.2fs</td>' % variance

      line += '</tr>\n'

      return (line, graph)

  def generateSummaryPage(self, pagename, tests, startdate, enddate):
    # tests { testname: { build: { date: { hour: [ (testname, itemDateTime, delta.days, buildname, hour, revision, runs, total, average) ] }}}}

    # This code assumes that there will only be a single buildkey (i.e. tinderbox) for each platform

      # some 'constants' to make it easier to add items to the data structure
      # without having to track down all occurances of 7 to change it to 8 :)
    DP_REVISION = 5
    DP_RUNS     = 6
    DP_TOTAL    = 7
    DP_AVERAGE  = 8

    page   = []
    detail = []
    tbox   = []
    graph  = []

    revisions = { 'osx':   ['', ''],
                  'linux': ['', ''],
                  'win':   ['', ''], }

    previousRun = { 'osx':   0,
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

        detail.append('<h2>%s: %s</h2>\n' % (testDisplayName, testkey))

        platforms = { 'osx':   { 'var':      0,
                                 'avg':      0,
                                 'count':    0,
                                 'total':    0,
                                 'values':   [],
                                 'revision': '' },
                      'linux': { 'var':      0,
                                 'avg':      0,
                                 'count':    0,
                                 'total':    0,
                                 'values':   [],
                                 'revision': '' },
                      'win':   { 'var':      0,
                                 'avg':      0,
                                 'count':    0,
                                 'total':    0,
                                 'values':   [],
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
            detail.append('<tr><th>Time</th><th>Rev #</th><th>Runs</th><th>Median</th></tr>\n')

            for hour in k_hours:
              for datapoint in dateitem[hour]:
                revision =  datapoint[DP_REVISION]
                dv_total += datapoint[DP_AVERAGE]

                platformdata['values'].append(datapoint[DP_AVERAGE])

                detail.append('<tr><td>%02d:%02d:%02d</td><td>%s</td><td class="number">%d</td><td class="number">%02.5f</td></tr>\n' %
                              (datapoint[1].hour, datapoint[1].minute, datapoint[1].second,
                               revision, datapoint[DP_RUNS], datapoint[DP_AVERAGE]))
                detail.append('<!-- revision %s runs %d time %02.5f -->\n' % (revision, datapoint[DP_RUNS], datapoint[DP_AVERAGE]))

                print "%s %s %s %s %s %s %f" % (testDisplayName, platformkey, buildkey, datekey, hour, revision, datapoint[DP_AVERAGE])

            (v, n, avg) = self.variance(platformdata['values'])

            #print "average: %02.5f count: %d variance: %02.5f" % (avg, n, v)
            page.append('<!-- build: %s avg: %02.5f count: %d variance: %02.5f -->\n' % (buildkey, avg, n, v))

            detail.append('</table>\n')
            detail.append('<p>%d items in days sample for an median of %02.5f and a variance of %02.5f</p>\n' % (n, avg, v))

            platformdata['var']      = v
            platformdata['avg']      = avg
            platformdata['total']    = dv_total
            platformdata['count']    = n
            platformdata['revision'] = revision

            if len(k_hours) > 2:
                revisions[platformkey] = [revision, dateitem[k_hours[-2]][0][DP_REVISION]]
            else:
                revisions[platformkey] = [revision, revision]

            previousRun[platformkey] = dateitem[k_hours[-1]][0][DP_AVERAGE]

        (summaryline, graphdata) = self._generateSummaryDetailLine(platforms, testkey, enddate, testDisplayName, previousRun)

        page.append(summaryline)
        tbox.append(summaryline)

        graph += graphdata

    #print revisions

    page.append('</table>\n')
                                      
    page.append('<p>The Test name link will take you to the detail information that was \n')
    page.append('used to generate the summary numbers for that test<br/>\n')
    page.append('The original <a href="variance.html">variance page</a> shows the other test \n')
    page.append('data that is captured and the variance data for the last 7 days</p>\n')

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

    tboxfile.write('<div id="tbox">\n')
    tboxfile.write('<table>\n')
    tboxfile.write('<tr><th></th>')
    tboxfile.write('<th colspan="5">Windows (r %s vs %s)</th>' % (revisions['win'][0], revisions['win'][1]))
    tboxfile.write('<th colspan="5">OS X (r %s vs %s)</th>' % (revisions['osx'][0], revisions['osx'][1]))
    tboxfile.write('<th colspan="5">Linux (r %s vs %s)</th></tr>\n' % (revisions['linux'][0], revisions['linux'][1]))
    tboxfile.write('<tr><th>Test</th>')
    tboxfile.write('<th>0.6 Target</th><th>time</th><th>&Delta; %</th><th>&Delta; time</th><th>std.dev</th>')
    tboxfile.write('<th>0.6 Target</th><th>time</th><th>&Delta; %</th><th>&Delta; time</th><th>std.dev</th>')
    tboxfile.write('<th>0.6 Target</th><th>time</th><th>&Delta; %</th><th>&Delta; time</th><th>std.dev</th></tr>\n')

    if os.path.isfile(os.path.join(self._options['perf_data'], 'tbox.html.header')):
      for line in file(os.path.join(self._options['perf_data'], 'tbox.html.header')):
        tboxfile.write(line)

    for line in tbox:
      tboxfile.write(line)

    if os.path.isfile(os.path.join(self._options['perf_data'], 'tbox.html.footer')):
      for line in file(os.path.join(self._options['perf_data'], 'tbox.html.footer')):
        tboxfile.write(line)

    tboxfile.close()


  def generateOutput(self, tests, startdate, enddate):
    self.generateVarianceDetailPage('variance.html', tests, startdate, enddate)
    self.generateSummaryPage('index.html', tests, startdate, enddate)

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
