__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import Scheduler
import threading, logging

""" Controls the task thread """
class TaskManager(object):
    def __init__(self):
        super(TaskManager, self).__init__()

        self.thread = TaskThread()
        self.isRunning = False
        self.__lock = threading.Lock()

    def start(self):
        """ start the task manager thread """
        self.__lock.acquire()
        try:
            if not self.isRunning:
                self.isRunning = True
                self.thread.start()
        finally:
            self.__lock.release()

    def stop(self):
        """ stop the task manager thread """
        self.__lock.acquire()
        try:
            if self.isRunning:
                self.thread.stop()
                self.thread.join()
                self.isRunning = False
        finally:
            self.__lock.release()

    def running(self):
        """ returns True if the task manager is running """
        self.__lock.acquire()
        try:
            return self.isRunning
        finally:
            self.__lock.release()


""" TaskManager's thread """
from repository.persistence.Repository import RepositoryThread
class TaskThread(RepositoryThread):
    def __init__(self):
        super(TaskThread, self).__init__(Globals.repository, target=self.__run)
        self.setDaemon(True)
        self.scheduler = Scheduler.Scheduler()

    def __run(self):
        repository = Globals.repository

        # XXX
        # it isn't clear why this is needed here, but if it isn't here
        # the repository deadlocks when we try to find()
        repository.commit()

        # schedule all instructions with times
        self.__ScheduleTasks()

        # Start the scheduler
        self.scheduler.start()

    def stop(self):
        self.scheduler.stop()

    def __ScheduleTasks(self):
        # this function is really ugly.. i should clean it up :)

        from repository.item.Query import KindQuery
        taskKind = Globals.repository.find('//parcels/osaf/framework/tasks/Task')
            
        for task in KindQuery().run([taskKind]):
            try:
                schedule = task.schedule
            except AttributeError:
                continue

            try:
                startTime = schedule.startTime.ticks()
            except AttributeError:
                startTime = None

            repeatFlag = schedule.repeatFlag
            if repeatFlag:
                try:
                    repeatDelay = schedule.repeatDelay.seconds
                except AttributeError:
                    repeatDelay = 0

            if startTime:
                self.scheduler.scheduleabs(startTime, repeatFlag, repeatDelay, _ExecuteTask, task)
            else:
                self.scheduler.schedule(repeatDelay, repeatFlag, repeatDelay, _ExecuteTask, task)

""" Callback """
def _ExecuteTask(task):
    result = task.Execute()
    yield result
