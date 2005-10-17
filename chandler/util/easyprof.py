
import hotshot
from time import clock
from datetime import timedelta

class Profile(object):
    """
    A quick 'n easy class for profiling a set of methods in a file

    Simple use::

        p = Profile('mymethods.prof')

        class A(object)::
            @p.profiled
            def SomeMethod(self, ...)

            @p.profiled
            def AnotherMethod(self, ...)
    """
    
    def __init__(self, profilefile):
        
        self.profiler = hotshot.Profile(profilefile)
        self.profiler_active = False

    def profiled(self, method):
        def profile_me(*args, **kwds):
            if self.profiler_active:
                method(*args, **kwds)
            else:
                self.profiler_active = True
                self.profiler.runcall(method, *args, **kwds)
                self.profiler_active = False
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
        print "Call to %s = %.3f" % (method.__name__, newtime-oldtime)
        return result
    timed_call.__name__ = method.__name__
    return timed_call

