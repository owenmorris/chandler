Full instructions on how to run performance tests are on the wiki at:

  http://wiki.osafoundation.org/Projects/RunningPerformanceTests

do_tests.sh -p runs all performance tests that start with Perf*. The script
will also run the startup performance tests.

*LargeData* files must be run with a restored large repository (which is
created by PerfImportCalendar.py). Other Perf* tests are self contained and
can be run as is.