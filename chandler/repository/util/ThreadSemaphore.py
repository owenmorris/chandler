
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from threading import currentThread, Semaphore


class ThreadSemaphore(object):

    def __init__(self, n=1):

        self._semaphore = Semaphore()
        self._thread = None

    def acquire(self, wait=True):

        if not self._thread is currentThread():
            #print currentThread(), 'acquiring'
            result = self._semaphore.acquire(wait)
            if result:
                #print currentThread(), 'got it'
                self._thread = currentThread()

            return result

        return False

    def release(self):

        if self._thread is not currentThread():
            raise ValueError, 'current thread did not acquire semaphore'
        else:
            self._thread = None
            self._semaphore.release()
            #print currentThread(), 'released it'
