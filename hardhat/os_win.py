__version__ 	= "$Revision$"
__date__ 	= "$Date$"
__copyright__ 	= "Copyright (c) 2003 Open Source Applications Foundation"
__license__	= "GPL -- see LICENSE.txt"

"""distutils.msvccompiler

Contains MSVCCompiler, an implementation of the abstract CCompiler class
for the Microsoft Visual Studio."""


# created 1999/08/19, Perry Stoll
# hacked by Robin Becker and Thomas Heller to do a better job of
#   finding DevStudio (through the registry)
#
# Rehacked by John Anderson to fix problems with finding DevStudio
#   through the registry. Using the registry is always going to be
#   an inexact science, since Microsoft can always change how they
#   store data in the registry and the data in the registry isn't
#   documented.

__revision__ = "$Id$"

import sys, os, string
from types import *
import hardhatlib

_can_read_reg = 0
_use_cygwin_mode = 0

try:
    import _winreg

    _can_read_reg = 1
    hkey_mod = _winreg

    RegOpenKeyEx = _winreg.OpenKeyEx
    RegEnumKey = _winreg.EnumKey
    RegEnumValue = _winreg.EnumValue
    RegError = _winreg.error

except ImportError:
    try:
        import win32api
        import win32con
        _can_read_reg = 1
        hkey_mod = win32con

        RegOpenKeyEx = win32api.RegOpenKeyEx
        RegEnumKey = win32api.RegEnumKey
        RegEnumValue = win32api.RegEnumValue
        RegError = win32api.error

    except ImportError:
	try:
	    import cygwinreg
	    RegOpenKeyEx = cygwinreg.RegOpenKeyEx
	    RegEnumKey = cygwinreg.RegEnumKey
	    RegEnumValue = cygwinreg.RegEnumValue
	    RegError = cygwinreg.RegError
	    hkey_mod = cygwinreg
	    if cygwinreg.checkForRegistry():
		_can_read_reg = 1
		_use_cygwin_mode = 1
	    else:
		raise hardhatlib.HardHatRegistryError

	except:
	    raise hardhatlib.HardHatRegistryError


if _can_read_reg:
    HKEY_CLASSES_ROOT = hkey_mod.HKEY_CLASSES_ROOT
    HKEY_LOCAL_MACHINE = hkey_mod.HKEY_LOCAL_MACHINE
    HKEY_CURRENT_USER = hkey_mod.HKEY_CURRENT_USER
    HKEY_USERS = hkey_mod.HKEY_USERS



def get_devstudio_versions ():
    """Get list of devstudio versions from the Windows registry.  Return a
       list of strings containing version numbers; the list will be
       empty if we were unable to access the registry (eg. couldn't import
       a registry-access module) or the appropriate registry keys weren't
       found."""

    if not _can_read_reg:
        return []

    K = 'SOFTWARE\\Microsoft\\VisualStudio'
    L = []
    for base in (HKEY_CLASSES_ROOT,
                 HKEY_LOCAL_MACHINE,
                 HKEY_CURRENT_USER,
                 HKEY_USERS):
        try:
            k = RegOpenKeyEx(base,K)
            i = 0
            while 1:
                try:
                    p = RegEnumKey(k,i)
                    if p[0] in '123456789' and p not in L:
                        L.append(p)
                except RegError:
                    break
                i = i + 1
        except RegError:
            pass
    if not L:
        log.info("Warning: Can't find the Microsoft compiler in the registry")
    L.sort()
    L.reverse()
    return L

# get_devstudio_versions ()


def convert_mbcs (string):
    """Convert from multibyte character set (mbcs) if possible."""

    if hasattr(string, "encode"):
        try:
            string = string.encode("mbcs")
        except :
            pass
    return string
# convert_mbcs()


def read_key (base, key, lowerCaseKeys):
    """Open the registry key and returns a dictionary of the name values
       pairs. Converts all the names to lowerCaseKeys when lowerCaseKeys is true."""

    handle = RegOpenKeyEx(base, key)
    dict = {}
    i = 0
    while 1:
        try:
            (name, value, type) = RegEnumValue(handle, i)
	    if _use_cygwin_mode:
		name = string.strip(name)
		value = string.strip(value)
		name = remove_unprintable(name)
		value = remove_unprintable(value)
            if lowerCaseKeys:
                name = name.lower()
            dict[convert_mbcs(name)] = convert_mbcs(value)
        except RegError:
            break
        i = i + 1
    return dict
# read_key()


def remove_unprintable(str):
    new = []
    for c in str:
	if c in string.printable:
	    new.append(c)
    return string.join(new, "")


VC_INSTALL_DIR = "$(VCInstallDir)"
VS_INSTALL_DIR = "$(VSInstallDir)"
FRAMEWORK_DIR = "$(FrameworkDir)"
FRAMEWORK_SDK_DIR = "$(FrameworkSDKDir)"
FRAMEWORK_VERSION = "$(FrameworkVersion)"
_initializedMacros = 0

def expand_macros (string, base, version, numericVersion):
    """Expand macros of the form $(VCInstallDir), $(VCInstallDir),
       $(FrameworkDir), $(FrameworkSDKDir) in paths.
       The locations of these macros in the registry apparently are
       not documented, so they were determined by just looking around
       in regedit. Consequently """

    global _initializedMacros, VC_INSTALL_DIR, VS_INSTALL_DIR
    global FRAMEWORK_DIR, FRAMEWORK_SDK_DIR
    if numericVersion >= 7.0:
        if not _initializedMacros:
            try:
                _initializedMacros = 1

                key = ('SOFTWARE\\Microsoft\\VisualStudio\\%s\\Setup\\VC') % (version)
                pairs = read_key(base, key, 1)
                VC_INSTALL_DIR = pairs['productdir']

                key = ('SOFTWARE\\Microsoft\\VisualStudio\\%s\\Setup\\VS') % (version)
                pairs = read_key(base, key, 1)
                VS_INSTALL_DIR = pairs['productdir']

                pairs = read_key (base, 'SOFTWARE\\Microsoft\\.NETFramework', 1)
                FRAMEWORK_DIR = pairs['installroot']
                FRAMEWORK_SDK_DIR = pairs['sdkinstallroot']
        
                location = 'SOFTWARE\\Microsoft\\NET Framework Setup\\Product';
                handle = RegOpenKeyEx(base, location)
                key = RegEnumKey(handle, 0)
                pairs = read_key (base, location + '\\' + key, 1)
                FRAMEWORK_VERSION = pairs['version']

            except RegError:
                log.info("Warning: Can't read registry node: " + key)
            except KeyError:
                log.info("Warning: Can't read registry key:" + KeyError)
        string = string.replace ('$(VCInstallDir)', VC_INSTALL_DIR)
        string = string.replace ('$(VSInstallDir)', VS_INSTALL_DIR)
        string = string.replace ('$(FrameworkDir)', FRAMEWORK_DIR)
        string = string.replace ('$(FrameworkSDKDir)', FRAMEWORK_SDK_DIR)
    return string
# expand_macros()


def get_msvc_paths (path, version='6.0', platform='x86'):
    """Get a list of devstudio directories (include, lib or path).  Return
       a list of strings; will be empty list if unable to access the
       registry or appropriate registry keys not found."""

    if not _can_read_reg:
        return []

    L = []
    if path=='lib':
        path= 'Library'
    path = string.lower(path + ' Dirs')
    numericVersion = 6.0;
    try:
        numericVersion = float (version)
    except ValueError:
        pass
    
    if numericVersion < 7.0: 
        key = ('SOFTWARE\\Microsoft\\Devstudio\\%s\\'
               'Build System\\Components\\Platforms\\'
               'Win32 (%s)\\Directories') % (version, platform)
    else:
        key = ('SOFTWARE\\Microsoft\\VisualStudio\\%s\\'
               'VC\\VC_OBJECTS_PLATFORM_INFO\\Win32\\Directories') % (version)

    for base in (HKEY_CLASSES_ROOT,
                 HKEY_LOCAL_MACHINE,
                 HKEY_CURRENT_USER,
                 HKEY_USERS):
        try:
            pairs = read_key(base, key, 1)
            if pairs.has_key(path):
                for s in string.split(expand_macros(pairs[path],
                                                    base,
                                                    version,
                                                    numericVersion),';'):
                    if not (s in L):
                        L.append(s)
                break
        except RegError:
            pass
    return L

# get_msvc_paths()


def cygwin_path_convert(path):
    if path[1:3] == ":\\":
	path = path[0] + path[2:]
	path = "/cygdrive/" + path
	path = string.join(string.split(path, "\\"), "/")
    return path

def find_exe (exe, version_number):
    """Try to find an MSVC executable program 'exe' (from version
       'version_number' of MSVC) in several places: first, one of the MSVC
       program search paths from the registry; next, the directories in the
       PATH environment variable.  If any of those work, return an absolute
       path that is known to exist.  If none of them work, return None
    """

    for p in get_msvc_paths ('path', version_number):
	if _use_cygwin_mode:
	    fn = os.path.join (p, exe)
	    fn = cygwin_path_convert(fn)
	else:
            fn = os.path.join (os.path.abspath(p), exe)
        if os.path.isfile(fn):
            return fn

    # didn't find it; try existing path
    for p in string.split (os.environ['PATH'],';'):
        fn = os.path.join(os.path.abspath(p),exe)
        if os.path.isfile(fn):
            return fn

    return None                          # last desperate hope


def set_path_env_var (name, version_number):
    """Set environment variable 'name' to an MSVC path type value obtained
       from 'get_msvc_paths()'.  This is equivalent to a SET command prior
       to execution of spawned commands."""

    p = get_msvc_paths (name, version_number)
    if p:
        os.environ[name] = string.join (p,';')

