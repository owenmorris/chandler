import os, sys

def findInPath(path,fileName):
    dirs = path.split(os.pathsep)
    for dir in dirs:
        if os.path.isfile(os.path.join(dir, fileName)):
            return os.path.join(dir, fileName)
        if os.name == 'nt' or sys.platform == 'cygwin':
            if os.path.isfile(os.path.join(dir, fileName + ".exe")):
                return os.path.join(dir, fileName + ".exe")
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

def executeCommandReturnOutput(args):

    args[0] = escapeSpaces(args[0])
    args = map(escapeBackslashes, args)

    if not os.path.exists(args[0]):
        raise CommandNotFound

    # all args need to be quoted
    # args = map(quoteString, args)

    args_str = ' '.join(args)
    print args_str

    output = os.popen(args_str, "r")
    outputList = output.readlines()
    exitCode = output.close()

    if exitCode != None:
        raise ExternalCommandError, exitCode

    return outputList


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

