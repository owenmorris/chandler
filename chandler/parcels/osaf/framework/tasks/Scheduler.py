__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import threading
import types
import time as _time

__all__ = ['Scheduler']

class Event(object):
    def __init__(self, startTime, repeat, repeatDelay, action, *args):
        self._startTime = startTime
        self._delay = repeatDelay
        self.repeat = repeat

        self.action = action
        self.args = args

        self.condition = None
        self.conditionis = True

        self.time = self._startTime

    def resetTime(self):
        self.time = _time.time() + self._delay


class Queue(object):
    def __init__(self):
        self.__lock = threading.Lock()
        self.__queue = []

    def __len__(self):
        """ Get the number of events in the queue """
        self.__lock.acquire()
        try:
            return len(self.__queue)
        finally:
            self.__lock.release()
        return 0

    def get(self, i=0):
        """ Get an event from the queue
        If the queue does not have the event at the index you asked for
        it will return None
        """
        self.__lock.acquire()
        try:
            if len(self.__queue) > i:
                return self.__queue[i]
        finally:
            self.__lock.release()
        return None

    def put(self, event):
        """ Puts an event in to the queue """
        self.__lock.acquire()
        try:
            return self.__put(event)
        finally:
            self.__lock.release()
        return 0

    def __put(self, event):
        """ Really puts an event in to the queue """
        assert self.__lock.locked(), 'lock not acquired'

        i = 0
        time = event.time
        for item in self.__queue:
            if time < item.time:
                break
            i += 1
        self.__queue.insert(i, event)
        return i

    def remove(self, event):
        """ Removes an event from the queue """
        self.__lock.acquire()
        try:
            self.__remove(event)
        finally:
            self.__lock.release()

    def __remove(self, event):
        """ Really removes an event from the queue """
        assert self.__lock.locked(), 'lock not acquired'

        self.__queue.remove(event)

    def reschedule(self, event, delay = 0):
        """ Reschedules an event to fire again after delay
        This is a utility function to avoid having to lock twice
        """
        self.__lock.acquire()
        try:
            event.time = _time.time() + delay
            self.__remove(event)
            self.__put(event)
        finally:
            self.__lock.release()        

    def getNextTime(self):
        """ Utility function to get the next event in the queue's time
        If there are no events in the queue, it returns None
        """
        self.__lock.acquire()
        try:
            if len(self.__queue) > 0:
                return self.__queue[0].time
        finally:
            self.__lock.release()
        return None


class Scheduler(object):
    def __init__(self):
        self.queue = Queue()
        self.__running = False
        self.__waiting = False
        self.__condition = threading.Condition()

    def _scheduleEvent(self, event):
        #self.log.debug("event scheduled %s", event)
        # add to queue
        i = self.queue.put(event)

        # if this is the first thing in the queue, poke our condition variable
        self.__condition.acquire()
        try:
            if self.__waiting and i == 0:
                self.__condition.notify()
        finally:
            self.__condition.release()

    def schedule(self, delay, repeatFlag, repeatDelay, action, *args):
        event = Event(_time.time() + delay, repeatFlag, repeatDelay, action, *args)
        self._scheduleEvent(event)
        return event

    def scheduleabs(self, startTime, repeatFlag, repeatDelay, action, *args):
        event = Event(startTime, repeatFlag, repeatDelay, action, *args)
        self._scheduleEvent(event)
        return event

    def start(self):
        #self.log.debug("starting scheduler")
        self.running = True
        while self.running:
            self.__condition.acquire()
            try:
                self.__waiting = False
            finally:
                self.__condition.release()

            waitTime = self._run()
            #print 'waiting', waitTime

            # XXX What happens if self.running is false here?  Should we
            #     check and bail?  Sorta sucks since we're in a while loop
            #     already checking this...
            if not self.running:
                break

            self.__condition.acquire()
            try:
                self.__waiting = True
                self.__condition.wait(waitTime)
            finally:
                self.__condition.release()

    def stop(self):
        #self.log.debug("stopping scheduler")
        self.running = False
        self.__condition.acquire()
        try:
            if self.__waiting:
                self.__condition.notify()
        finally:
            self.__condition.release()

    def _run(self):
        q = self.queue

        while True:
            event = q.get()
            if not event:        # no events in the queue
                return None

            time = event.time
            now = _time.time()
            if now < time:       # it isn't time to run yet.. try again later
                return time - now
            del time

            doEvent = True
            if event.condition and event.condition() != event.conditionis:
                q.reschedule(event)
                doEvent = False
                #print 'condition failed'

            if doEvent:
                # remove from the queue and fire the action
                q.remove(event)
                self._runEvent(event)

            # don't use event after this point
            del event

            nextTime = q.getNextTime()
            if nextTime is None: # no more events in the queue.  wait for one
                return None

            now = _time.time()
            if now >= nextTime:  # the next event should have fired already!
                continue

            return nextTime - now

    def _runEvent(self, event):
        result = None

        try:
            result = event.action(*event.args)
        except StopIteration:
            event.repeat = False

        # look at the result to see if we need to do anything extra
        if isinstance(result, types.TupleType):
            print 'got tuple', result
            reason = result[0]
            if reason == 'condition':
                event.condition = result[1]
                event.conditionis = result[2]
        elif isinstance(result, types.GeneratorType):
            #print 'got generator'
            self.schedule(0.01, True, 0.01, result.next)

        if event.repeat:
            event.resetTime()
            self._scheduleEvent(event)


# Test code

class TestThread(threading.Thread):    
    def __init__(self):
        threading.Thread.__init__(self)
        self.scheduler = Scheduler()

    def run(self):
        self.scheduler.start()

def foo(bar):
    print bar

import random

def bar():
    print random.random()

def hehe():
    i = 0
    while i < 5:
        i += 1
        print 'hehe()', i
        yield i

def lala():
    i = 0
    while i < 10:
        if i == 7:
            yield hehe()
        i += 1
        print 'lala()', i
        yield i

def _main():
    thread = TestThread()
    thread.start()
    thread.scheduler.schedule(10,  False, 0, foo, '10 blah')
    thread.scheduler.schedule(5,   False, 0, foo, '5 blah')
    thread.scheduler.schedule(15,  False, 0, foo, '15 blah')
    thread.scheduler.schedule(5.2, False, 0, foo, '5.2 blah')
    thread.scheduler.schedule(5.3, False, 0, foo, '5.3 blah')
    thread.scheduler.schedule(5.4, False, 0, foo, '5.4 blah')
    thread.scheduler.schedule(2,   False, 0, foo, '2 blah')
    thread.scheduler.schedule(1,   False, 0, foo, '1 blah')
    thread.scheduler.schedule(4,   False, 0, bar)
    thread.scheduler.schedule(3,   False, 0, bar)
    thread.scheduler.schedule(2,   False, 0, lala)

if __name__ == '__main__':
    _main()
