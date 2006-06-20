
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


import os, sys, time, sha, md5
from stat import *

def findInPath(path, fileName, strict=1):
    """
    Find filename in path.
    """
    dirs = path.split(os.pathsep)
    for dir in dirs:
        if os.path.isfile(os.path.join(dir, fileName)):
            return os.path.join(dir, fileName)
        if os.name == 'nt' or sys.platform == 'cygwin':
            if os.path.isfile(os.path.join(dir, fileName + ".exe")):
                return os.path.join(dir, fileName + ".exe")
    if strict:
        raise CommandNotFound, fileName
        
    return None


def rmdirRecursive(dir):
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
            rmdirRecursive(full_name)
        else:
            # print "removing file", full_name
            os.remove(full_name)
    os.rmdir(dir)
# rmdirRecurisve()

def quoteString(str):
    return "\'" + str + "\'"

def escapeSpaces(str):
    return str.replace(" ", "|")

def escapeBackslashes(str):
    return str.replace("\\", "\\\\")


def executeCommandReturnOutputRetry(args):

    args[0] = escapeSpaces(args[0])
    args = map(escapeBackslashes, args)

    if not os.path.exists(args[0]):
        raise CommandNotFound

    # all args need to be quoted
    # args = map(quoteString, args)

    args_str = ' '.join(args)
    # print args_str

    attempt = 1
    while attempt <= 5:
        output = os.popen(args_str, "r")
        outputList = output.readlines()
        exitCode = output.close()
        if exitCode == None:
            return outputList
        print "Command failed with exit code", exitCode
        print "Waiting 30 seconds..."
        time.sleep(30)
        print "Retrying command"
        attempt += 1

    raise ExternalCommandError, exitCode


def executeCommandReturnOutput(args):
    args[0] = escapeSpaces(args[0])
    args = map(escapeBackslashes, args)

    if not os.path.exists(args[0]):
        raise CommandNotFound

    # all args need to be quoted
    # args = map(quoteString, args)

    args_str = ' '.join(args)
    print args_str

    if os.name not in ['nt', 'os2']:
        import popen2
        p = popen2.Popen4(args_str)
        p.tochild.close()
        outputList = p.fromchild.readlines()
        exitCode = p.wait()
        if exitCode == 0:
            exitCode = None
        else:
            exitCode >>= 8
    else:
        i,k = os.popen4(args_str)
        i.close()
        outputList = k.readlines()
        exitCode = k.close()
        
    if exitCode is not None:
        raise ExternalCommandErrorWithOutputList, [exitCode, outputList]

    return outputList

def dumpOutputList(outputList, fd = None):
    for line in outputList:
        print "   "+ line,
        if fd:
            fd.write(line)
    print

class MissingFileError(Exception):
    """ Exception thrown when we can't find a file """
    pass

class CommandNotFound(Exception):
    """ Exception thrown when we can't find the program to run """
    pass

class ExternalCommandError(Exception):
    """ Exception thrown an external command exits with nonzero """

    def __init__(self,args=None):
        self.args = args


class ExternalCommandErrorWithOutputList(ExternalCommandError):
    def __init__(self,args=None):
        if args:
            self.args = args[0]
            self.outputList = args[1]
        else:
            self.args = args
            self.outputList = []
                                                    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Module import functions

def ModuleFromFile(module_path, module_name):
    """ 
    Load a module from a file into a code object.
    Parameters:
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
        raise MissingFileError, "Missing " + module_path
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

def RemovePunctuation(str):
    s = str.replace("-", "")
    s = s.replace(" ", "")
    s = s.replace(":", "")
    return s


def _checksum(hashobj, filename):
    fileobj = open(filename)
    filedata = fileobj.read()
    fileobj.close()
    hashobj.update(filedata)
    return hashobj.hexdigest()
    

def MD5sum(filename):
    """Compute MD5 checksum for the file
    """
    return _checksum(md5.new(), filename)


def SHAsum(filename):
    """Compute SHA-1 checksum for the file
    """
    return _checksum(sha.new(), filename)


def fileSize(filename, humanReadable=1):
    """
    Get file size, and return it as string either directly converted to
    string or in "human readable" format where we return the file size in
    megabytes, kilobytes or bytes depending on the file size.

    Size of 0 will be reported for directories.
    """
    size = os.stat(filename)[ST_SIZE]
    if not humanReadable:
        return str(size)
    
    if size > 1024*1000:
        return '%.1f MB' % (size / (1024 * 1000.0))
    elif size > 1024:
        return '%.1f KB' % (size / 1024.0)
    return '%d B' % size
