import re, sys

"""
adapted python cookbook: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/198078
usage: see the bottom of this file"""

#@@@ use the logging system...
log = sys.stdout

indent = 0
indStr = '  '


#ANSI escape codes for terminals.
#cygwin: run through |tee /dev/null and colors work
#linux: always works
#mac: untested
#less -r  understands escape codes (even if in logfile)

BLACK     =        "\033[0;30m"
BLUE      =        "\033[0;34m"
GREEN     =        "\033[0;32m"
CYAN      =       "\033[0;36m"
RED       =        "\033[0;31m"
PURPLE    =        "\033[0;35m"
BROWN     =        "\033[0;33m"
GRAY      =        "\033[0;37m"
BOLDGRAY  =       "\033[1;30m"
BOLDBLUE     =   "\033[1;34m"
BOLDGREEN    =   "\033[1;32m"
BOLDCYAN     =   "\033[1;36m"
BOLDRED      =   "\033[1;31m"
BOLDPURPLE   =   "\033[1;35m"
BOLDYELLOW   =         "\033[1;33m"
WHITE     =        "\033[1;37m"

NORMAL = "\033[0m"


def logmethod(methodname):
    def _method(self,*argl,**argd):
        global indent

        #parse the arguments and create a string representation
        args = []
        for item in argl:
            args.append('%s' % shortstr(item))
        for key,item in argd.items():
            args.append('%s=%s' % (key,str(item)))
        argstr = ','.join(args)   
        try:
            raise
            selfstr = str(self)
        except:
            selfstr = shortstr(self)
            
        #print >> log,"%s%s.  %s  (%s) " % (indStr*indent,selfstr,methodname,argstr)
        print >> log,"%s%s.%s%s%s  (%s) " % (indStr*indent,selfstr,  BOLDRED,methodname,NORMAL, argstr)
        indent += 1
        # do the actual method call
        returnval = getattr(self,'_H_%s' % methodname)(*argl,**argd)
        indent -= 1
        #print >> log,'%s:'% (indStr*indent), str(returnval)
        log.flush()
        return returnval
    return _method

def shortstr(obj):
    if "wx." in str(obj.__class__)  or  obj.__class__.__name__.startswith("wx"):
        shortclassname = obj.__class__.__name__
        #shortclassname = str(obj.__class__).split('.')[-1]
        if hasattr(obj, "blockItem") and hasattr(obj.blockItem, "blockName"):
            moreInfo = "block:'%s'" %obj.blockItem.blockName
        else:
            moreInfo = "at %d" %id(obj)
        return "<%s %s>" % (shortclassname, moreInfo)
    else:
        return str(obj)
            
            
class LogTheMethods(type):
    def __new__(cls,classname,bases,classdict):
        logmatch = re.compile(classdict.get('logMatch','.*'))
        
        for attr,item in classdict.items():
            if callable(item) and logmatch.match(attr):
                classdict['_H_%s'%attr] = item    # rebind the method
                classdict[attr] = logmethod(attr) # replace method by wrapper

        return type.__new__(cls,classname,bases,classdict)   



if __name__=='__main__':
    class Test(object):
        __metaclass__ = LogTheMethods
        logMatch = '.*'
    
        def __init__(self):
            self.a = 10
    
        def meth1(self):pass
        def add(self,a,b):return a+b
        def fac(self,val): # faculty calculation
            if val == 1:
                return 1
            else:
                return val * self.fac(val-1)
    
    t = Test()
    t.add(5,6)
    t.fac(4)