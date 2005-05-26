__version__     = "$Revision$"
__date__        = "$Date$"
__copyright__   = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__     = "GPL -- see LICENSE.txt"


"""
hardhatlib

hardhatlib provides a set of methods for controlling the build process of
multiple sub-projects in a uniform way.  The typical way to interact with
this library is via the hardhat.py command-line script, but you could
call these methods directly from some automated build system or GUI.
Each sub- project needs a __hardhat__.py file which defines build, clean,
and execute methods; these methods are passed a dictionary describing
the build environment.  The __hardhat__.py methods also log their status
to a structured log, and alert hardhatlib of problems via Exceptions.

"""

import os, sys, platform, glob, fnmatch, errno, string, shutil, fileinput, re, popen2
import hardhatutil

# Earlier versions of Python don't define these, so let's include them here:
True = 1
False = 0

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

defaults = {
    'verbosity'   : 1,
    'showenv'     : 0,
    'version'     : 'release',
    'showlog'     : False,
    'interactive' : True,
    'outputdir'   : "",
}


def getCHANDLERvars(buildenv):

    CHANDLERHOME = os.getenv('CHANDLERHOME')
    if not CHANDLERHOME:
        if buildenv['os'] == 'win':
            # Use DOS format paths under windows
            CHANDLERHOME = os.path.join(buildenv['root_dos'], 'chandler')
        else:
            CHANDLERHOME = os.path.join(buildenv['root'], 'chandler')

    return (CHANDLERHOME, os.getenv('CHANDLERBIN') or CHANDLERHOME)


def init(buildenv):
    """
    Initialize the build environment, which is a dictionary containing
    various values for OS type, PATH, compiler, debug/release setting, etc.
    Parameters:
        root: fully qualified path to the top of the build hierarchy
    Returns:
        buildenv:  a dictionary containing the following environment settings:
            - root: the root path passed in (which should be the parent of chandler)
            - os: win, posix, unknown
            - path: system executable search path
            - compiler: full path to C compiler (currently windows only)
            - python: full path to release version of python we are building
            - python_d: full path to debug version of python we are building
            - verbosity: 0 for quiet, > 0 for messages displayed to stdout
            - log: a time-ordered list of log entries
            - version: 'debug' or 'release'
    """

    if not buildenv.has_key('root'):
        raise HardHatBuildEnvError, "Missing 'root'"

    if not buildenv.has_key('hardhatroot'):
        raise HardHatBuildEnvError, "Missing 'hardhatroot'"

    for key in defaults.keys():
        if not buildenv.has_key(key):
            buildenv[key] = defaults[key]

    if not buildenv.has_key('logfile'):
        buildenv['logfile'] = os.path.join(buildenv['root'], "hardhat.log")

    # normalize what python thinks the OS is to a string that we like:
    buildenv['os']        = 'unknown'
    buildenv['osversion'] = 'unknown'
    
    if os.name == 'nt':
        buildenv['os'] = 'win'
        buildenv['oslabel'] = 'win'
        buildenv['root_dos'] = buildenv['root']
        buildenv['path'] = os.environ['path']
    elif os.name == 'posix':
        buildenv['os'] = 'posix'
        buildenv['oslabel'] = 'linux'
        buildenv['path'] = os.environ['PATH']
        if sys.platform == 'darwin':
            # It turns out that Mac OS X happens to have os.name of 'posix'
            # but the steps to build things under OS X is different enough
            # to warrant its own 'os' value:
            buildenv['os'] = 'osx'
            buildenv['oslabel'] = 'osx'
            
            macVersion = platform.mac_ver()
            osVersion  = macVersion[0]
            
            buildenv['osversion'] = osVersion[:4]
            
        if sys.platform == 'cygwin':
            buildenv['os'] = 'win'
            buildenv['oslabel'] = 'win'
            buildenv['path'] = os.environ['PATH']
            try:
                cygpath = os.popen("/bin/cygpath -w " + buildenv['root'], "r")
                buildenv['root_dos'] = cygpath.readline()
                buildenv['root_dos'] = buildenv['root_dos'][:-1]
                cygpath.close()
            except Exception, e:
                print e
                print "Unable to call 'cygpath' to determine DOS-equivalent for project path."
                print "Either make sure that 'cygpath' is in your PATH or run the Windows version"
                print "of Python from http://python.org/, rather than the Cygwin Python"
                raise HardHatError

    else:
        raise HardHatUnknownPlatformError

    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)

    buildenv['sh']    = hardhatutil.findInPath(buildenv['path'], "sh", 0)
    buildenv['make']  = hardhatutil.findInPath(buildenv['path'], "make", 0)
    buildenv['svn']   = hardhatutil.findInPath(buildenv['path'], "svn")
    buildenv['scp']   = hardhatutil.findInPath(buildenv['path'], "scp", 0)
    buildenv['tar']   = hardhatutil.findInPath(buildenv['path'], "tar", 0)
    buildenv['gzip']  = hardhatutil.findInPath(buildenv['path'], "gzip", 0)
    buildenv['zip']   = hardhatutil.findInPath(buildenv['path'], "zip", 0)

    # set OS-specific variables
    if buildenv['os'] == 'win':

        buildenv['python']   = os.path.join(CHANDLERBIN, 'release', 'bin', 'python.exe')
        buildenv['python_d'] = os.path.join(CHANDLERBIN, 'debug',   'bin', 'python_d.exe')
        buildenv['swig']     = os.path.join(CHANDLERBIN, 'release', 'bin', 'swig.exe')
        buildenv['swig_d']   = os.path.join(CHANDLERBIN, 'debug',   'bin', 'swig.exe')

        buildenv['makensis'] = hardhatutil.findInPath(buildenv['path'], "makensis.exe", 0)

        import os_win
        
        vs = os_win.VisualStudio();
        
        buildenv['compilerVersion'] = vs.version

        if vs.Found:
            # log(buildenv, HARDHAT_MESSAGE, "HardHat", "Looking for devenv.exe...")
            devenv_file = vs.find_exe( "devenv.exe")
            if( devenv_file ):
                # log(buildenv, HARDHAT_MESSAGE, "HardHat", "Found " + devenv_file)
                buildenv['compiler'] = devenv_file
            else:
                log(buildenv, HARDHAT_ERROR, "HardHat", "Can't find devenv.exe")
                log_dump(buildenv)
                raise HardHatMissingCompilerError

            # log(buildenv, HARDHAT_MESSAGE, "HardHat", "Looking for nmake.exe...")
            nmake_file = vs.find_exe( "nmake.exe")
            if( nmake_file ):
                # log(buildenv, HARDHAT_MESSAGE, "HardHat", "Found " + nmake_file)
                buildenv['nmake'] = nmake_file
            else:
                log(buildenv, HARDHAT_ERROR, "HardHat", "Can't find nmake.exe")
                log_dump(buildenv)
                raise HardHatMissingCompilerError
            include_path = vs.get_msvc_paths('include')
            include_path = string.join( include_path, ";")
            # log(buildenv, HARDHAT_MESSAGE, "HardHat", "Include: " + include_path)
            os.putenv('INCLUDE', include_path)
            lib_path = vs.get_msvc_paths('library')
            lib_path = string.join( lib_path, ";")
            # log(buildenv, HARDHAT_MESSAGE, "HardHat", "lib: " + lib_path)
            os.putenv('LIB', lib_path)

            cl_dir = os.path.dirname(nmake_file)
            buildenv['path'] = cl_dir + os.pathsep + buildenv['path']
            devenv_dir = os.path.dirname(devenv_file)
            buildenv['path'] = devenv_dir + os.pathsep + buildenv['path']
        else:
            log(buildenv, HARDHAT_MESSAGE, "HardHat", "Could not locate Visual Studio")

    if buildenv['os'] == 'posix':

        buildenv['python'] = os.path.join(CHANDLERBIN,
                                          'release', 'bin', 'python')
        buildenv['python_d'] = os.path.join(CHANDLERBIN,
                                            'debug', 'bin', 'python_d')

        buildenv['swig'] = os.path.join(CHANDLERBIN,
                                        'release', 'bin', 'swig')
        buildenv['swig_d'] = os.path.join(CHANDLERBIN,
                                          'debug', 'bin', 'swig')

    if buildenv['os'] == 'osx':

        buildenv['python'] = os.path.join(CHANDLERBIN, 'release', 'Library',
                                          'Frameworks', 'Python.framework',
                                          'Versions', 'Current', 'Resources',
                                          'Python.app', 'Contents', 'MacOS',
                                          'Python')

        buildenv['python_d'] = os.path.join(CHANDLERBIN, 'debug', 'Library',
                                            'Frameworks', 'Python.framework',
                                            'Versions', 'Current', 'Resources',
                                            'Python.app', 'Contents', 'MacOS',
                                            'Python')

        buildenv['swig'] = os.path.join(CHANDLERBIN,
                                        'release', 'bin', 'swig')
        buildenv['swig_d'] = os.path.join(CHANDLERBIN,
                                          'debug', 'bin', 'swig')


    # Determine the Python lib directory (the parent of site-packages)
    if buildenv['os'] == 'posix':
        lib_dir_release = os.path.join(CHANDLERBIN,
                                       'release', 'lib', 'python2.4')
        lib_dir_debug = os.path.join(CHANDLERBIN,
                                     'debug', 'lib', 'python2.4')

    if buildenv['os'] == 'win':
        lib_dir_release = os.path.join(CHANDLERBIN, 'release', 'bin', 'Lib')
        lib_dir_debug = os.path.join(CHANDLERBIN, 'debug', 'bin', 'Lib')

    if buildenv['os'] == 'osx':
        lib_dir_release = os.path.join(CHANDLERBIN, 'release', 'Library',
                                       'Frameworks', 'Python.framework',
                                       'Versions', 'Current', 'lib',
                                       'python2.4')
        lib_dir_debug = os.path.join(CHANDLERBIN, 'debug', 'Library',
                                     'Frameworks', 'Python.framework',
                                     'Versions', 'Current', 'lib',
                                     'python2.4')

    buildenv['pythonlibdir'] = lib_dir_release
    buildenv['pythonlibdir_d'] = lib_dir_debug

    return buildenv
# end init()

def inspectSystem():
    print "Not implemented yet"
    return

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Log-related functions and message types

# Types of log messages, used as 2nd parameter to log()
HARDHAT_MESSAGE = 0  # Normal log message
HARDHAT_WARNING = 1  # Warning message
HARDHAT_ERROR   = 2  # Error message


def log(buildenv, status, module_name, message):
    """
    Store a message to the hardhat log.  Display the message on stdout if
    verbose parameter is > 0.
    Parameters:
        buildenv: the build environment dictionary
        status: one of the three types defined above
        module_name: a string identifying the source of this message
        message: the message string itself
    Returns:
        nothing
    """

    if not buildenv.has_key('log'):
        buildenv['log'] = []
    buildenv['log'].append((status, module_name, message))
    if buildenv.has_key('verbosity'):
        if buildenv['verbosity'] > 0:
            entry_dump((status, module_name, message))

    output = file(buildenv['logfile'], 'a+', 0)
    entry_dump((status, module_name, message), output)
    output.close()

# end log()


def entry_dump(entry, file=sys.stdout):
    """
    Print a single entry to stdout.
    Parameters:
        entry: a tuple of the following format (status, module_name, message)
    Returns:
        nothing
    """

    file.write("[ " + entry[1] + " ]")
    if entry[0] == HARDHAT_WARNING:
        file.write(" WARNING ")
    if entry[0] == HARDHAT_ERROR:
        file.write(" ***ERROR*** ")
    file.write(": " + entry[2] + "\n")
# end entry_dump()


def log_dump(buildenv):
    """
    Display the entire log to stdout.
    Parameters:
        buildenv: the build environment dictionary containing the log.
    Returns:
        nothing
    """

    if buildenv.has_key('log'):
        for entry in buildenv['log']:
            entry_dump(entry)
# end log_dump()


def log_rotate(buildenv):
    """
    Rotates log files by renaming hardhat.log --> hardhat.log.1
    and so on up to hardhat.log.5
    """
    logfiles = [buildenv['logfile']]
    for i in range(1,6):
        logfiles.append(buildenv['logfile'] + "." + str(i))
    for i in range(len(logfiles)-1,-1,-1):
        if os.path.isfile(logfiles[i]):
            if( i == 5 ):
                os.remove(logfiles[i])
            else:
                os.rename(logfiles[i], logfiles[i+1])


            
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Build, clean, execute functions

def clean(buildenv, module_name):
    """
    Prepare then invoke the clean() method for the given module_name.  Current
    working directory is set to the subproject's directory before executing
    its clean() method.
    Parameters:
        buildenv: the build environment dictionary
        module_name: the directory name of the subproject to clean
    Returns:
        nothing
    """

    os.chdir(buildenv['root'])
    # log(buildenv, HARDHAT_MESSAGE, module_name, "Cleaning")
    module_path = buildenv['root'] + os.sep + module_name + os.sep + \
     "__hardhat__.py"
    module = module_from_file(buildenv, module_path, module_name)
    os.chdir(module_name)
    module.clean(buildenv)
    # log(buildenv, HARDHAT_MESSAGE, module_name, "Back from clean")
# end clean()


def cleanDependencies(buildenv, module_name, history):
    """
    Based on the list of dependencies in the module's __hardhat_.py file, 
    call each one's clean(), and then call module's clean().
    Parameters:
        buildenv: the build environment dictionary
        module_name: the directory name of the subproject
        history: keeps track of which subprojects have been cleaned, so that
         each is cleaned only once
    Returns:
        nothing
    """

    module_path = buildenv['root'] + os.sep + module_name + os.sep + \
     "__hardhat__.py"
    module = module_from_file(buildenv, module_path, module_name)
    clean(buildenv, module_name)
    history[module_name] = 1
    dep_list = list(module.dependencies)
    dep_list.reverse()
    for dependency in dep_list:
        if not history.has_key(dependency):
            cleanDependencies(buildenv, dependency, history)
# end cleanDependencies()




def build(buildenv, module_name):
    """
    Prepare then invoke the build() method for the given module_name.  Current
    working directory is set to the subproject's directory before executing
    its build() method.
    Parameters:
        buildenv: the build environment dictionary
        module_name: the directory name of the subproject to build
    Returns:
        nothing
    """

    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)

    os.chdir(buildenv['root'])
    log(buildenv, HARDHAT_MESSAGE, module_name, "Building")
    if module_name == 'chandler':
        module_path = os.path.join(CHANDLERHOME, "__hardhat__.py")
    else:
        module_path = os.path.join(CHANDLERHOME, module_name, "__hardhat__.py")
    module = module_from_file(buildenv, module_path, module_name)
    os.chdir(module_name)
    module.build(buildenv)
    # log(buildenv, HARDHAT_MESSAGE, module_name, "Back from build")
# end build()

    
def buildDependencies(buildenv, module_name, history):
    """
    Based on the list of dependencies in the module's __hardhat_.py file, 
    call each one's build(), and then call module's build().
    Parameters:
        buildenv: the build environment dictionary
        module_name: the directory name of the subproject
        history: keeps track of which subprojects have been built, so that
         each is built only once
    Returns:
        nothing
    """

    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)

    if module_name == 'chandler':
        module_path = os.path.join(CHANDLERHOME, "__hardhat__.py")
    else:
        module_path = os.path.join(CHANDLERHOME, module_name, "__hardhat__.py")
    module = module_from_file(buildenv, module_path, module_name)
    for dependency in module.dependencies:
        if not history.has_key(dependency):
            buildDependencies(buildenv, dependency, history)
    build(buildenv, module_name)
    history[module_name] = 1
# end buildDependencies()



def scrub(buildenv, module_name):
    """
    Calls svnClean to remove all local files that aren't under SVN control.
    This is helpful when you want to make sure that the module is really clean!
    Parameters:
        buildenv: the build environment dictionary
        module_name: the directory name of the subproject to scrub
    Returns:
        nothing
    """

    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)

    os.chdir(buildenv['root'])
    log(buildenv, HARDHAT_MESSAGE, module_name, "Scrubbing")
    if module_name == 'chandler':
        module_path = CHANDLERHOME
    else:
        module_path = os.path.join(CHANDLERHOME, module_name)
    svnClean(buildenv, [module_path])
    # log(buildenv, HARDHAT_MESSAGE, module_name, "Back from build")
# end scrub()

    
def scrubDependencies(buildenv, module_name):
    """
    Based on the list of dependencies in the module's __hardhat_.py file, 
    call scrub() on each one, and then call scrub() on the module.
    Parameters:
        buildenv: the build environment dictionary
        module_name: the directory name of the subproject
    Returns:
        nothing
    """

    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)

    dependencies = {}
    getDependencies(buildenv, module_name, dependencies)
    dirsToScrub = []
    for dep in dependencies.keys():
        dirsToScrub.append(os.path.join(CHANDLERHOME, dep))
    svnClean(buildenv, dirsToScrub)
# end scrubDependencies()

def getDependencies(buildenv, module_name, history):
    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)
    if module_name == 'chandler':
        module_path = os.path.join(CHANDLERHOME, "__hardhat__.py")
    else:
        module_path = os.path.join(CHANDLERHOME, module_name, "__hardhat__.py")
    module = module_from_file(buildenv, module_path, module_name)
    for dependency in module.dependencies:
        if not history.has_key(dependency):
            getDependencies(buildenv, dependency, history)
    history[module_name] = 1



def run(buildenv, module_name):
    """
    Execute the run() method for the given module.  Current working directory
    is set to that of the subproject before execution.
    Parameters:
        buildenv: the build environment dictionary
        module_name:  the directory name of the subproject whose execute() 
         method we are calling.
    Returns:    
        nothing
    """
    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)
    log(buildenv, HARDHAT_MESSAGE, module_name, "Executing")
    os.chdir(buildenv['root'])
    if module_name == 'chandler':
        module_path = os.path.join(CHANDLERHOME, "__hardhat__.py")
    else:
        module_path = os.path.join(CHANDLERHOME, module_name, "__hardhat__.py")
    module = module_from_file(buildenv, module_path, module_name)
    os.chdir(module_name)

    module.run(buildenv)
    log(buildenv, HARDHAT_MESSAGE, module_name, "Execution complete")
# end run()


def removeRuntimeDir(buildenv, module_name):
    """
    Remove the "release" or "debug" directory for the module.  [Can someone
    think of a better name for what these directories are, besides "runtime"?]
    Current working directory is set to that of the subproject before 
    execution.
    Parameters:
        buildenv: the build environment dictionary
        module_name:  the directory name of the subproject whose
         removeRuntimeDir() method we are calling
    Returns:    
        nothing
    """

    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)
    log(buildenv, HARDHAT_MESSAGE, module_name, "Removing runtime directory")
    os.chdir(buildenv['root'])
    if module_name == 'chandler':
        module_path = os.path.join(CHANDLERHOME, "__hardhat__.py")
    else:
        module_path = os.path.join(CHANDLERHOME, module_name, "__hardhat__.py")
    module = module_from_file(buildenv, module_path, module_name)
    os.chdir(module_name)
    module.removeRuntimeDir(buildenv)
    log(buildenv, HARDHAT_MESSAGE, module_name, "Removal complete")
# end removeRuntimeDir()


def distribute(buildenv, module_name, buildVersion):
    """
    Execute the distribute() method for the given module.  Current working 
    directory is set to that of the subproject before execution.
    Parameters:
        buildenv: the build environment dictionary
        module_name:  the directory name of the subproject whose execute() 
         method we are calling.
    Returns:    
        nothing
    """
    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)
    log(buildenv, HARDHAT_MESSAGE, module_name, "Creating distribution")
    os.chdir(buildenv['root'])
    if module_name == 'chandler':
        module_path = os.path.join(CHANDLERHOME, "__hardhat__.py")
    else:
        module_path = os.path.join(CHANDLERHOME, module_name, "__hardhat__.py")
    module = module_from_file(buildenv, module_path, module_name)
    os.chdir(module_name)

    buildenv["buildVersion"] = buildVersion
    module.distribute(buildenv)
    log(buildenv, HARDHAT_MESSAGE, module_name, "Distribution complete")
# end distribute()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Unit testing functions

def runTest(buildenv, testFile, fullPath):

    if buildenv['version'] == 'debug':
        python = buildenv['python_d']
        pythonPath = buildenv['pythonlibdir_d'] + os.sep + '..' + os.sep + '..'
    elif buildenv['version'] == 'release':
        python = buildenv['python']
        pythonPath = buildenv['pythonlibdir'] + os.sep + '..' + os.sep + '..'

    exit_code = executeCommand(buildenv, testFile, [ python, testFile, '-v' ],
                               "Testing %s" %(fullPath),
                               HARDHAT_NO_RAISE_ON_ERROR)
    if exit_code != 0:
        buildenv['failed_tests'].append(fullPath)
        log(buildenv, HARDHAT_ERROR, 'Tests', "Failed: %s" %(fullPath))
        
def recursiveTest(buildenv, path):

    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)

    path = os.path.abspath(path)
    os.chdir(path)

    testFiles = glob.glob('Test*.py')
    for testFile in testFiles:
        fullTestFilePath = os.path.join(path, testFile)
        runTest(buildenv, testFile, fullTestFilePath)

    chandler_debug = os.path.join(CHANDLERBIN, 'debug')
    chandler_release = os.path.join(CHANDLERBIN, 'release')

    for name in os.listdir(path):
        full_name = os.path.join(path, name)
        if os.path.isdir(full_name):
            # Do not recurse into debug or release dirs since they
            # should not contain any of our tests.
            if (full_name.rfind(chandler_debug) < 0) and \
               (full_name.rfind(chandler_release) < 0):
                recursiveTest(buildenv, full_name)

def test(buildenv, dir, *modules):
    """
    Given a directory, recursively find all files named "Test*.py" and run
    them as unit tests, or run the test modules passed on the command line.
    """

    buildenv['failed_tests'] = []
    args = []
    
    if modules:
        i = 0
        for m in modules:
            if m.startswith('-'):
                args = list(modules[i:])
                modules = modules[0:i]
                break
            else:
                i += 1

    if not modules:
        recursiveTest(buildenv, dir)
    else:
        for module in modules:
            runTest(buildenv, module, module)

    failures = len(buildenv['failed_tests'])
    if failures == 0:
        log(buildenv, HARDHAT_MESSAGE, 'Tests', "All tests successful")
    else:
        log(buildenv, HARDHAT_ERROR, 'Tests', "%d test(s) failed" %(failures))
        for testFile in buildenv['failed_tests']:
            log(buildenv, HARDHAT_ERROR, 'Tests', "Failed: %s" %(testFile))
        raise HardHatUnitTestError

    return args

# end test()


def generateDocs(buildenv, module_name):
    os.chdir(buildenv['root'])
    # log(buildenv, HARDHAT_MESSAGE, module_name, "Building")
    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)
    if module_name == 'chandler':
        module_path = os.path.join(CHANDLERHOME, "__hardhat__.py")
    else:
        module_path = os.path.join(CHANDLERHOME, module_name, "__hardhat__.py")
    module = module_from_file(buildenv, module_path, module_name)
    os.chdir(module_name)
    module.generateDocs(buildenv)
    # log(buildenv, HARDHAT_MESSAGE, module_name, "Back from build")
# end build()



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module import functions

def module_from_file(buildenv, module_path, module_name):
    """ 
    Load a module from a file into a code object.
    Parameters:
        buildenv: the build environment dictionary
        module_path: absolute path to python file
        module_name: name assigned to code object
    Returns:
        code module object
    """


    if os.access(module_path, os.R_OK):
        module_file = open(module_path)

        # Here's a cool bug I had to workaround:  if module_name has a "." in
        # it, bad things happen down the road (exceptions get created within
        # invalid package); example:  if module_name is 'wxWindows-2.4' then
        # hardhatlib throws an exception and it gets created as 
        # wxWindows-2.hardhatlib.HardHatError.  The fix is to replace "." with
        # "_"
        module_name = module_name.replace(".", "_")

        module = import_code(module_file, module_name)
        return module
    else:
        if buildenv:
            log(buildenv, HARDHAT_ERROR, 'hardhat', module_path + \
             "doesn't exist")
        raise HardHatMissingFileError, "Missing " + module_path
# end module_from_file()


def import_code(code, name):
    """
    Imports python code from open file handle into a code module object.
    Parameters:
        code: an open file handle containing python code
        name: a name to assign to this module
    Returns:
        code module object
    """

    import imp
    module = imp.new_module(name)
    sys.modules[name] = module
    exec code in module.__dict__
    return module
# end import_code()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Utility functions

def rmdir_recursive(dir):
    """
    Recursively remove a directory.
    Parameters:
        dir: directory path
    Returns:
        nothing
    """

    if os.path.islink(dir):
        os.remove(dir)
        return

    for name in os.listdir(dir):
        full_name = os.path.join(dir, name)
        # on Windows, if we don't have write permission we can't remove
        # the file/directory either, so turn that on
        if os.name == 'nt':
            if not os.access(full_name, os.W_OK):
                os.chmod(full_name, 0600)
        if os.path.isdir(full_name):
            rmdir_recursive(full_name)
        else:
            # print "removing file", full_name
            os.remove(full_name)
    os.rmdir(dir)
# rmdir_recurisve()

def rm_files(dir, pattern):
    """
    Remove files in a directory matching pattern
    Parameters:
        dir: directory path
        patter: filename pattern
    Returns:
        nothing
    """

    pattern = '^%s$' %(pattern)
    pattern = pattern.replace('.', '\\.').replace('*', '.*').replace('?', '.')
    exp = re.compile(pattern)
    
    for name in os.listdir(dir):
        if exp.match(name):
            full_name = os.path.join(dir, name)
            if not os.path.isdir(full_name):

                # on Windows, if we don't have write permission we can't remove
                # the file/directory either, so turn that on
                if os.name == 'nt':
                    if not os.access(full_name, os.W_OK):
                        os.chmod(full_name, 0600)

                os.remove(full_name)
# rm_files()

def executeScript(buildenv, args):

    if buildenv['version'] == 'debug':
        python = buildenv['python_d']

    if buildenv['version'] == 'release':
        python = buildenv['python']

    # script = args[0]
    print [python] + args
    executeCommandNoCapture( buildenv, "HardHat",
     [python] + args, "Running" )


def epydoc(buildenv, name, message, *args):

    setupEnvironment(buildenv)

    if buildenv['version'] == 'debug':
        python = buildenv['python_d']
    elif buildenv['version'] == 'release':
        python = buildenv['python']

    command = [ python, '-c', '"from epydoc.cli import cli\ncli()"' ]
    command.extend(args)

    if name is None:   # normal -j command line use, not from __hardhat__.py
        buildlog = sys.stdout
    else:
        buildlog = file(buildenv['logfile'], 'a+', 0)
        log(buildenv, HARDHAT_MESSAGE, name, message)

    print >> buildlog, command
    process = popen2.Popen4(' '.join(command), True)

    while True:
        output = process.fromchild.read(128)
        if len(output) == 0:
            break
        print >> buildlog, output,

    exit_code = process.wait()
    if name is not None:
        buildlog.close()
    
    if exit_code == 0:
        log(buildenv, HARDHAT_MESSAGE, "HardHat", "OK")
    else:
        log(buildenv, HARDHAT_ERROR, "HardHat",
            "Command exited with code = %s" %(exit_code))
        raise HardHatExternalCommandError
    
    return exit_code

#def cvsCheckout(buildenv, projectRoot):
#
#    cvs = buildenv['cvs']
#    cvsroot = os.getenv('CHANDLER_CVSROOT')
#
#    if cvsroot == None:
#        log(buildenv, HARDHAT_ERROR, "HardHat",
#            "CHANDLER_CVSROOT environment variable not set")
#        raise HardHatBuildEnvError
#        
#    command = [ cvs, '-z3', '-d', cvsroot, 'co chandler-system' ]
#    os.chdir(os.path.join(projectRoot, '..', '..'))
#
#    print os.path.abspath(".") + '>' + string.join(command)
#
#    exit_code = os.spawnv(os.P_WAIT, cvs, command)
#
#    if exit_code == 0:
#        log(buildenv, HARDHAT_MESSAGE, "HardHat", "OK")
#    else:
#        log(buildenv, HARDHAT_ERROR, "HardHat",
#            "Command exited with code = " + str(exit_code) )
#        raise HardHatExternalCommandError
#    
#    return exit_code


def findHardHatFile(dir):
    """ Look for __hardhat__.py in directory "dir", and if it's not there,
        keep searching up the directory hierarchy; return the first directory
        that contains a __hardhat__.py file.  If / is reached without finding
        one, return None.
    """
    absPath = os.path.abspath(dir)
    if os.path.isfile(os.path.join(absPath, "__hardhat__.py")):
        return os.path.join(absPath, "__hardhat__.py")
    prevHead = None
    (head, tail) = os.path.split(absPath)
    print "Looking for __hardhat__.py in..."
    while head != prevHead:
        print " ", head,
        if os.path.isfile(os.path.join(head, "__hardhat__.py")):
            print " ...found one"
            print
            return os.path.join(head, "__hardhat__.py")
        prevHead = head
        print " ...no"
        (head, tail) = os.path.split(head)
    print
    return None


def lint(buildenv, args):
    """ Run PyChecker against the scripts passed in as args """

    if buildenv['version'] == 'debug':
        python = buildenv['python_d']
        sitePackages = os.path.join(buildenv['pythonlibdir_d'], "site-packages")

    if buildenv['version'] == 'release':
        python = buildenv['python']
        sitePackages = os.path.join(buildenv['pythonlibdir'], "site-packages")

    checkerFile = os.path.join(sitePackages, "pychecker", "checker.py")

    executeCommandNoCapture( buildenv, "HardHat",
     [python, checkerFile] + args, "Running PyChecker" )


def mirrorDirSymlinks(src, dest):
    """ Recreate the directory structure of src under dest, with symlinks
        pointing to the files in src.  src and dest must be absolute.  """

    if not os.path.exists(dest):
        os.mkdir(dest)

    for name in os.listdir(src):
        fullName = os.path.join(src, name)
        if os.path.isdir(fullName):
            mirrorDirSymlinks(fullName, os.path.join(dest, name))
        if os.path.isfile(fullName):
            if not os.path.exists(os.path.join(dest, name)):
                os.symlink(fullName, os.path.join(dest, name))


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# External program control functions

def setupEnvironment(buildenv):

    CHANDLERHOME, CHANDLERBIN = getCHANDLERvars(buildenv)
    os.putenv('CHANDLERHOME', CHANDLERHOME)
    os.putenv('CHANDLERBIN', CHANDLERBIN)

    path = [ os.path.join(CHANDLERBIN, buildenv['version'], 'bin'),
             buildenv['path'] ]
    path = os.pathsep.join(path)
    os.putenv('BUILDMODE', buildenv['version'])

    # to run Chandler-related scripts from directories other than 
    # chandler, PYTHONPATH is needed
    pythonpaths = []
    prevPath = os.getenv('PYTHONPATH')
    if prevPath:
        pythonpaths.append(prevPath)

    # need to add chandler and chandler/parcels to PYTHONPATH
    pythonpaths.append(CHANDLERHOME)
    pythonpaths.append(os.path.join(CHANDLERHOME, "parcels"))
    pythonpath = os.pathsep.join(pythonpaths)

    # log(buildenv, HARDHAT_MESSAGE, 'hardhat', "Setting path to " + path)
    # os.putenv('path', path)
    if (sys.platform == 'cygwin'):
        # Even though we're under cygwin, we're going to be launching 
        # external programs that expect PATH to be in DOS format, so
        # convert it
        try:
            if('.'.join(map(str, sys.version_info[:3])) < '2.3.0'):
                # we only need to fix the path on versions before 2.3
                cygpath = os.popen("/bin/cygpath -wp \"" + path + "\"", "r")
                path = cygpath.readline()
                path = path[:-1]
                cygpath.close()

            # also convert PYTHONPATH to DOS format
            cygpath = os.popen("/bin/cygpath -wp \"" + pythonpath + "\"", "r")
            pythonpath = cygpath.readline()
            pythonpath = pythonpath[:-1]
            cygpath.close()

        except Exception, e:
            print e
            print "Unable to call 'cygpath' to determine DOS-equivalent for PATH"
            print "Either make sure that 'cygpath' is in your PATH or run the Windows version"
            print "of Python from http://python.org/, rather than the Cygwin Python"
            raise HardHatError

    os.putenv('PATH', path)
    os.putenv('PYTHONPATH', pythonpath)

    if buildenv['os'] == 'posix':
        ld_library_path = os.getenv('LD_LIBRARY_PATH', '')
        ver = buildenv['version']
        additional_paths = [ os.path.join(CHANDLERBIN, ver, 'lib'),
                             os.path.join(CHANDLERBIN, ver, 'db', 'lib'),
                             os.path.join(CHANDLERBIN, ver, 'icu', 'lib'),
                             ld_library_path ]
        ld_library_path = os.pathsep.join(additional_paths)
        os.putenv('LD_LIBRARY_PATH', ld_library_path)

    if buildenv['os'] == 'osx':
        dyld_library_path = os.getenv('DYLD_LIBRARY_PATH', '')
        ver = buildenv['version']
        additional_paths = [ os.path.join(CHANDLERBIN, ver, 'lib'),
                             os.path.join(CHANDLERBIN, ver, 'db', 'lib'),
                             os.path.join(CHANDLERBIN, ver, 'icu', 'lib'),
                             dyld_library_path ]
        dyld_library_path = os.pathsep.join(additional_paths)
        os.putenv('DYLD_LIBRARY_PATH', dyld_library_path)

        dyld_framework_path = os.getenv('DYLD_FRAMEWORK_PATH', '')
        additional_paths = [ os.path.join(CHANDLERBIN, ver, 'Library',
                                          'Frameworks'),
                             dyld_framework_path ]
        dyld_framework_path = os.pathsep.join(additional_paths)
        os.putenv('DYLD_FRAMEWORK_PATH', dyld_framework_path)

def quoteString(str):
    return "\'" + str + "\'"

def escapeSpaces(str):
    return str.replace(" ", "|")

def escapeBackslashes(str):
    return str.replace("\\", "\\\\")

HARDHAT_NO_RAISE_ON_ERROR = 1

def executeCommand(buildenv, name, args, message, flags=0, extlog=None):

    setupEnvironment(buildenv)

    wrapper = buildenv['hardhatroot'] + os.sep + "wrapper.py"
    logfile = buildenv['logfile']

    if buildenv['showenv']:
        showenv = "yes"
    else:
        showenv = "no"

    if showenv == "yes":
        print "incoming args:"
        for arg in args:
            print arg
        print "PYTHONPATH is", os.getenv('PYTHONPATH')
        print "PYTHONHOME is", os.getenv('PYTHONHOME')
        print "PATH is", os.getenv('PATH')

    # spawnl wants the name of the file we're executing twice -- however,
    # on windows the second one can't have spaces in it, so we just pass
    # in the basename()
    if buildenv['os'] == 'win' and sys.platform != 'cygwin':
        # args[0] is the path to the exe we want wrapper to run.  If it has
        # a space in it, it doesn't get passed to wrapper correctly (under
        # windows), so convert spaces to pipes (which windows filenames
        # aren't allowed to contain).  These will then get converted back
        # to spaces inside wrapper.py
        args[0] = escapeSpaces(args[0])
        args[:0] = [sys.executable, os.path.basename(sys.executable), wrapper, 
         logfile, showenv]
    else:
        args[:0] = [sys.executable, sys.executable, wrapper, 
         logfile, showenv]
    args = map(escapeBackslashes, args)

    if not os.path.exists(args[0]):
        log(buildenv, HARDHAT_ERROR, name, "Program does not exist: " + \
         args[0])
        if not (flags & HARDHAT_NO_RAISE_ON_ERROR):
            raise HardHatExternalCommandError
        return 127 # standard not found exit code

    # all args need to be quoted
    args = map(quoteString, args)

    args_str = ','.join(args)
    execute_str = "exit_code = os.spawnl(os.P_WAIT," + args_str + ")"
    if showenv == "yes":
        print execute_str

    log(buildenv, HARDHAT_MESSAGE, name, message)
    
    exec(execute_str)

    if extlog:
        # The program just executed put its output to an external log file
        # (specifically this is for Visual Studio, which apparently doesn't
        # want to send output to stdout).  Read the external log file and
        # inject it into our hardhat log.
        try:
            extlogfile = file(extlog, 'r')
            lines = extlogfile.readlines()
            buildlog = file(buildenv['logfile'], 'a+', 0)
            for line in lines:
                buildlog.write(line)
            extlogfile.close()

        except Exception, e:
            log(buildenv, HARDHAT_ERROR, name, "Trouble opening " + extlog + \
             ":" + str(e))
       

    if exit_code == 0:
        log(buildenv, HARDHAT_MESSAGE, name, "OK")
    else:
        log(buildenv, HARDHAT_ERROR, name, "Exit code = " + str(exit_code) )
        if not (flags & HARDHAT_NO_RAISE_ON_ERROR):
            raise HardHatExternalCommandError
    
    return exit_code


def executeCommandNoCapture(buildenv, name, args, message, flags=0):

    setupEnvironment(buildenv)

    # spawnl wants the name of the file we're executing twice -- the first
    # one is the full path, the second is just the filename
    if buildenv['os'] == 'win' and sys.platform != 'cygwin':
        args[1:0] = [ os.path.basename(args[0]) ]
    else:
        args[:0] = [ args[0] ]
    args = map(escapeBackslashes, args)

    # all args need to be quoted
    args = map(quoteString, args)

    args_str = ','.join(args)
    execute_str = "exit_code = os.spawnl(os.P_WAIT," + args_str + ")"

    log(buildenv, HARDHAT_MESSAGE, name, message)
    log(buildenv, HARDHAT_MESSAGE, name, ",".join(args[0:]))
    

    print "\nExecution output - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n"
    exec(execute_str)
    print "\nExecution complete - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n"

    if exit_code == 0:
        log(buildenv, HARDHAT_MESSAGE, name, "OK")
    else:
        log(buildenv, HARDHAT_ERROR, name, "Command exited with code = " + str(exit_code) )
        if not (flags & HARDHAT_NO_RAISE_ON_ERROR):
            raise HardHatExternalCommandError
    
    return exit_code


def executeShell(buildenv):

    setupEnvironment(buildenv)

    shell = os.environ['SHELL']
    args = [shell]
    name = "HardHat"
    message = "Running shell"

    os.putenv('PROMPT', "HardHat Shell>")

    # spawnl wants the name of the file we're executing twice
    args[:0] = [ args[0] ]
    args = map(escapeBackslashes, args)

    if buildenv['os'] == 'win':
        args = map(escapeArgForWindows, args)

    # all args need to be quoted
    args = map(quoteString, args)

    args_str = ','.join(args)
    execute_str = "exit_code = os.spawnl(os.P_WAIT," + args_str + ")"

    log(buildenv, HARDHAT_MESSAGE, name, message)
    log(buildenv, HARDHAT_MESSAGE, name, ",".join(args[1:]))
    
    print execute_str

    print "\nYou are now in an interactive shell; don't forget to 'exit' when done"
    exec(execute_str)
    print "\nBack from interactive shell"

    if exit_code == 0:
        log(buildenv, HARDHAT_MESSAGE, name, "OK")
    else:
        log(buildenv, HARDHAT_ERROR, name, "Exit code = " + str(exit_code) )
    
    return exit_code


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Manifest processing functions

# A manifest file describes which files to copy and where they should go in
# order to create a binary distribution.  Comments are denoted by #; empty
# lines are skipped.  There are five "variables" that you set in order to
# control what's going on:  src, dest, recursive, exclude and glob.  The file
# is processed sequentially; variables maintain their values until reassigned.
# The "src" variable should be set to a path relative to buildenv['root'],
# and "dest" should be set to a path relative to buildenv['distdir']; either
# can be set to an empty string (e.g. "dest=").  When a non-assignment line
# is reached (meaning it doesn't have an "=" in it), that line is assumed
# to represent a path relative to "src".  If a file exists there, that file
# is copied to the "dest" directory; if instead a directory exists there, 
# then the patterns specified in the most recent "glob" line are used to
# look for matching files to copy.  Then if "recursive" is set to "yes",
# subdirectories are recursively copied (but only the files matching the
# current pattern). If any file or directory matches any pattern in the 
# "excludes" parameter/list, it is skipped.

def handleManifest(buildenv, filename, fatalErrors=True):

    params = {}
    params["src"] = None
    params["dest"] = None
    params["recursive"] = True
    params["glob"] = "*"
    params["exclude"] = "\.svn"
    srcdir = buildenv['root']
    destdir = buildenv['distdir']

    if fatalErrors:
        hhMsg = HARDHAT_ERROR
    else:
        hhMsg = HARDHAT_WARNING
        
    for line in fileinput.input(filename):
        line = line.strip()
        if len(line) == 0:
            continue
        if line[0:1] == "#":
            continue

        line = expandVars(line)

        if line.find("=") != -1:
            (name,value) = line.split("=")
            params[name] = value
            if name == "src":
                srcdir = os.path.join(buildenv['root'],value)
                log(buildenv, HARDHAT_MESSAGE, "HardHat", "src=" + srcdir)
            if name == "dest":
                destdir = os.path.join(buildenv['distdir'],value)
                log(buildenv, HARDHAT_MESSAGE, "HardHat", "dest=" + destdir)
            if name == "glob":
                params['glob'] = value.split(",")
                log(buildenv, HARDHAT_MESSAGE, "HardHat", "pattern=" + value)
            if name == "recursive":
                if value == "yes":
                    params["recursive"] = True
                else:
                    params["recursive"] = False
                log(buildenv, HARDHAT_MESSAGE, "HardHat", "recursive=" + value)
            if name == "exclude":
                params["exclude"] = value.split(",")
                log(buildenv, HARDHAT_MESSAGE, "HardHat", "exclude=" + value)
        else:
            abspath = os.path.join(srcdir,line)
            if os.path.isdir(abspath):
                log(buildenv, HARDHAT_MESSAGE, "HardHat", abspath)
                copyto = os.path.join(buildenv['distdir'], params["dest"], line)
                _copyTree(abspath, copyto, params["recursive"], params["glob"], params["exclude"])
            else:
                if os.path.exists(abspath):
                    log(buildenv, HARDHAT_MESSAGE, "HardHat", abspath)
                    copyto = os.path.join(buildenv['distdir'], params["dest"],
                     line)
                    createpath = os.path.dirname(copyto)
                    mkdirs(createpath)
                    if os.path.islink(abspath):
                        linkto = os.readlink(abspath)
                        os.symlink(linkto, copyto)
                    else:
                        shutil.copy(abspath, copyto)
                else:
                    log(buildenv, hhMsg, "HardHat", "File missing: " 
                     + abspath)
                    if fatalErrors:
                        raise HardHatError, 'File missing: ' + abspath
                    else:
                        continue

#expand $(VAR) with value of VAR environment variable
#expand ${program} with full path of directory containing program from PATH

def expandVars(line):

    def replaceVars(line, op, cl, fn):
        
        start = 0
        while True:
            start = line.find(op, start)
            if start == -1:
                return line
            end = line.find(cl, start)
            if end == -1:
                return line

            var = line[start+len(op):end]
            var = fn(var)

            if var is not None:
                line = "%s%s%s" %(line[0:start], var, line[end+len(cl):])
            else:
                start = start + len(op)

    def pathFind(var):

        path = os.getenv('PATH')
        if path is not None:
            for p in path.split(os.pathsep):
                program = os.path.join(p, var)
                if os.path.isfile(program):
                    return p

        return None

    line = replaceVars(line, '$(', ')', os.getenv)
    line = replaceVars(line, '${', '}', pathFind)

    return line
    

def _copyTree(srcdir, destdir, recursive, patterns, excludes):
    """
       This function implements a directory-tree copy
       from one place (srcdir) to another (destdir),
       whether it should be recursive, 
       what file patterns to copy (may be a list),
       and what file patterns to exclude (may be a list)
    """
    os.chdir(srcdir)
    # iterate over the file patterns to be copied
    for pattern in patterns:
        # matches contains a list of files matching the current pattern
        matches = glob.glob(pattern)
        excludesMatch = []
        # prepare a list of files to be excluded
        for filePat in excludes:
            # add to the excludes list all files in the match list which match the current exclude pattern
            excludesMatch += fnmatch.filter(matches, filePat)
            # (debug) display current excludes list
            # print "%s matches %s " % (excludesMatch, filePat)

        # (debug) display current excludes list
        # print "excluding %s for %s " % (excludesMatch, srcdir)

        # iterate over the match list for each file
        for match in matches:
            # if the current match is a file that is NOT in the excludes list, then try to copy
            if os.path.isfile(match) and not match in excludesMatch:
                try:
                    if not os.path.exists(destdir):
                        mkdirs(destdir)
                    if os.path.islink(match):
                        linkto = os.readlink(match)
                        os.symlink(linkto, os.path.join(destdir,match))
                    else:
                        shutil.copy(match, destdir)
                except (IOError, os.error), why:
                    print "Can't copy %s to %s: %s" % (match, destdir, str(why))
    if recursive:
        for name in os.listdir(srcdir):
            full_name = os.path.join(srcdir, name)
            # we are only checking one pattern here; 
            # directory excludes so far only being for one pattern - .svn
            # if we need to add more, this will have to change to match method of file excludes above
            if os.path.isdir(full_name) and not name in excludes:
                _copyTree(full_name, os.path.join(destdir, name), True, 
                 patterns, excludes)

def mkdirs(newdir, mode=0777):
    try: 
        os.makedirs(newdir, mode)
    except OSError, err:
        # Reraise the error unless it's about an already existing directory 
        if err.errno != errno.EEXIST or not os.path.isdir(newdir): 
            raise

def copyFile(srcfile, destdir):
    mkdirs(destdir)
    shutil.copy(srcfile, destdir)


def copyFiles(srcdir, destdir, patterns):
    for pattern in patterns:
        matches = glob.glob(os.path.join(srcdir, pattern))
        for match in matches:
            if os.path.isfile(match):
                if not os.path.exists(destdir):
                    mkdirs(destdir)
                shutil.copy(match, destdir)

def copyTree(srcdir, destdir, patterns, excludes):
    """
       This function implements a directory-tree copy
       from one place (srcdir) to another (destdir),
       whether it should be recursive, 
       what file patterns to copy (may be a list),
       and what file patterns to exclude (may be a list)
    """
    # iterate over the file patterns to be copied
    for pattern in patterns:
        # matches contains a list of files matching the current pattern
        matches = glob.glob(os.path.join(srcdir, pattern))
        excludesMatch = []
        # prepare a list of files to be excluded
        for filePat in excludes:
            # add to the excludes list all files in the match list which match the current exclude pattern
            excludesMatch += fnmatch.filter(matches, filePat)
            # (debug) display current excludes list
            # print "%s matches %s " % (excludesMatch, filePat)

        # (debug) display current excludes list
        # print "excluding %s for %s " % (excludesMatch, srcdir)

        # iterate over the match list for each file
        for match in matches:
            # if the current match is a file that is NOT in the excludes list, then try to copy
            if os.path.isfile(match) and not match in excludesMatch:
                try:
                    if not os.path.exists(destdir):
                        mkdirs(destdir)
                    if os.path.islink(match):
                        linkto = os.readlink(match)
                        os.symlink(linkto, os.path.join(destdir,match))
                    else:
                        shutil.copy(match, destdir)
                except (IOError, os.error), why:
                    print "Can't copy %s to %s: %s" % (match, destdir, str(why))
    for name in os.listdir(srcdir):
        fullpath = os.path.join(srcdir, name)
        # we are only checking one pattern here; 
        # directory excludes so far only being for one pattern - .svn
        # if we need to add more, this will have to change to match method of file excludes above
        if os.path.isdir(fullpath) and not fnmatch.fnmatch(name, excludes):
            copyTree(fullpath, os.path.join(destdir, name), patterns, excludes)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# SVN-cleaning methods

def svnFindRemovables(dir):
    """ Find all files in the given directory (and its children) that aren't 
    checked into SVN and return them in a list """

    removables = []
    dir = os.path.abspath(dir)
    svnEntriesFile = os.path.join(dir, ".svn", "entries")
    if(os.path.isfile(svnEntriesFile)):

        """
        According to http://www.cvshome.org/docs/manual/cvs_2.html#IDX42
        you will find an Entries file inside CVS/ and possibly an Entries.log
        file.  Files/dirs listed in Entries are considered to be under CVS
        control, and are added to our cvsFiles dict.
        Next, if Entries.log exists, all lines beginning with "A " are
        treated as if they were read from Entries.  All lines beginning with
        "R " have been removed from CVS, so lines from the Entries.log file
        modify the cvsFiles dict accordingly.  
        Once we have the list of CVS files, each local file is compared
        to that list and those not under CVS control are added to the
        removeables list.
        """

        svnFiles = {}
        for line in fileinput.input(svnEntriesFile):
            line = line.strip()
            fields = line.split("=")
            if len(fields) > 1 and fields[1]:
                svnFiles[fields[1][1:-1]] = 1 # this one is in SVN

        for file in os.listdir(dir):
            if file != ".svn": # always skip ".svn" directory
                absFile = os.path.join(dir,file)
                if not svnFiles.has_key(file) or not svnFiles[file]:
                    # not in svn, so add to removeables
                    removables.append(absFile)
                else:
                    # if in SVN, see if a directory and recurse
                    if os.path.isdir(absFile):
                        childremovables = svnFindRemovables(absFile)
                        removables += childremovables
    else:
        print "Did not find .svn/entries file in", dir

    return removables

def svnClean(buildenv, dirs):
    allRemovables = []
    for dir in dirs:
        dir = os.path.abspath(dir)
        log(buildenv, HARDHAT_MESSAGE, "HardHat", "Examining " + dir + "...")
        removables = svnFindRemovables(dir)
        allRemovables += removables
    allRemovables.sort()
    if len(allRemovables) == 0:
        log(buildenv, HARDHAT_MESSAGE, "HardHat", "No local files to remove")
        return

    if buildenv['interactive']:
        print
        print "The following files and directories are not in SVN:"
        print
        for removable in allRemovables:
            print removable
        print
        yn = raw_input("Would you like to remove these files?  y/n: ")
    else:
        yn = "y"

    if yn == "y" or yn == "Y":
        log(buildenv, HARDHAT_MESSAGE, "HardHat", "Removing files...")
        for removable in allRemovables:
            log(buildenv, HARDHAT_MESSAGE, "HardHat", removable)
            if os.path.isdir(removable):
                rmdir_recursive(removable)
            elif os.path.isfile(removable) or os.path.islink(removable):
                os.remove(removable)
            elif not os.path.exists(removable):
                log(buildenv, HARDHAT_WARNING, "HardHat", "Tried to remove "+\
                 removable +" but it doesn't exist")

        log(buildenv, HARDHAT_MESSAGE, "HardHat", "Files removed")
    else:
        log(buildenv, HARDHAT_MESSAGE, "HardHat", "Not removing files")

# - - - - - - -
def compressDirectory(buildenv, directories, fileRoot):
    """This assumes that directory is an immediate child of the current dir"""
    if buildenv['os'] == 'win':
        executeCommand(buildenv, "HardHat",
         [buildenv['zip'], "-r", fileRoot + ".zip"] + directories,
        "Zipping up to " + fileRoot + ".zip")
        return fileRoot + ".zip"
    else:
        executeCommand(buildenv, "HardHat",
         [buildenv['tar'], "cf", fileRoot+".tar"] + directories,
        "Tarring to " + fileRoot + ".tar")
        executeCommand(buildenv, "HardHat", 
         [buildenv['gzip'], "-f", fileRoot+".tar"],
        "Running gzip on " + fileRoot + ".tar")
        return fileRoot + ".tar.gz"

def makeInstaller(buildenv, directories, fileRoot, majorVersion='0', minorVersion='0', releaseVersion='1'):
    """
    This assumes that directory is an immediate child of the current dir
    """
        # TODO: OS X (dmg?) support
    if buildenv['os'] == 'win':
        if not buildenv['makensis']:
            raise hardhatutil.CommandNotFound, 'makensis'
        nsisScriptPath = os.path.join(buildenv['root'], "internal", "installers", "win")
        scriptOption   = '/DSNAP_%s /DDISTRIB_DIR=%s /DDISTRIB_VERSION=%s.%s-%s' % \
                          (buildenv['version'].upper(), fileRoot, majorVersion, minorVersion, releaseVersion)

        if sys.platform == 'cygwin':
          scriptName = os.path.join(nsisScriptPath, "makeinstaller.sh")
          executeCommand(buildenv, "HardHat", 
             [scriptName, scriptOption, nsisScriptPath, "chandler.nsi"],
             "Building Windows Installer")
        else:
            executeCommand(buildenv, "HardHat",
                 [buildenv['makensis'], scriptOption, os.path.join(nsisScriptPath, "chandler.nsi")],
                 "Building Windows Installer")

        installTargetFile = '%s.exe' % fileRoot
        installTarget     = os.path.join(buildenv['root'], installTargetFile)

        if os.path.exists(installTarget):
            os.remove(installTarget)

        os.rename(os.path.join(nsisScriptPath, 'Setup.exe'), installTarget)

    elif buildenv['os'] == 'posix':
        specPath   = os.path.join(buildenv['root'], "internal", "installers", "rpm")
        scriptName = os.path.join(specPath, "makeinstaller.sh")
        version    = '%s.%s' % (majorVersion, minorVersion)

        executeCommand(buildenv, "HardHat",
             [scriptName, specPath, os.path.join(specPath, "chandler.spec"), buildenv['root'], fileRoot, version, releaseVersion],
             "Building Linux (RPM) Installer")

        installTargetFile = '%s.i386.rpm' % fileRoot
        
    return installTargetFile

def convertLineEndings(srcdir):
    """Convert all .txt files in the distribution root to DOS style line endings"""
    for name in os.listdir(srcdir):
        fullpath = os.path.join(srcdir, name)
        if os.path.isdir(fullpath):
            convertLineEndings(fullpath)
        else:
            if fnmatch.fnmatch(name, "*.txt"):
                if os.path.isfile(fullpath):
                    text    = open(fullpath, "rb").read()
                    newtext = text.replace("\n", "\r\n")
                    if newtext != text:
                        f = open(fullpath, "wb")
                        f.write(newtext)
                        f.close()
 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Exception Classes

class HardHatError(Exception):
    """ General HardHat exception; more specific errors subclass this. """
    pass

class HardHatBuildEnvError(Exception):
    """ Exception thrown when the buildenv has invalid or missing values. """
    
    def __init__(self,args=None):
        self.args = args

class HardHatInspectionError(HardHatError):
    """ Exception thrown when the system fails inspection. """
    pass

class HardHatMissingCompilerError(HardHatError):
    """ Exception thrown when a compiler cannot be located. """
    pass

class HardHatUnknownPlatformError(HardHatError):
    """ Exception thrown when run on an unsupported platform. """
    pass

class HardHatExternalCommandError(HardHatError):
    """ Exception thrown when an external command returns non-zero exit code """
    pass

class HardHatRegistryError(HardHatError):
    """ Exception thrown when we can't read the windows registry """
    pass

class HardHatUnitTestError(HardHatError):
    """ Exception thrown when at least one unit test fails """
    pass

class HardHatMissingFileError(HardHatError):
    """ Exception thrown when a __hardhat__.py file cannot be found. """

    def __init__(self,args=None):
        self.args = args

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -




