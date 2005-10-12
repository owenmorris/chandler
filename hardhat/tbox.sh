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

HH_DIR=`pwd`
LOGFILES="svn.log distrib.log install.log tests.log"
MODES="release debug"
SLEEP_MINUTES=5
ENDLOOP="no"

while [ "$ENDLOOP" = "no" ]
do
    BUILDID=`date +%Y%m%d%H%M%S`
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
        $TBOX_UPDATE -t $TBOX_TREE -b $TBOX_BUILD -s building

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

    EXCLUDES=("$C_DIR/release" "$C_DIR/debug" "$C_DIR/tools" "$C_DIR/util")
    L_EXCLUDES=(0 0 0 0)
    for item in 0 1 2 3 ; do
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

                echo Running \"make -C $C_DIR $SNAP install strip\" | tee -a $BUILDLOG
                make -C $C_DIR $SNAP install strip &> $T_DIR/install.log

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

          # remove any reference to buildRevision (only if at start of line)
        sed -i "/^buildRevision/d" $C_DIR/version.py
        echo buildRevision = \"$REVISION\" >> $C_DIR/version.py
    fi

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

      # Set test result variables to initial value of "ok"
      # if any test fails it will be set to "failed" 

    UNITTEST_RESULT="ok"
    FUNCTEST_RESULT="ok"
    PERFTEST_RESULT="ok"

      # walk thru all of the test dirs and find the test files

    for mode in $MODES ; do
        echo Running $mode unit tests | tee -a $BUILDLOG

        for testdir in $TESTDIRS ; do
            TESTS=`find $testdir -name 'Test*.py' -print`

            for test in $TESTS ; do
                if [ "$OSTYPE" = "cygwin" ]; then
                    TESTNAME=`cygpath -w $test`
                else
                    TESTNAME=$test
                fi

                echo Running $TESTNAME | tee -a $BUILDLOG

                cd $C_DIR
                $CHANDLERBIN/$mode/$RUN_PYTHON $TESTNAME &> $T_DIR/test.log
            
                  # scan the test output for the success messge "OK"
                RESULT=`grep '^OK' $T_DIR/test.log`

                echo - - - - - - - - - - - - - - - - - - - - - - - - - - >> $T_DIR/tests.log
                echo $TESTNAME [$RESULT] >> $T_DIR/tests.log
                cat $T_DIR/test.log      >> $T_DIR/tests.log

                if [ "$RESULT" != "OK" ]; then
                    UNITTEST_RESULT="failed"
                fi
            done
        done

          # if Functional Tests are needed - walk the CATS directory
          # and create a list of all valid tests

        echo Running $mode functional tests | tee -a $BUILDLOG

        if [ ! "$CHANDLER_FUNCTIONAL_TEST" = "no" ]; then
            test="$C_DIR/tools/QATestScripts/Functional/FunctionalTestSuite.py"

            if [ "$OSTYPE" = "cygwin" ]; then
                TESTNAME=`cygpath -w $test`
                P_DIR=`cygpath -w $C_DIR`
            else
                TESTNAME=$test
                P_DIR=$C_DIR
            fi

            echo Running $TESTNAME | tee -a $BUILDLOG

            cd $C_DIR
            $CHANDLERBIN/$mode/$RUN_CHANDLER --create --profileDir="$P_DIR" --scriptFile="$TESTNAME" &> $T_DIR/test.log

              # functional tests output a #TINDERBOX# Status = PASSED that we can scan for
            RESULT=`grep "#TINDERBOX# Status = PASSED" $T_DIR/test.log`

            echo - - - - - - - - - - - - - - - - - - - - - - - - - - >> $T_DIR/tests.log
            echo $TESTNAME [$RESULT] >> $T_DIR/tests.log
            cat $T_DIR/test.log      >> $T_DIR/tests.log

            if [ ! "$RESULT" != "#TINDERBOX# Status = PASSED" ]; then
                FUNCTEST_RESULT="failed"
            fi
        fi
    done

      # if Performance Tests are needed - walk the CATS directory
      # and create a list of all valid tests

    if [ "$CHANDLER_PERFORMANCE_TEST" = "yes" ]; then
        echo Running performance tests | tee -a $BUILDLOG

        TESTS=`find $C_DIR/tools/QATestScripts/Performance -name 'Perf*.py' -print`

        for test in $TESTS ; do
            if [ "$OSTYPE" = "cygwin" ]; then
                TESTNAME=`cygpath -w $test`
                P_DIR=`cygpath -w $C_DIR`
            else
                TESTNAME=$test
                P_DIR=$C_DIR
            fi

            echo Running $TESTNAME | tee -a $BUILDLOG

            cd $C_DIR
            $CHANDLERBIN/release/$RUN_CHANDLER --create --profileDir="$P_DIR" --scriptFile="$TESTNAME" &> $T_DIR/test.log

              # performance tests output a #TINDERBOX# Status = PASSED that we can scan for
            RESULT=`grep "#TINDERBOX# Status = PASSED" $T_DIR/test.log`

            echo - - - - - - - - - - - - - - - - - - - - - - - - - - >> $T_DIR/tests.log
            echo $TESTNAME [$RESULT] >> $T_DIR/tests.log
            cat $T_DIR/test.log      >> $T_DIR/tests.log

            if [ "$RESULT" != "#TINDERBOX# Status = PASSED" ]; then
                PERFTEST_RESULT="failed"
            fi
        done
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

        $TBOX_UPDATE -t $TBOX_TREE -b $TBOX_BUILD -s $TBOX_STATUS -f tbox_$BUILDID.log -p $LOGPATH
    fi

    if [ "$TBOX" = "yes" ]; then
        if [ "$TBOX_CYCLE" != "yes" ]; then
            ENDLOOP="yes"
        fi
    else
        ENDLOOP="yes"
    fi
    
    if [ "$ENDLOOP" = "no" ]; then
        echo Sleeping for $SLEEP_MINUTES minutes | tee -a $BUILDLOG

        SLEEP_INTERVAL=`expr $SLEEP_MINUTES \* 60`
        sleep $SLEEP_INTERVAL | tee -a $BUILDLOG
    fi
done