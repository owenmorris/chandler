__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os

from repository.persistence.XMLRepository import XMLRepository
from repository.parcel.Util import PrintItem

rootdir = os.environ['CHANDLERHOME']
repdir = os.path.join(rootdir, 'chandler', '__repository__')
rep = XMLRepository(repdir)

createRepository = False

if createRepository:
    rep.create()
    schemaPack = os.path.join(rootdir, 'chandler', 'repository', 'packs', 
                              'schema.pack')
    rep.loadPack(schemaPack)
    rep.commit()
else:
    rep.open( )

PrintItem("//Schema", rep)

rep.close()
