#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""startRev, endRev, repeat, test [OPTIONS d, h]
changes local svn tree to each rev between startRev and endRev
runs test rep number of times
Works only on read only trees using password free svn checkout.
Requires CHANDLERHOME environment variable to be set
Paths to test files should be relative paths starting from CHANDLERHOME

"""
import os, re, sys, getopt, glob

def getCurrentRev():
    """Returns current svn revision as a string"""
    p=re.compile('(?:Revision: )(.*)')
    info = os.popen('svn info').read()
    return p.findall(info)[0]

def getValidRevs():
    """Returns a tuple of all valid svn rev numbers"""
    p=re.compile('(?:^r)([0-9]{4}[1-9]?)(?: |)',re.MULTILINE)
    return p.findall(os.popen('svn log').read())
    
def updateTree(svnRev):
    """Changes local tree to supplied rev"""
    printStatus('changing tree to rev ' + svnRev)
    os.system('svn cleanup')
    updateStr = 'svn up -r ' + svnRev
    os.system(updateStr)
    printStatus('Deleting "release" directory')
    os.system('rm -fr release')
    printStatus('make install')
    os.system('make install purge')
    #fail if did not update - this will probably cause problems until we 
    #figure out how to skip svn rev's that aren't valid
    #assert getCurrentRev == svnRev

def incRev(curRev):
    """Moves up to next rev number.  In the future this should skip numbers that are not valid chandler revs
    for now it just increments it.  """
    curRev = str(1 + int(curRev))
    return curRev

def usage():
    """print help info"""
    print "\n  Usage:"
    print "  python regress.py --startRev=xxxx --endRev=xxxx --repeat=x --test=testscript.py [-dh]"
    print "  or"
    print "  python regressAndTest.py -sxxxx -exxxx -rx -ttestscript.py [-dh]\n"
    print "  Changes svn tree to each revision between startRev, endRev and runs supplied test(s)\n"
    print "  -s  --startRev   is lowest svn revision number to test"
    print "  -e  --endRev     is highest svn revision number to test"
    print "  -r  --repeat     is number of times to repeat test at each revision"
    print "  -t  --test       is path and file name of test script to run"
    print "  -h  --help       prints this"
    print "  -d  --directory  if present 'test' argument is interpreted as a path to a directory of tests"
    print "                   rather than a single file, all .py files in the directory will be run as tests\n"
    print "  Test output is collected in a file named regress_result.txt"
    print "  Output file contains svn rev, test name, test status (pass, fail), and elapsed time for test in a comma delimited format"
    print "  This script needs to be run in a svn directory with read only access, script does not deal with ssh passwords"
    print "  Requires CHANDLERHOME environment variable to be set"
    print "  Paths to test files should be relative paths starting from CHANDLERHOME\n"
    print "  end"
    
def report(result, rev, test, fileOut='regress_result.txt'):
    """test result str, svn rev, test path and file
    outputs test result to file
    """
    try:
        pName = re.compile('(?:#TINDERBOX# Testname = )(.*)(?:\\n)') #capture test name
        pStatus = re.compile('(?:#TINDERBOX# Status = )(.*)')#capture status only ie 'FAILED, PASSED ...
        pTime = re.compile('(?:#TINDERBOX# Time elapsed = )(.*)')#capture elapsed time
        name = pName.findall(result)[0].strip()
        status = pStatus.findall(result)[0].strip()
        eTime = pTime.findall(result)[0].strip()
        rev = rev.strip()
        outStr = ('%s, %s, %s, %s\n' % (rev, name, status, eTime))
        printStatus('Test result\n' + outStr)
        if not os.path.isfile(fileOut):
            f = open(fileOut,'w')
            # add header line
            f.write('Rev,Test, Status, Elapsed Time\n')
        else:
            f = open(fileOut, 'a')
        f.write(outStr)
        f.close()
    except:
        print 'Error reporting on %s %s ' % (rev, test)
    
def printStatus(msg):
    """print message surrounded by blank lines to make it stand out on console"""
    #for i in range(3): print 'X'*20
    print '\n' + msg + '\n'
    #for i in range(3): print 'X'*20
        
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 's:e:r:t:hd',['startRev=','endRev=','repeat=','test='])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    sRev = eRev = rep = test = directory = None
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print 'Help'
            usage()
            sys.exit()
        if opt in ("-d", "--directory"):
            directory = True
        if opt in ("--startRev","-s"):
            sRev = arg
        if opt in ("--endRev","-e"):
            eRev = arg
        if opt in ("--repeat", "-r"):
            rep = arg
        if opt in ("--test","-t"):
            test = arg
    if not (sRev and eRev and rep and test):
        usage()
        sys.exit(2)
    startDir = os.path.abspath(os.curdir)
    CHANDLERHOME = os.getenv('CHANDLERHOME')
    if CHANDLERHOME:
        os.chdir(CHANDLERHOME)
    else:
        print 'CHANDLERHOME environment var not found, exiting'
        sys.exit(2)
    curRev = sRev
    if directory: #test = directory of tests
        tests = glob.glob(test +'/*.py')
    else:
        tests = [test]
    while curRev <= eRev:
        if curRev != getCurrentRev():
            updateTree(curRev)
        else:
            print 'svn repository already at %s skipping svn update' % curRev
        for test in tests:
            for i in range(int(rep)):
                printStatus('on rev %s pass %s of %s for test %s' % (curRev, str(i + 1), rep, test))  
                #remove previous results file if exists
                if os.path.isfile('tmpResult.txt'):
                    os.remove('tmpResult.txt')
                cmdStr = r'./release/RunChandler.bat --create --nocatch -f %s >tmpResult.txt ' % test
                os.system(cmdStr)
                if os.path.isfile('tmpResult.txt'):
                    f = open('tmpResult.txt','r')
                    result = f.read()
                    f.close()
                else:
                    result = "#TINDERBOX# Status =  FAILED TO CAPTURE TEST RESULT \n#TINDERBOX# Testname = %s \n#TINDERBOX# Time elapsed = 0 (seconds)""" % test
                report(result, curRev, test, os.path.join(startDir,'regress_result.txt'))
        curRev = incRev(curRev)


if __name__ == "__main__":
    main()
