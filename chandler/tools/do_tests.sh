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

USAGE="Usage: `basename $0` chandler-base-path"

if [ ! -n "$1" ]; then
    echo $USAGE
    echo if CHANDLER_FUNCTIONAL_TEST=no then CATS Functional Tests are skipped
    echo if CHANDLER_PERFORMANCE_TEST=yes then CATS Performance Tests are run
    exit 65
else
    C_DIR="$1"
    T_DIR=$C_DIR

    if [ ! -d "$C_DIR/i18n" ]; then
        echo Error: The path [$C_DIR] given does not point to a chandler/ directory
        echo $USAGE
        exit 65
    fi
fi

HH_DIR=`pwd`
MODES="release debug"

echo - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + 
echo Started `date`                                              
echo Setting up script environment                               

if [ "$OSTYPE" = "cygwin" ]; then
    RUN_CHANDLER=RunChandler.bat
    RUN_PYTHON=RunPython.bat
else
    RUN_CHANDLER=RunChandler
    RUN_PYTHON=RunPython
fi

  # if the debug/ path is not found, then avoid debug tests
if [ ! -d $C_DIR/debug ]; then
    MODES="release"
    echo Skipping debug tests as $C_DIR/debug does not exist 
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

echo Running \"make -C $C_DIR cats\" 

make -C $C_DIR cats

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
    echo Running $mode unit tests 

    for testdir in $TESTDIRS ; do
        TESTS=`find $testdir -name 'Test*.py' -print`

        for test in $TESTS ; do
            if [ "$OSTYPE" = "cygwin" ]; then
                TESTNAME=`cygpath -w $test`
            else
                TESTNAME=$test
            fi

            echo Running $TESTNAME

            cd $C_DIR
            ./$mode/$RUN_PYTHON $TESTNAME
        done
    done

      # if Functional Tests are needed - walk the CATS directory
      # and create a list of all valid tests

    echo Running $mode functional tests 

    if [ ! "$CHANDLER_FUNCTIONAL_TEST" = "no" ]; then
        TESTS=`find $C_DIR/util/QATestScripts/Functional -name 'Test*.py' -print`

        for test in $TESTS ; do
            if [ "$OSTYPE" = "cygwin" ]; then
                TESTNAME=`cygpath -w $test`
                P_DIR=`cygpath -w $C_DIR`
            else
                TESTNAME=$test
                P_DIR=$C_DIR
            fi

            echo Running $TESTNAME

            cd $C_DIR
            ./$mode/$RUN_CHANDLER --create --profileDir="$P_DIR" --scriptFile="$TESTNAME"
        done
    fi
done

  # if Performance Tests are needed - walk the CATS directory
  # and create a list of all valid tests

if [ "$CHANDLER_PERFORMANCE_TEST" = "yes" ]; then
    echo Running performance tests 

    TESTS=`find $C_DIR/util/QATestScripts/Performance -name 'Perf*.py' -print`

    for test in $TESTS ; do
        if [ "$OSTYPE" = "cygwin" ]; then
            TESTNAME=`cygpath -w $test`
            P_DIR=`cygpath -w $C_DIR`
        else
            TESTNAME=$test
            P_DIR=$C_DIR
        fi

        echo Running $TESTNAME

        cd $C_DIR
        ./release/$RUN_CHANDLER --create --profileDir="$P_DIR" --scriptFile="$TESTNAME"
    done
fi
