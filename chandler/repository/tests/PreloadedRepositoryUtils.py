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


import logging, os, sys, time

from repository.persistence.DBRepository import DBRepository
from repository.util.Path import Path
import application

preloadPath = '__preloaded_repository__'

def makePreloadedRepository(path, schema=True, parcels=False):
    """
    """
    rootdir = os.environ['CHANDLERHOME']
    handler = logging.FileHandler(os.path.join(rootdir,'chandler.log'))
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)

    rep = DBRepository(path)
    rep.create(ramdb=False)

    if schema:
        # Load all core schemas
        chandlerPack = os.path.join(rootdir, 'chandler', 'repository',
                                    'packs', 'chandler.pack')
        rep.loadPack(chandlerPack)

    if parcels:
        manager = application.Parcel.Manager.get(rep.view, \
         path=[os.path.join(rootdir, 'chandler', 'parcels')])
        manager.loadParcels()


    rep.commit()
    rep.close()

def testCreate(rep, rootdir):
    """
    """
    rep.delete()
    t1 = time.time()
    rep.create()
    rep.commit()
    print time.time() - t1

def testOpenFrom(rep, rootdir):
    """
    """
    rep.delete()
    t1 = time.time()
    rep.open(restore=os.path.join(rootdir,'repository','tests',preloadPath))
    rep.commit()
    print time.time() - t1

def testPreloadVsNoPreload():
    """
    """
    rootdir = os.environ['CHANDLERHOME']
    handler = logging.FileHandler(os.path.join(rootdir,'chandler.log'))
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)

    rep = DBRepository('__repository__')
    testCreate(rep, rootdir)
    rep.close()

    testOpenFrom(rep, rootdir)
    rep.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("""usage: PreloadedRepositoryUtils: [--create [parcels]] [--test]
  --create [parcels]  create a preloaded repository containing core schema
                      if the word 'parcels' is supplied as an argument, the
                      preloaded repository contains all parcels as well
  --test              run a simple test comparing preloaded vs non-preloaded performance""")
    args = sys.argv[1:]
    create=False
    if '--create' in args:
        create=True
    parcels = False
    if 'parcels' in args:
        parcels=True
    test=False
    if '--test' in args:
        test = True

    if create:
        makePreloadedRepository(preloadPath, parcels=parcels)
                 
    if test:
        if os.path.exists(preloadPath):
            testPreloadVsNoPreload()
        else:
            sys.exit("No preloaded repository")
    
