
import hotshot

class Profile(object):
    """
    A quick 'n easy class for profiling a set of methods in a file

    Simple use:

    p = Profile('mymethods.prof')

    class A(object):
        @p.profiled
        def SomeMethod(self, ...)

        @p.profiled
        def AnotherMethod(self, ...)
    """
    
    def __init__(self, profilefile):
        
        self.profiler = hotshot.Profile(profilefile)

    def profiled(self, method):
        def profile_me():
            self.profiler.runcall(method)
        return profile_me

def QuickProfile(profilefile):
    """
    A quick 'n dirty way to profile a single method

    use:

    class B(object):
        @QuickProfile('mymethods.prof')
        def SomeMethod(self, ...)

    """

    profile = hotshot.Profile(profilefile)
    def profiled_descriptor(method):
        """
        Descriptor which returns a function that should be called
        """
        def profiled_caller(*args):
            """
            Wrapper which actually calls the profiler
            """
            profile.runcall(method, *args)
        return profiled_caller

    return profiled_descriptor

