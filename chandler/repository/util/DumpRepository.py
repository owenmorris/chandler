__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os

from repository.persistence.XMLRepository import XMLRepository
from repository.parcel.Util import PrintItem

rootdir = os.environ['CHANDLERHOME']
repdir = os.path.join(rootdir, 'Chandler', '__repository__')
rep = XMLRepository(repdir)
rep.open()

# This works
PrintItem("//parcels", rep)

# This doesn't:
# PrintItem("//Schema", rep)

rep.close()
