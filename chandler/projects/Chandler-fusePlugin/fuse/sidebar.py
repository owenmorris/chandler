#   Copyright (c) 2007-2008 Open Source Applications Foundation
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


import os, stat, time, traceback, sys, commands, atexit

from osaf.pim import EventStamp, has_stamp, SmartCollection
from osaf.sharing import ICalendar
from application import schema

from fuse.c import FUSE
from chandlerdb.persistence.DBRepository import DBRepository
from chandlerdb.persistence.Repository import RepositoryThread, RepositoryWorker


class sidebar(FUSE):
    """
    A sample filesystem that exposes the Chandler Sidebar collections.
    A Calendar .ics file is generated upon file open for reading.

    Until MacFUSE supports the -odirect_io option, there may be 0-padding at
    the end of the generated .ics files. 

    A Calendar .ics file is imported when writing. The actual import work is
    done by a separate RepositoryWorker view/thread.

    Anything else remains to be implemented.
    """

    def __init__(self, repository):

        super(sidebar, self).__init__(repository.logger, RepositoryThread)

        self.view = repository.createView('sidebar', pruneSize=50)
        self.openFiles = {}
        self.thread = None

        self.importWorker = ImportWorker('import', repository)
        self.importWorker.start()

    def readdir(self, path):

        if path == "":
            return ['sidebar']
        elif path == 'sidebar':
            self.view.refresh()
            sidebar = schema.ns('osaf.app', self.view).sidebarCollection
            return [c.displayName for c in sidebar]

        return []

    def stat(self, path):

        values = [0] * 10
        if path in ("", 'sidebar'):
            values[stat.ST_MODE] = stat.S_IFDIR | 0777
            values[stat.ST_NLINK] = 2
            return values

        if path.startswith('sidebar/'):
            if path.endswith('.ics'):
                if path in self.openFiles:
                    values[stat.ST_MODE] = stat.S_IFREG | 0666
                    values[stat.ST_NLINK] = 1
                    values[stat.ST_CTIME] = time.time()
                    return values
            else:
                self.view.refresh()
                store = self.view.store
                dir, name = path.split('/', 1)
                sidebar = schema.ns('osaf.app', self.view).sidebarCollection
                for c in sidebar:
                    if c.displayName == name:
                        then, x, x, x = store.getCommit(c.itsVersion)
                        values[stat.ST_MODE] = stat.S_IFREG | 0444
                        values[stat.ST_INO] = hash(c.itsUUID)
                        if path in self.openFiles:
                            values[stat.ST_SIZE] = len(self.openFiles[path][0])
                        else:
                            values[stat.ST_SIZE] = 256 * 1024
                        values[stat.ST_NLINK] = 1
                        values[stat.ST_MTIME] = then
                        return values

        return None

    def statvfs(self, path):
        # bogus, trying to placate the Finder
        return os.statvfs(self.view.repository.dbHome)
        
    def open(self, path, flags):

        if flags == os.O_RDONLY:
            if path.startswith('sidebar/'):
                if path in self.openFiles:
                    self.openFiles[path][1] += 1
                    return True

                self.view.refresh()
                dir, name = path.split('/', 1)
                sidebar = schema.ns('osaf.app', self.view).sidebarCollection
                for c in sidebar:
                    if c.displayName == name:
                        for item in c:
                            if has_stamp(item, EventStamp):
                                break
                        else:
                            return False

                        cal = ICalendar.itemsToVObject(self.view, c)
                        data = cal.serialize()
                        self.openFiles[path] = [data, 1, flags]
                        return True

        elif flags == os.O_WRONLY:
            if path.startswith('sidebar/'):
                if path.endswith('.ics'):
                    self.openFiles[path] = ['', 1, flags]
                    return True

        elif flags == os.O_CREAT:  # coming from mknod (FUSE pre 2.5)
            if path.endswith('.ics'):
                self.openFiles[path] = ['', 1, 0]
                return True

        return False

    def create(self, path, mode):

        if mode & stat.S_IFREG:
            if path.endswith('.ics'):
                self.openFiles[path] = ['', 1, 0]
                return True

        return False

    def mknod(self, path, mode):  # FUSE pre 2.5

        if mode & stat.S_IFREG:
            return True  # actual creation happens in open

        return False
        
    def close(self, path):

        if path.startswith('sidebar/'):
            if path in self.openFiles:
                data, count, flags = self.openFiles[path]
                if count == 1:
                    if path.endswith('.ics'):
                        self.importWorker.queueRequest((data, path))
                    del self.openFiles[path]
                else:
                    self.openFiles[path][1] -= 1

                return True

        return False

    def read(self, path, size, offset):

        if path in self.openFiles:
            data = self.openFiles[path][0][offset:offset+size]
            if data:
                return data

        return None

    def write(self, path, data, offset):

        if path in self.openFiles:
            file = self.openFiles[path]
            file[0] += data
            return len(data)

    def chown(self, path, uid, gid):
        return True

    def chmod(self, path, mode):
        return True

    def utimes(self, path, atime, mtime):
        return True

    def mount(self, mountpoint, volname="Chandler"):
        
        if not os.path.exists(mountpoint):
            os.mkdir(mountpoint)

        if sys.platform == 'darwin':
            options = ['-onoubc', '-onoreadahead',
                       '-ovolname=%s' %(volname), '-oping_diskarb']
        else:
            options = ['-odirect_io']

        options.append(mountpoint)

        thread = self.thread = super(sidebar, self).mount(*options)  # started

        self.mountpoint = mountpoint
        atexit.register(self.umount)

        return thread

    def umount(self):

        try:
            return commands.getstatusoutput('umount "%s"' %(self.mountpoint))[0]
        except:
            return -1
        else:
            del self.mountpoint

    def isMounted(self):
        
        return self.thread is not None and self.thread.isAlive()


class ImportWorker(RepositoryWorker):

    def processRequest(self, view, request):

        if view is None:
            view = self._repository.createView(self.getName(),
                                               pruneSize=50)

        view.refresh()

        try:
            data, path = request
            dir, filename = path.split('/', 1)

            events, name = ICalendar.itemsFromVObject(view, data)
            if name is None:
                name = filename

            c = SmartCollection(itsView=view, displayName=name)
            schema.ns("osaf.app", view).sidebarCollection.add(c)
            for event in events:
                c.add(event.getMaster().itsItem)
        
            view.commit()

        except Exception, e:
            print traceback.format_exc()
            view.cancel()

        return view
        
