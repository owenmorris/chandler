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

import hotshot
from time import clock
from datetime import timedelta

class Profile(object):
    """
    A quick 'n easy class for profiling a set of methods in a file

    Simple use::

        profiled = Profile('mymethods.prof')

        class A(object)::
            @profiled
            def SomeMethod(self, ...):

            @profiled
            def AnotherMethod(self, ...):
    """
    
    def __init__(self, profilefile):
        
        self.profiler = hotshot.Profile(profilefile)
        self.profiler_active = False

    def __call__(self, method):
        def profile_me(*args, **kwds):
            # Make sure we actually return the original
            # method's return value.
            if self.profiler_active:
                result = method(*args, **kwds)
            else:
                self.profiler_active = True
                result = self.profiler.runcall(method, *args, **kwds)
                self.profiler_active = False
            return result
        profile_me.__name__ = method.__name__
        return profile_me

def QuickProfile(profilefile):
    """
    A quick 'n dirty way to profile a single method

    use::

        class B(object)::
            @QuickProfile('mymethods.prof')
            def SomeMethod(self, ...)
    """

    profile = hotshot.Profile(profilefile)
    def profiled_descriptor(method):
        """
        Descriptor which returns a function that should be called
        """
        def profiled_caller(*args, **kwds):
            """
            Wrapper which actually calls the profiler
            """
            profile.runcall(method, *args, **kwds)
        return profiled_caller

    return profiled_descriptor

def Timed(method):
    def timed_call(*args, **kwds):
        oldtime = clock()
        result = method(*args, **kwds)
        newtime = clock()
        print "Call to %s = %.3fs" % (method.__name__, newtime-oldtime)
        return result
    timed_call.__name__ = method.__name__
    return timed_call

