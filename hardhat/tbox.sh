#!/bin/bash

#
# script to run all Chandler unit tests
#
# All output is gathered into temporary log files and
# then dumped to stdout for capture if wanted
#
# Scans the chandler/ tree for any sub-directory that is named 
# "tests" and then within that directory calls RunPython for any
# file named Test*.py
#
# if CHANDLER_PERFORMANCE_TEST=yes then CATS Performance Tests are run
# if CHANDLER_FUNCTIONAL_TEST=no then CATS Functional Tests are skipped
# if CHANDLER_UNIT_TEST=no then Unit Tests are skipped
#
# For tbox operation, define TBOX=yes and if you want it to cycle define TBOX_CYCLE=yes
# tbox operation changes the meaning of the path parameter - under tbox it should point
# to the working directory (default is ~/tinderbox) and from there the chandler directory
# is calculated.
#
# In tbox mode, only the release mode is processed.
#

USAGE="Usage: `basename $0` chandler-base-path"

if [ ! -n "$1" ]; then
    if [ "$TBOX" = "yes" ]; then
        T_DIR=~/tinderbuild
        C_DIR=$T_DIR/chandler
    else
        echo $USAGE
        echo if CHANDLER_FUNCTIONAL_TEST=no then CATS Functional Tests are skipped
        echo if CHANDLER_PERFORMANCE_TEST=yes then CATS Performance Tests are run
        echo if TBOX=yes then only release mode is tested and no distribution is built
        exit 65
    fi
else
    if [ "$TBOX" = "yes" ]; then
        T_DIR="$1"
        C_DIR=$T_DIR/chandler
    else
        C_DIR="$1"
        T_DIR=$C_DIR

        if [ ! -d "$C_DIR/i18n" ]; then
            echo Error: The path [$C_DIR] given does not point to a chandler/ directory
            echo $USAGE
            exit 65
        fi
    fi
fi

if [ "$TBOX" = "yes" ]; then
    if [ "$TBOX_BUILD" = "" ]; then
        echo TBOX_BUILD environment variable must be set
    fi
    if [ "$TBOX_TREE" = "" ]; then
        echo TBOX_TREE environment variable must be set
    fi
    if [ ! -d "$T_DIR" ]; then
        mkdir "$T_DIR"
    fi
fi

if [ "$CHANDLERBIN" = "" ]
then
    CHANDLERBIN="$C_DIR"
fi

# this is needed for the short term for tests that don't init i18n
export UNIT_TESTING=True

HH_DIR=`pwd`
LOGFILES="svn.log distrib.log install.log tests.log"
MODES="release debug"

BUILDID=`date +%Y%m%d%H%M%S`
STARTEPOCH=`date +%s`
BUILDLOG=$T_DIR/tbox_$BUILDID.log

if [ -e $BUILDLOG ]; then
    rm $BUILDLOG
fi

echo - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + | tee -a $BUILDLOG
echo Started `date`                                              | tee -a $BUILDLOG
echo Setting up script environment                               | tee -a $BUILDLOG

if [ "$OSTYPE" = "cygwin" ]; then
    RUN_CHANDLER=RunChandler.bat
    RUN_PYTHON=RunPython.bat
    TBOX_UPDATE=`cygpath -w $HH_DIR/tbox_update.py`
else
    RUN_CHANDLER=RunChandler
    RUN_PYTHON=RunPython
    TBOX_UPDATE=$HH_DIR/tbox_update.py
fi

for i in $LOGFILES ; do
    if [ -e $T_DIR/$i ]; then
        rm $T_DIR/$i
    fi
    touch $T_DIR/$i
done

if [ "$TBOX" = "yes" ]; then
    python $TBOX_UPDATE -t $TBOX_TREE -b $TBOX_BUILD -s building -e $STARTEPOCH

    if [ "$CHANDLER_PERFORMANCE_TEST" = "yes" ]; then
        MODES="release"
    fi
else
      # if the debug/ path is not found, then avoid debug tests
    if [ ! -d $C_DIR/debug ]; then
        MODES="release"
        echo Skipping debug tests as $C_DIR/debug does not exist | tee -a $BUILDLOG
    fi
fi

  # each directory to exclude should be place in the EXCLUDES array
  # and a 0 value should be place in the L_EXCLUDES array
  # the EXCLUDES array is then walked and the length of the 
  # directory is calculated - beats doing it by hand and making a mistake

EXCLUDES=("$C_DIR/release" "$C_DIR/debug" "$C_DIR/tools" "$C_DIR/util" "$C_DIR/projects" "$C_DIR/plugins")
L_EXCLUDES=(0 0 0 0 0 0)
for item in 0 1 2 3 4 5 ; do
    L_EXCLUDES[$item]=${#EXCLUDES[$item]}
done

if [ "$TBOX" = "yes" ]; then
    echo Setting up Chandler environment | tee -a $BUILDLOG

    INSTALL="no"

    if [ -d $C_DIR ]; then
        cd $C_DIR
        svn up &> $T_DIR/svn.log

        if [ `wc -l < $T_DIR/svn.log` -ne "1" ]; then
            echo Source updates require install and distribution | tee -a $BUILDLOG
            INSTALL="yes"
        fi
    else
        echo Chandler install required | tee -a $BUILDLOG
        INSTALL="yes"
        cd $T_DIR
        svn co http://svn.osafoundation.org/chandler/trunk/chandler &> $T_DIR/svn.log
    fi

    if [ "$INSTALL" = "yes" ]; then
        for mode in $MODES ; do
            if [ "$mode" = "debug" ]; then
                SNAP="DEBUG=1"
            else
                SNAP=
            fi

            echo Running \"make -C $C_DIR $SNAP distrib strip\" | tee -a $BUILDLOG
            make -C $C_DIR $SNAP distrib strip &> $T_DIR/install.log

            if [ ! "$CHANDLER_PERFORMANCE_TEST" = "yes" ]; then
                echo do distribution step | tee -a $BUILDLOG
            fi
        done
    else
        echo Source has not changed - skipping install and distribution | tee -a $BUILDLOG
    fi

      # brute force remove all variations of the last line of the svn log
      # until only the revision number remains
    REVISION=`tail -n 1 $T_DIR/svn.log`
    REVISION=${REVISION/At revision /}
    REVISION=${REVISION/Updated to revision /}
    REVISION=${REVISION/Checked out revision /}
    REVISION=${REVISION/./}

      # update the revision number (only if at start of line)
    sed "s/^revision = \"[0-9]*\"/revision = \"$REVISION\"/" $C_DIR/version.py > $C_DIR/version.new
    mv -f $C_DIR/version.new $C_DIR/version.py
else
    REVISION=0000
fi

DIRS=`find $C_DIR -type d -name tests -print`
SETUPS=`find $C_DIR/projects -type f -name 'setup.py' -print`

  # this code walks thru all the dirs with "tests" in their name
  # and then compares them to the exclude dir array by
  # taking the substring of the L_EXCLUDE length value
  # if there is a match, the loop is broken and the dir is skipped

for item in $DIRS ; do
    FILEPATH=${item%/*}
    EXCLUDED=no
    for index in 0 1 2 3 4 5 ; do
        exclude=${EXCLUDES[$index]}
        len=${L_EXCLUDES[$index]}

        if [ "${FILEPATH:0:$len}" = "$exclude" ]; then
            EXCLUDED=yes
            break;
        fi
    done         
    if [ "$EXCLUDED" = "no" ]; then
        TESTDIRS="$TESTDIRS $item"
    fi
done

  # Set test result variables to initial value of "ok"
  # if any test fails it will be set to "failed" 

UNITTEST_RESULT="ok"
FUNCTEST_RESULT="ok"
PERFTEST_RESULT="ok"

  # walk thru all of the test dirs and find the test files

if [ ! "$CHANDLER_UNIT_TEST" = "no" ]; then
    PP_DIR="$C_DIR/plugins"
    C_HOME="$C_DIR"

    if [ "$OSTYPE" = "cygwin" ]; then
        PP_DIR=`cygpath -aw $PP_DIR`
        C_HOME=`cygpath -aw $C_HOME`
    fi

    for mode in $MODES ; do
        echo Running $mode unit tests | tee -a $BUILDLOG

        CONTINUE="true"
        for testdir in $TESTDIRS ; do
            TESTS=`find $testdir -name 'Test*.py' -print`

            for test in $TESTS ; do
                if [ "$CONTINUE" = "true" ]; then
                    if [ "$OSTYPE" = "cygwin" ]; then
                        TESTNAME=`cygpath -w $test`
                    else
                        TESTNAME=$test
                    fi

                    echo Running $TESTNAME | tee -a $BUILDLOG

                    cd $C_DIR
                    PARCELPATH=$PP_DIR $CHANDLERBIN/$mode/$RUN_PYTHON $TESTNAME &> $T_DIR/test.log

                    if [ "$OSTYPE" = "cygwin" ]; then
                        dos2unix $T_DIR/test.log
                    fi

                      # scan the test output for the success messge "OK"
                    RESULT=`grep '^OK' $T_DIR/test.log`

                    echo - - - - - - - - - - - - - - - - - - - - - - - - - - >> $T_DIR/tests.log
                    echo $TESTNAME [$RESULT] >> $T_DIR/tests.log
                    cat $T_DIR/test.log      >> $T_DIR/tests.log

                    if [ "$RESULT" != "OK" ]; then
                        UNITTEST_RESULT="failed"
                        CHANDLER_FUNCTIONAL_TEST="no"
                        CHANDLER_PERFORMANCE_TEST="no"
                        CONTINUE="false"
                        echo Skipping further tests due to failure | tee -a $BUILDLOG
                    fi
                fi
            done
        done

        for setup in $SETUPS ; do
            if [ "$CONTINUE" == "true" ]; then
                TESTNAME=`basename \`dirname $setup\``
                echo Running $setup | tee -a $BUILDLOG

                cd `dirname $setup`
                PARCELPATH=$PP_DIR CHANDLERHOME=$C_HOME $CHANDLERBIN/$mode/$RUN_PYTHON `basename $setup` test &> $T_DIR/test.log

                if [ "$OSTYPE" = "cygwin" ]; then
                    dos2unix $T_DIR/test.log
                fi

                # scan the test output for the success messge "OK"
                RESULT=`grep '^OK' $T_DIR/test.log`

                echo - - - - - - - - - - - - - - - - - - - - - - - - - - >> $T_DIR/tests.log
                echo $TESTNAME [$RESULT] >> $T_DIR/tests.log
                cat $T_DIR/test.log      >> $T_DIR/tests.log

                if [ "$RESULT" != "OK" ]; then
                    UNITTEST_RESULT="failed"
                    CHANDLER_FUNCTIONAL_TEST="no"
                    CHANDLER_PERFORMANCE_TEST="no"
                    CONTINUE="false"
                    echo Skipping further tests due to failure | tee -a $BUILDLOG
                fi
            fi
            cd $C_DIR
        done

          # if Functional Tests are needed - walk the CATS directory
          # and create a list of all valid tests

        echo Running $mode functional tests | tee -a $BUILDLOG

        if [ ! "$CHANDLER_FUNCTIONAL_TEST" = "no" ]; then
            test="$C_DIR/tools/cats/Functional/FunctionalTestSuite.py"

            PP_DIR="$C_DIR/tools/QATestScripts/DataFiles"

            if [ "$OSTYPE" = "cygwin" ]; then
                TESTNAME=`cygpath -w $test`
                P_DIR=`cygpath -w $C_DIR`
                PP_DIR=`cygpath -w $PP_DIR`
            else
                TESTNAME=$test
                P_DIR=$C_DIR
            fi

            echo Running $TESTNAME | tee -a $BUILDLOG

            cd $C_DIR
            $CHANDLERBIN/$mode/$RUN_CHANDLER --create --nocatch --profileDir="$P_DIR" --parcelPath="$PP_DIR" --scriptTimeout=720  --chandlerTestMask=0 --chandlerTestDebug=1 --scriptFile="$TESTNAME" --chandlerTestLogfile=FunctionalTestSuite.log &> $T_DIR/test.log

              # functional tests output a #TINDERBOX# Status = PASSED that we can scan for
            RESULT=`grep "#TINDERBOX# Status = PASSED" $T_DIR/test.log`

            echo - - - - - - - - - - - - - - - - - - - - - - - - - - >> $T_DIR/tests.log
            echo $TESTNAME [$RESULT] >> $T_DIR/tests.log
            cat $T_DIR/test.log      >> $T_DIR/tests.log

            if [ "$RESULT" != "#TINDERBOX# Status = PASSED" ]; then
                FUNCTEST_RESULT="failed"
                CHANDLER_PERFORMANCE_TEST="no"
            fi
        fi
    done
fi

  # if Performance Tests are needed - walk the CATS directory
  # and create a list of all valid tests

if [ "$CHANDLER_PERFORMANCE_TEST" = "yes" ]; then
    echo Running performance tests | tee -a $BUILDLOG

    # How many times to run each test
    # NOTE: Currently the median calculations assume 3 runs, so if you
    # change this you will also have to change the median calculations.
    RUNS="1 2 3"

    TESTS=`find $C_DIR/tools/QATestScripts/Performance -name 'Perf*.py' -print`

    rm -fr $C_DIR/__repository__.0*
    REPO=$C_DIR/__repository__.001
    if [ "$OSTYPE" = "cygwin" ]; then
        REPO=`cygpath -w $REPO`
    fi

    for test in $TESTS ; do
        # Don't run large data tests here
        if [ `echo $test | grep -v PerfLargeData` ]; then

            TESTNAME=$test
            P_DIR=$C_DIR
            if [ "$OSTYPE" = "cygwin" ]; then
                TESTNAME=`cygpath -w $TESTNAME`
                P_DIR=`cygpath -w $P_DIR`
            fi

            echo Running $TESTNAME | tee -a $BUILDLOG

            cd $C_DIR

            for run in $RUNS ; do 
                T_LOG="$T_DIR/time$run.log"
                if [ "$OSTYPE" = "cygwin" ]; then
                    T_LOG=`cygpath -w $T_LOG`
                fi
                $CHANDLERBIN/release/$RUN_CHANDLER --create --nocatch --profileDir="$P_DIR" --catsPerfLog="$T_LOG" --scriptTimeout=600 --scriptFile="$TESTNAME" &> $T_DIR/test$run.log
                echo `<"$T_LOG"` | tee -a $BUILDLOG
            done

            # Pick the median
            MEDIANTIME=`cat $T_DIR/time1.log $T_DIR/time2.log $T_DIR/time3.log | sort -n | head -n 2 | tail -n 1`        
            for run in $RUNS ; do
                if [ `cat $T_DIR/time$run.log` = $MEDIANTIME ]; then
                    cat $T_DIR/test$run.log > $T_DIR/test.log
                    break
                fi
            done

              # performance tests output a #TINDERBOX# Status = PASSED that we can scan for
            RESULT=`grep "#TINDERBOX# Status = PASSED" $T_DIR/test.log`

            echo - - - - - - - - - - - - - - - - - - - - - - - - - - >> $T_DIR/tests.log
            echo $TESTNAME [$RESULT] >> $T_DIR/tests.log
            cat $T_DIR/test.log      >> $T_DIR/tests.log

            if [ "$RESULT" != "#TINDERBOX# Status = PASSED" ]; then
                PERFTEST_RESULT="failed"
            fi
        fi
    done

    if [ "$RESULT" = "" ]; then
        for test in $TESTS ; do
            FAILED_TESTS="$FAILED_TESTS $test"
        done
    else
        # Run all tests with restored large repository
        for test in $TESTS ; do
            # Only run the large data tests
            if [ `echo $test | grep PerfLargeData` ]; then
                TESTNAME=$test
                P_DIR=$C_DIR
                if [ "$OSTYPE" = "cygwin" ]; then
                    TESTNAME=`cygpath -w $TESTNAME`
                    P_DIR=`cygpath -w $P_DIR`
                fi

                echo Running $TESTNAME | tee -a $BUILDLOG

                cd $C_DIR

                for run in $RUNS ; do 
                    T_LOG="$T_DIR/time$run.log"
                    if [ "$OSTYPE" = "cygwin" ]; then
                        T_LOG=`cygpath -w $T_LOG`
                    fi
                    $CHANDLERBIN/release/$RUN_CHANDLER --restore="$REPO" --nocatch --profileDir="$P_DIR" --catsPerfLog="$T_LOG" --scriptTimeout=600 --scriptFile="$TESTNAME" &> $T_DIR/test$run.log
                    echo `<"$T_LOG"` | tee -a $BUILDLOG
                done

                # Pick the median
                MEDIANTIME=`cat $T_DIR/time1.log $T_DIR/time2.log $T_DIR/time3.log | sort -n | head -n 2 | tail -n 1`        
                for run in $RUNS ; do
                    if [ `cat $T_DIR/time$run.log` = $MEDIANTIME ]; then
                        cat $T_DIR/test$run.log > $T_DIR/test.log
                        break
                    fi
                done

                  # performance tests output a #TINDERBOX# Status = PASSED that we can scan for
                RESULT=`grep "#TINDERBOX# Status = PASSED" $T_DIR/test.log`

                echo - - - - - - - - - - - - - - - - - - - - - - - - - - >> $T_DIR/tests.log
                echo $TESTNAME [$RESULT] >> $T_DIR/tests.log
                cat $T_DIR/test.log      >> $T_DIR/tests.log

                if [ "$RESULT" != "#TINDERBOX# Status = PASSED" ]; then
                    PERFTEST_RESULT="failed"
                fi
            fi
        done
    fi

    echo Running startup time tests | tee -a $BUILDLOG

    if [ "$OSTYPE" = "cygwin" ]; then
        TESTNAME=`cygpath -w $C_DIR/tools/QATestScripts/Performance/end.py`
        CREATEREPO=`cygpath -w $C_DIR/tools/QATestScripts/Performance/quit.py`
        P_DIR=`cygpath -w $C_DIR`
        TIME='time.exe --format=%e'
    else
        TESTNAME=$C_DIR/tools/QATestScripts/Performance/end.py
        CREATEREPO=$C_DIR/tools/QATestScripts/Performance/quit.py
        P_DIR=$C_DIR
        if [ "${OSTYPE:0:6}" = "darwin" ]; then
            # NOTE: gtime is not part of OS X, you need to compile one
            # yourself (get source from http://directory.fsf.org/time.html)
            # or get it from darwinports project.
            TIME='gtime --format=%e'
        else
            TIME='/usr/bin/time --format=%e'
        fi
    fi

    cd $C_DIR

    echo Creating new empty repository | tee -a $BUILDLOG
    $CHANDLERBIN/release/$RUN_CHANDLER --create --nocatch --profileDir="$P_DIR" --scriptTimeout=600 --scriptFile="$CREATEREPO" &> $T_DIR/test.log

    echo Timing startup | tee -a $BUILDLOG
    for run in $RUNS ; do
        $TIME -o $T_DIR/start1.$run.log $CHANDLERBIN/release/$RUN_CHANDLER --nocatch --profileDir="$P_DIR" --scriptTimeout=600 --scriptFile="$TESTNAME" &> $T_DIR/test.log
        cat $T_DIR/start1.$run.log | sed "s/^Command exited with non-zero status [0-9]\+ //" > $T_DIR/test.log
        cat $T_DIR/test.log > $T_DIR/start1.$run.log
        echo `<"$T_DIR/start1.$run.log"` | tee -a $BUILDLOG
    done

    echo Creating new large repository | tee -a $BUILDLOG
    $CHANDLERBIN/release/$RUN_CHANDLER --restore="$REPO" --nocatch --profileDir="$P_DIR" --scriptTimeout=600 --scriptFile="$CREATEREPO" &> $T_DIR/test.log

    echo Timing startup | tee -a $BUILDLOG
    for run in $RUNS ; do
        $TIME -o $T_DIR/start6.$run.log $CHANDLERBIN/release/$RUN_CHANDLER --profileDir="$P_DIR" --nocatch --scriptTimeout=600 --scriptFile="$TESTNAME" &> $T_DIR/test.log
        cat $T_DIR/start6.$run.log | sed "s/^Command exited with non-zero status [0-9]\+ //" > $T_DIR/test.log
        cat $T_DIR/test.log > $T_DIR/start6.$run.log
        echo `<"$T_DIR/start6.$run.log"` | tee -a $BUILDLOG
    done

    echo Getting medians from startup runs | tee -a $BUILDLOG

    STARTUP=`cat $T_DIR/start1.1.log $T_DIR/start1.2.log $T_DIR/start1.3.log | sort -n | head -n 2 | tail -n 1`        
    STARTUP_LARGE=`cat $T_DIR/start6.1.log $T_DIR/start6.2.log $T_DIR/start6.3.log | sort -n | head -n 2 | tail -n 1`

    echo Printing results | tee -a $BUILDLOG

    echo - - - - - - - - - - - - - - - - - - - - - - - - - - >> $T_DIR/tests.log
    echo $TESTNAME \[\#TINDERBOX\# Status = PASSED\]         >> $T_DIR/tests.log
    echo OSAF_QA: Startup \| $REVISION \| $STARTUP           >> $T_DIR/tests.log
    echo \#TINDERBOX\# Testname = Startup                    >> $T_DIR/tests.log
    echo \#TINDERBOX\# Status = PASSED                       >> $T_DIR/tests.log
    echo \#TINDERBOX\# Time elapsed = $STARTUP \(seconds\)   >> $T_DIR/tests.log

    echo - - - - - - - - - - - - - - - - - - - - - - - - - -                 >> $T_DIR/tests.log
    echo $TESTNAME \[\#TINDERBOX\# Status = PASSED\]                         >> $T_DIR/tests.log
    echo OSAF_QA: Startup_with_large_calendar \| $REVISION \| $STARTUP_LARGE >> $T_DIR/tests.log
    echo \#TINDERBOX\# Testname = Startup_with_large_calendar                >> $T_DIR/tests.log
    echo \#TINDERBOX\# Status = PASSED                                       >> $T_DIR/tests.log
    echo \#TINDERBOX\# Time elapsed = $STARTUP_LARGE \(seconds\)             >> $T_DIR/tests.log

fi

echo - - - - svn.log - - - - - - - - - - - - - - - - - - - - - - | tee -a $BUILDLOG
cat $T_DIR/svn.log                                               | tee -a $BUILDLOG
echo - - - - install.log - - - - - - - - - - - - - - - - - - - - | tee -a $BUILDLOG
cat $T_DIR/install.log                                           | tee -a $BUILDLOG
echo - - - - distrib.log - - - - - - - - - - - - - - - - - - - - | tee -a $BUILDLOG
cat $T_DIR/distrib.log                                           | tee -a $BUILDLOG
echo - - - - tests.log - - - - - - - - - - - - - - - - - - - - - | tee -a $BUILDLOG
cat $T_DIR/tests.log                                             | tee -a $BUILDLOG
echo - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + | tee -a $BUILDLOG

if [ "$TBOX" = "yes" ]; then
    echo Unit Tests [$UNITTEST_RESULT] Functional [$FUNCTEST_RESULT] Performance [$PERFTEST_RESULT] | tee -a $BUILDLOG

    if [ "$UNITTEST_RESULT" = "failed" -o "$FUNCTEST_RESULT" = "failed" -o "$PERFTEST_RESULT" = "failed" ]; then
        TBOX_STATUS=test_failed
    else
        TBOX_STATUS=success
    fi
    if [ "$OSTYPE" = "cygwin" ]; then
        LOGPATH=`cygpath -w $T_DIR/`
    else
        LOGPATH=$T_DIR/
    fi

    python $TBOX_UPDATE -t $TBOX_TREE -b $TBOX_BUILD -s $TBOX_STATUS -f tbox_$BUILDID.log -p $LOGPATH -e $STARTEPOCH
fi

