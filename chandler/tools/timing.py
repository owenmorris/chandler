"""
@copyright: Copyright (c) 2004 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

"""
The tools.timing module is a simple way to time critical sections of your
code.  By placing begin() and end() calls around the sections you want to time,
you can get a report of how many times that section was called, total time,
and average time -- a lightweight profiler.  The begin() and end() methods
take a name parameter that is a string which describes the operation you
are timing -- make sure they match! -- that will appear in the report printed
by the results() method.

Example:

    import tools.timing

    def myFunction():
        [... uninteresting python code here ...]

        tools.timing.begin("Creating widgets")
        [... interesting python code here ...]
        tools.timing.end("Creating widgets")

        [... uninteresting python code here ...]

        tools.timing.begin("Assigning widgets")
        [... interesting python code here ...]
        tools.timing.end("Assigning widgets")

        [... uninteresting python code here ...]

    [... later ...]
    timing.tools.results()  # prints out the report

    Operation                       Count  Total    Avg
    ------------------------------ ------ ------ ------
    Assigning widgets                 730  3.170  0.004
    Creating widgets                  730  5.259  0.007
    ------------------------------ ------ ------ ------
    Totals:                          1460  8.429  0.006


Gotchas:

- Recursion isn't handled (you will get an assert if you try to call begin()
on the same label without an intervening end())
- The grand total will be inflated if any of the timed sections are nested.
"""

import time

trackers = {}

class Tracker(object):

    def __init__(self, name):
        self.name = name
        self.count = 0
        self.totalTime = 0.0
        self.prevBeginTime = None

    def begin(self):
        if self.prevBeginTime is not None:
            print "Begin called without twice without intervening end %s" % self.name
            # raise "Begin called without twice without intervening end %s" % self.name
        self.prevBeginTime = time.time()
        self.count += 1

    def end(self):
        if self.prevBeginTime is None:
            print "End called without a Begin on %s" % self.name
            # raise "End called without a Begin on %s" % self.name
        duration = time.time() - self.prevBeginTime
        self.totalTime += duration
        self.prevBeginTime = None

    def results(self):
        return (self.name, self.count, self.totalTime, self.totalTime / self.count)

def begin(name):
    if not trackers.has_key(name):
        trackers[name] = Tracker(name)
    trackers[name].begin()

def end(name):
    if not trackers.has_key(name):
        print "End called without a Begin on %s" % name
        # raise "End called without a Begin on %s" % name
    trackers[name].end()

def reset():
    global trackers
    trackers = {}
    totalCounts = 0
    totalTime = 0.0

def results():
    keys = trackers.keys()
    keys.sort()
    totalCounts = 0
    totalTime = 0.0
    bannerFormat = "         %-30s   %6s   %8s   %8s"
    lines = bannerFormat % \
     ("-----------------------------", "------", "--------", "--------")
    dataFormat = "OSAF_QA: %-30s | %6d | %6.5f | %6.5f"
    print bannerFormat % ("Operation", "Count", "Total", "Avg")
    print lines
    for key in keys:
        (name, count, time, avg) = trackers[key].results()
        totalCounts += count
        totalTime += time
        print dataFormat % (name, count, time, avg)
    print lines
    print dataFormat % ("Totals:", totalCounts, totalTime, totalTime/totalCounts)
