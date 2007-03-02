import os, sys, time
c = sys.argv[1]
if c == 'stderr':
    sys.stderr.write('stderr\n')
elif c == 'stdout':
    sys.stdout.write('stdout\n')
elif c == 'envtest':
    sys.stdout.write('%s\n' % os.environ[c.upper()])
elif c == 'traceback':
    raise Exception
elif c == 'nonzero':
    sys.exit(42)
elif c == 'timeout':
    time.sleep(30)
    print 'should not see this'

