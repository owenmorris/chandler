
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


"""
  Much of this code was taken from distutils.msvccompiler
"""

import sys, os, string, types, commands
from types import *
import hardhatlib

"""
  Cygwin doesn't support _winreg yet, but they have implemented a readonly
filesystem view of the registry named "/proc/registry". However, we do a
lame implementation of the _winreg api in cygwinreg, that will work in a pinch
"""
if os.path.exists("/proc/registry"):
    registryModuleName = 'cygwinreg'
    _cygwin = True
else:
    registryModuleName = '_winreg'
    _cygwin = False

hkey_mod = __import__(registryModuleName, globals(), locals())

RegOpenKeyEx = hkey_mod.OpenKeyEx
RegEnumKey = hkey_mod.EnumKey
RegEnumValue = hkey_mod.EnumValue
RegError = hkey_mod.error

HKEYS = (hkey_mod.HKEY_USERS,
         hkey_mod.HKEY_CURRENT_USER,
         hkey_mod.HKEY_LOCAL_MACHINE,
         hkey_mod.HKEY_CLASSES_ROOT)

def read_keys(base, key):
    """Return list of registry keys."""

    try:
        handle = RegOpenKeyEx(base, key)
    except RegError:
        return None
    L = []
    i = 0
    while 1:
        try:
            k = RegEnumKey(handle, i)
        except RegError:
            break
        L.append(k)
        i = i + 1
    return L

def read_values(base, key):
    """Return dict of registry keys and values.

    All names are converted to lowercase.
    """
    def convert_mbcs(s):
        enc = getattr(s, "encode", None)
        if enc is not None:
            try:
                s = enc("mbcs")
            #cygwin fails with AttributeError and LookupError
            except (UnicodeError, AttributeError, LookupError):
                pass
        return s

    try:
        handle = RegOpenKeyEx(base, key)
    except RegError:
        return None
    d = {}
    i = 0
    while 1:
        try:
            name, value, type = RegEnumValue(handle, i)
        except RegError:
            break
        d[convert_mbcs(name.lower())] = convert_mbcs(value)
        i = i + 1
    return d

class MacroExpander:

    def __init__(self, version):
        self.macros = {}
        self.load_macros(version)

    def set_macro(self, macro, path, key):
        for base in HKEYS:
            d = read_values(base, path)
            if d:
                self.macros["$(%s)" % macro] = d[key]
                break
              
    def load_macros(self, version):
        vsbase = r"Software\Microsoft\VisualStudio\%0.1f" % version
        self.set_macro("VCInstallDir", vsbase + r"\Setup\VC", "productdir")
        self.set_macro("VSInstallDir", vsbase + r"\Setup\VS", "productdir")
        net = r"Software\Microsoft\.NETFramework"
        self.set_macro("FrameworkDir", net, "installroot")
        if version > 7.0:
            self.set_macro("FrameworkSDKDir", net, "sdkinstallrootv1.1")
        else:
            self.set_macro("FrameworkSDKDir", net, "sdkinstallroot")

        p = r"Software\Microsoft\NET Framework Setup\Product"
        for base in HKEYS:
            try:
                h = RegOpenKeyEx(base, p)
            except RegError:
                continue
            key = RegEnumKey(h, 0)
            d = read_values(base, r"%s\%s" % (p, key))
            self.macros["$(FrameworkVersion)"] = d["version"]

    def sub(self, s):
        for k, v in self.macros.items():
            s = string.replace(s, k, v)
        return s


class VisualStudio:
    """Allows access to Microsoft Visual Studio C++ paths"""

    def __init__ (self):
        # Find the newest version of Visual Studio that's installed
        self.version = 0
        self.Found = False
        
        for base in HKEYS:
            d = read_keys(base, r"Software\Microsoft\VisualStudio")
            if d:
                for value in d:
                    key = (r"Software\Microsoft\VisualStudio\%s" % (value))
                    d2 = read_values(base, key)
                    try:
                        if d2["installdir"]:
                            try:
                                number = float (value)
                            except ValueError:
                                pass
                            else:
                                if number > self.version:
                                    self.version = number
                    except KeyError:
                        pass

        if self.version:
            self.Found = True
            
            if self.version >= 7:
                self._root = r"Software\Microsoft\VisualStudio"
                self._macros = MacroExpander(self.version)
            else:
                self._root = r"Software\Microsoft\Devstudio"

    def get_msvc_paths(self, path):
        """Get a list of devstudio directories (include, lib or path).
    
        Return a list of strings.  The list will be empty if unable to
        access the registry or appropriate registry keys not found.
        """
    
        path = path + " dirs"
        if self.version >= 7:
            key = (r"%s\%0.1f\VC\VC_OBJECTS_PLATFORM_INFO\Win32\Directories"
                   % (self._root, self.version))
        else:
            key = (r"%s\6.0\Build System\Components\Platforms"
                   r"\Win32 (x86)\Directories" % (self._root))
    
        for base in HKEYS:
            d = read_values(base, key)
            if d:
                if self.version >= 7:
                    return string.split(self._macros.sub(d[path]), ";")
                else:
                    return string.split(d[path], ";")
        return []


    def find_exe (self, exe):
        """Try to find an MSVC executable program 'exe' otherwise
        return None
        """
        for p in self.get_msvc_paths ('path'):
            if _cygwin:
                status, p = commands.getstatusoutput('cygpath -a "' + p + '"')
            else:
                p = os.path.abspath(p)
            fn = os.path.join (p, exe)
            if os.path.isfile(fn):
                return fn
    
        return None
