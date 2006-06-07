#!/bin/bash

#
# script to run all Chandler unit, functional and performance tests
#
# Scans the chandler/ tree for any sub-directory that is named
# "tests" and then within that directory calls RunPython for any
# file named Test*.py
#
# if CHANDLER_PERFORMANCE_TEST=yes then CATS Performance Tests are run
# if CHANDLER_FUNCTIONAL_TEST=no then CATS Functional Tests are skipped
#

NO_ARGS=0
E_OPTERROR=65

USAGE="Usage: `basename $0` -fpu [-m debug|release] [-t test_name] [chandler-base-path]"

if [ "$CHANDLER_FUNCTIONAL_TEST" = "yes" ]; then
    RUN_FUNCTIONAL=yes
else
    RUN_FUNCTIONAL=no
fi
if [ "$CHANDLER_PERFORMANCE_TEST" = "yes" ]; then
    RUN_PERFORMANCE=yes
else
    RUN_PERFORMANCE=no
fi
if [ "$CHANDLER_UNIT_TEST" = "yes" ]; then
    RUN_UNIT=yes
else
    RUN_UNIT=no
fi

hadError=0

while getopts "fput:m:" Option
do
  case $Option in
    f ) RUN_FUNCTIONAL=yes;;
    p ) RUN_PERFORMANCE=yes;;
    u ) RUN_UNIT=yes;;
    t ) TEST_TO_RUN=$OPTARG;;
    m ) MODE_VALUE=$OPTARG;;
    * ) hadError=1
    ;;   # DEFAULT
  esac
done

if [ $hadError = 1 ]; then
    echo $USAGE
    echo "   if CHANDLER_FUNCTIONAL_TEST=yes or -f then CATS Functional Tests are run"
    echo "   if CHANDLER_PERFORMANCE_TEST=yes or -p then CATS Performance Tests are run"
    echo "   if CHANDLER_UNIT_TEST=yes or -u then Chandler Unit Tests are run"
    echo "if a specific test name or (pattern) is given using -t then only that test name will be run"
    echo "chandler-base-path is 'chandler' that has 'internal' and 'external' as sibling directories"
    exit $E_OPTERROR
fi

  # leave any remaining command line parameters on the command line
shift $(($OPTIND - 1))

if [ ! -n "$1" ]; then
      # if no chandler path is passed in, calculate it
      # the call to pwd is a quick way to get an absolute path
    cd `dirname $0`
    C_DIR=`pwd`
    C_DIR=`dirname $C_DIR`
else
      # a chandler path was passed in so cd to that and
      # get the absolute path
    cd $1
    C_DIR=`pwd`
fi

T_DIR=$C_DIR

if [ ! -d "$C_DIR/i18n" ]; then
    C_DIR=`pwd`
    echo Using current directory [$C_DIR] as the chandler/ directory

    if [ ! -d "$C_DIR/i18n" ]; then
        echo Error: The path [$C_DIR] given does not point to a chandler/ directory
        echo $USAGE
        exit 65
    fi
else
    echo Using [$C_DIR] as the chandler/ directory
fi

if [ "$CHANDLERBIN" = "" ]
then
    CHANDLERBIN="$C_DIR"
fi

HH_DIR=`pwd`
TESTLOG="$C_DIR/do_tests.log"
FAILED_TESTS=""

echo - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + | tee -a $TESTLOG
echo Started `date`                                              | tee -a $TESTLOG
echo Setting up script environment                               | tee -a $TESTLOG

PP_DIR="$C_DIR/tools/QATestScripts/DataFiles"

if [ "$CATSPROFILEDIR" = "" ]
then
    PC_DIR="$C_DIR/test_profile"
else
    PC_DIR="$CATSPROFILEDIR"
fi

if [ "$OSTYPE" = "cygwin" ]; then
    RUN_CHANDLER=RunChandler.bat
    RUN_PYTHON=RunPython.bat
    PP_DIR=`cygpath -w $PP_DIR`
    PC_DIR=`cygpath -w $PC_DIR`
else
    RUN_CHANDLER=RunChandler
    RUN_PYTHON=RunPython
fi

if [ ! -d "$PC_DIR" ]; then
    mkdir -p $PC_DIR
fi

MODES=""
if [ "$MODE_VALUE" == "debug" ]; then
    if [ ! -d $CHANDLERBIN/debug ]; then
        echo $CHANDLERBIN/debug does not exist bug debug mode was explicitly requested | tee -a $TESTLOG
        exit 1
    fi
    MODES="debug"
fi
if [ "$MODE_VALUE" == "release" ]; then
    if [ ! -d $CHANDLERBIN/release ]; then
        echo $CHANDLERBIN/release does not exist bug release mode was explicitly requested | tee -a $TESTLOG
        exit 1
    fi
    MODES="release"
fi

   # if no mode was explicitly requested then check to see what's available
if [ "$MODES" == "" ]; then
      # Run debug if we have that, and release if we have that
    MODE_DEBUG="debug"
    MODE_RELEASE="release"
    if [ ! -d $CHANDLERBIN/debug ]; then
        MODE_DEBUG=""
        echo Skipping debug tests as $CHANDLERBIN/debug does not exist | tee -a $TESTLOG
    fi
    if [ ! -d $CHANDLERBIN/release ]; then
        MODE_RELEASE=""
        echo Skipping release tests as $CHANDLERBIN/release does not exist | tee -a $TESTLOG
    fi
    MODES="$MODE_DEBUG $MODE_RELEASE"
    if [ "$MODES" == " " ]; then
    	echo Both debug and release directories are missing, cannot run.
    	exit 1
    fi
fi

  # each directory to exclude should be place in the EXCLUDES array
  # and a 0 value should be place in the L_EXCLUDES array
  # the EXCLUDES array is then walked and the length of the
  # directory is calculated - beats doing it by hand and making a mistake

EXCLUDES=("$CHANDLERBIN/release" "$CHANDLERBIN/debug" "$C_DIR/tools" "$C_DIR/util")
L_EXCLUDES=(0 0 0 0)
for item in 0 1 2 3 ; do
    L_EXCLUDES[$item]=${#EXCLUDES[$item]}
done

  # if a specific test name has been given then
  # find that test and run it

if [ -n "$TEST_TO_RUN" ]; then
    DIRS=`find $C_DIR -name $TEST_TO_RUN -print`

    if [ "$DIRS" = "" ]; then
        DIRS=`find $C_DIR -name $TEST_TO_RUN.py -print`
    fi

    if [ "$DIRS" = "" ]; then
        echo "Error: The test(s) you requested were not found:" ["$TEST_TO_RUN"]
        FAILED_TESTS="$TEST_TO_RUN"
    else
        for mode in $MODES ; do
            echo Running $mode | tee -a $TESTLOG

            for test in $DIRS ; do
                if [ "$OSTYPE" = "cygwin" ]; then
                    TESTNAME=`cygpath -w $test`
                else
                    TESTNAME=$test
                fi

                echo Running $TESTNAME | tee -a $TESTLOG

                cd $C_DIR

                if echo "$TESTNAME" | grep -q "QATestScripts" ; then
                    $CHANDLERBIN/$mode/$RUN_CHANDLER --create --stderr --nocatch --profileDir="$PC_DIR" --parcelPath="$PP_DIR" --scriptTimeout=600 --scriptFile="$TESTNAME" &> $C_DIR/test.log
                    SUCCESS="#TINDERBOX# Status = PASSED"
                else
                    $CHANDLERBIN/$mode/$RUN_PYTHON $TESTNAME &> $C_DIR/test.log
                    SUCCESS="^OK"
                fi

                echo - - - - - - - - - - - - - - - - - - - - - - - - - - | tee -a $TESTLOG
                cat $C_DIR/test.log | tee -a $TESTLOG

                RESULT=`grep "$SUCCESS" $C_DIR/test.log`
                if [ "$RESULT" = "" ]; then
                    FAILED_TESTS="$FAILED_TESTS ($mode)$TESTNAME"
                fi
            done
        done
    fi
else
    if [ "$RUN_UNIT" = "yes" ]; then
        DIRS=`find $C_DIR -type d -name tests -print`

          # this code walks thru all the dirs with "tests" in their name
          # and then compares them to the exclude dir array by
          # taking the substring of the L_EXCLUDE length value
          # if there is a match, the loop is broken and the dir is skipped

        for item in $DIRS ; do
            FILEPATH=${item%/*}
            EXCLUDED=no
            for index in 0 1 2 3 ; do
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

          # walk thru all of the test dirs and find the test files

        for mode in $MODES ; do
            echo Running $mode unit tests | tee -a $TESTLOG

            for testdir in $TESTDIRS ; do
                TESTS=`find $testdir -name 'Test*.py' -print`

                for test in $TESTS ; do
                    if [ "$OSTYPE" = "cygwin" ]; then
                        TESTNAME=`cygpath -w $test`
                    else
                        TESTNAME=$test
                    fi

                    echo Running $TESTNAME | tee -a $TESTLOG

                    cd $C_DIR
                    $CHANDLERBIN/$mode/$RUN_PYTHON $TESTNAME &> $C_DIR/test.log

                      # scan the test output for the success messge "OK"
                    RESULT=`grep '^OK' $C_DIR/test.log`

                    echo - - - - - - - - - - - - - - - - - - - - - - - - - - | tee -a $TESTLOG
                    echo $TESTNAME [$RESULT] | tee -a $TESTLOG
                    cat $C_DIR/test.log      | tee -a $TESTLOG

                    if [ "$RESULT" = "" ]; then
                        FAILED_TESTS="$FAILED_TESTS ($mode)$TESTNAME"
                    fi
                done
            done
        done
    fi

      # if Functional Tests are needed - find the FunctionalTestSuite and run it

    if [ "$RUN_FUNCTIONAL" = "yes" ]; then
        echo Running $mode functional tests | tee -a $TESTLOG

        for mode in $MODES ; do
            test="$C_DIR/tools/QATestScripts/Functional/FunctionalTestSuite.py"

            if [ "$OSTYPE" = "cygwin" ]; then
                TESTNAME=`cygpath -w $test`
            else
                TESTNAME=$test
            fi
            if [ "$mode" = "debug" ]; then
                STDERR_FLAG="--stderr"
            else
                STDERR_FLAG=""
            fi

            echo Running $TESTNAME | tee -a $TESTLOG

            cd $C_DIR
            $CHANDLERBIN/$mode/$RUN_CHANDLER --create $STDERR_FLAG --nocatch --profileDir="$PC_DIR" --parcelPath="$PP_DIR" --scriptTimeout=600 --scriptFile="$TESTNAME" &> $C_DIR/test.log

              # scan the test output for the success messge "OK"
            RESULT=`grep '#TINDERBOX# Status = PASSED' $C_DIR/test.log`

            echo - - - - - - - - - - - - - - - - - - - - - - - - - - | tee -a $TESTLOG
            echo $TESTNAME [$RESULT] | tee -a $TESTLOG
            cat $C_DIR/test.log      | tee -a $TESTLOG

            if [ "$RESULT" = "" ]; then
                FAILED_TESTS="$FAILED_TESTS ($mode)$TESTNAME"
            fi
        done
    fi

      # if Performance Tests are needed - walk the CATS directory
      # and create a list of all valid tests

    if [ "$RUN_PERFORMANCE" = "yes" ]; then
        echo Running performance tests | tee -a $TESTLOG

        TESTS=`find $C_DIR/tools/QATestScripts/Performance -name 'Perf*.py' -print`
        TIME_LOG=$C_DIR/time.log
        PERF_LOG=$C_DIR/perf.log
        if [ "$OSTYPE" = "cygwin" ]; then
            TIME_LOG=`cygpath -w $TIME_LOG`
            PERF_LOG=`cygpath -w $PERF_LOG`
        fi
        rm -f $PERF_LOG

        # First run tests with empty repository
        for test in $TESTS ; do
            rm -f $TIME_LOG

            # Don't run large data tests here
            if [ `echo $test | grep -v PerfLargeData` ]; then

                if [ "$OSTYPE" = "cygwin" ]; then
                    TESTNAME=`cygpath -w $test`
                else
                    TESTNAME=$test
                fi

                echo -n $TESTNAME
                cd $C_DIR
                $CHANDLERBIN/release/$RUN_CHANDLER --create --nocatch --profileDir="$PC_DIR" --catsPerfLog="$TIME_LOG" --scriptTimeout=600 --scriptFile="$TESTNAME" &> $C_DIR/test.log

                # scan the test output for the success message "OK"
                RESULT=`grep '#TINDERBOX# Status = PASSED' $C_DIR/test.log`

                if [ "$RESULT" = "" ]; then
                    RESULT=Failed
                else
                    RESULT=`cat $TIME_LOG`s
                fi

                echo \ [ $RESULT ] | tee -a $TESTLOG
                echo - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + >> $PERF_LOG
                cat $C_DIR/test.log >> $PERF_LOG

                if [ "$RESULT" = "Failed" ]; then
                    FAILED_TESTS="$FAILED_TESTS $TESTNAME"
                fi
            fi
        done

        echo -n Creating a large repository backup for the remaining tests
        rm -fr $PC_DIR/__repository__.0*
        REPO=$PC_DIR/__repository__.001
        BACKUP_REPO=$C_DIR/tools/QATestScripts/Performance/LargeDataBackupRepository.py
        if [ "$OSTYPE" = "cygwin" ]; then
            REPO=`cygpath -w $REPO`
            BACKUP_REPO=`cygpath -w $BACKUP_REPO`
        fi

        cd $C_DIR
        $CHANDLERBIN/release/$RUN_CHANDLER --create --nocatch --profileDir="$PC_DIR" --catsPerfLog="$TIME_LOG" --scriptTimeout=600 --scriptFile="$BACKUP_REPO" &> $C_DIR/test.log

        # scan the test output for the success message "OK"
        RESULT=`grep '#TINDERBOX# Status = PASSED' $C_DIR/test.log`

        cat $C_DIR/test.log >> $PERF_LOG

        if [ "$RESULT" = "" ]; then
            for test in $TESTS ; do
                FAILED_TESTS="$FAILED_TESTS $test"
            done
        else
            # Show the time it took to create backup
            echo \ \[`<$TIME_LOG`s\]

            # Then run large data tests with restored large repository
            for test in $TESTS ; do
                rm -f $TIME_LOG

                # Run only large data tests
                if [ `echo $test | grep PerfLargeData` ]; then

                    if [ "$OSTYPE" = "cygwin" ]; then
                        TESTNAME=`cygpath -w $test`
                    else
                        TESTNAME=$test
                    fi

                    echo -n $TESTNAME
                    cd $C_DIR
                    $CHANDLERBIN/release/$RUN_CHANDLER --restore="$REPO" --nocatch --profileDir="$PC_DIR" --catsPerfLog="$TIME_LOG" --scriptTimeout=600 --scriptFile="$TESTNAME" &> $C_DIR/test.log

                    # scan the test output for the success message "OK"
                    RESULT=`grep '#TINDERBOX# Status = PASSED' $C_DIR/test.log`

                    if [ "$RESULT" = "" ]; then
                        RESULT=Failed
                    else
                        RESULT=`cat $TIME_LOG`s
                    fi

                    echo \ [ $RESULT ] | tee -a $TESTLOG
                    echo - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + >> $PERF_LOG
                    cat $C_DIR/test.log >> $PERF_LOG

                    if [ "$RESULT" = "Failed" ]; then
                        FAILED_TESTS="$FAILED_TESTS $TESTNAME"
                    fi
                fi
            done
        fi

        RUN_STARTUP_TESTS=yes

        if [ "$OSTYPE" = "cygwin" ]; then
            TESTNAME=`cygpath -w $C_DIR/tools/QATestScripts/Performance/end.py`
            CREATEREPO=`cygpath -w $C_DIR/tools/QATestScripts/Performance/quit.py`
            TIME='time.exe --format=%e'
        else
            TESTNAME=$C_DIR/tools/QATestScripts/Performance/end.py
            CREATEREPO=$C_DIR/tools/QATestScripts/Performance/quit.py

            if [ "${OSTYPE:0:6}" = "darwin" ]; then
                # NOTE: gtime is not part of OS X, you need to compile one
                # yourself (get source from http://directory.fsf.org/time.html)
                # or get it from darwinports project.
                TIME='gtime --format=%e'
                if [ -f `which gtime` ]; then
                    RUN_STARTUP_TESTS=yes
                else
                    echo gtime not found, skipping startup tests
                    RUN_STARTUP_TESTS=no
                fi
            fi
        fi

        if [ "$RUN_STARTUP_TESTS" = "yes" ]; then
            cd $C_DIR
            RUNS="1 2 3"

            echo Creating new empty repository
            $CHANDLERBIN/release/$RUN_CHANDLER --create --nocatch --profileDir="$PC_DIR" --scriptTimeout=600 --scriptFile="$CREATEREPO" &> $C_DIR/test.log

            echo -n Timing startup
            for run in $RUNS ; do
                $TIME -o $T_DIR/start1.$run.log $CHANDLERBIN/release/$RUN_CHANDLER --nocatch --profileDir="$PC_DIR" --scriptTimeout=600 --scriptFile="$TESTNAME" &> $C_DIR/test.log
                cat $T_DIR/start1.$run.log | sed "s/^Command exited with non-zero status [0-9]\+ //" > $C_DIR/test.log
                cat $C_DIR/test.log > $T_DIR/start1.$run.log
                echo -n \ `<"$T_DIR/start1.$run.log"`
            done

            STARTUP=`cat $T_DIR/start1.1.log $T_DIR/start1.2.log $T_DIR/start1.3.log | sort -n | head -n 2 | tail -n 1`
            echo \ \[$STARTUP\s\]

            echo Creating new large repository
            $CHANDLERBIN/release/$RUN_CHANDLER --restore="$REPO" --nocatch --profileDir="$PC_DIR" --scriptTimeout=600 --scriptFile="$CREATEREPO" &> $C_DIR/test.log

            echo -n Timing startup with large repository
            for run in $RUNS ; do
                $TIME -o $T_DIR/start6.$run.log $CHANDLERBIN/release/$RUN_CHANDLER --nocatch --profileDir="$PC_DIR" --scriptTimeout=600 --scriptFile="$TESTNAME" &> $C_DIR/test.log
                cat $T_DIR/start6.$run.log | sed "s/^Command exited with non-zero status [0-9]\+ //" > $C_DIR/test.log
                cat $C_DIR/test.log > $T_DIR/start6.$run.log
                echo -n \ `<"$T_DIR/start6.$run.log"`
            done

            STARTUP_LARGE=`cat $T_DIR/start6.1.log $T_DIR/start6.2.log $T_DIR/start6.3.log | sort -n | head -n 2 | tail -n 1`
            echo \ \[$STARTUP_LARGE\s\]

            echo - - - - - - - - - - - - - - - - - - - - - - - - - - >> $PERF_LOG
            echo $TESTNAME \[\#TINDERBOX\# Status = PASSED\]         >> $PERF_LOG
            echo OSAF_QA: Startup \| $REVISION \| $STARTUP           >> $PERF_LOG
            echo \#TINDERBOX\# Testname = Startup                    >> $PERF_LOG
            echo \#TINDERBOX\# Status = PASSED                       >> $PERF_LOG
            echo \#TINDERBOX\# Time elapsed = $STARTUP \(seconds\)   >> $PERF_LOG

            echo - - - - - - - - - - - - - - - - - - - - - - - - - -                 >> $PERF_LOG
            echo $TESTNAME \[\#TINDERBOX\# Status = PASSED\]                         >> $PERF_LOG
            echo OSAF_QA: Startup_with_large_calendar \| $REVISION \| $STARTUP_LARGE >> $PERF_LOG
            echo \#TINDERBOX\# Testname = Startup_with_large_calendar                >> $PERF_LOG
            echo \#TINDERBOX\# Status = PASSED                                       >> $PERF_LOG
            echo \#TINDERBOX\# Time elapsed = $STARTUP_LARGE \(seconds\)             >> $PERF_LOG
        fi

        SLEEP_TIME=5
        echo Showing performance log in $SLEEP_TIME seconds, Ctrl+C to stop tests
        sleep $SLEEP_TIME
        cat $PERF_LOG
    fi
fi

echo - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + | tee -a $TESTLOG

if [ "$FAILED_TESTS" = "" ]; then
    echo All tests passed | tee -a $TESTLOG
else
    echo The following tests failed | tee -a $TESTLOG

    for item in $FAILED_TESTS ; do
        echo "    $item" | tee -a $TESTLOG
    done

    exit 1
fi
