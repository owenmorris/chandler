""" Unit tests
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"

import unittest, sys, os

sys.path.append(os.environ['OSAFROOT'] + "\\Chandler")

from application.repository.Repository import Repository
from application.repository.Thing import Thing
from application.repository.KindOfThing import KindOfThing
from application.repository.AttributeTemplate import AttributeTemplate
from application.repository.Namespace import chandler

from application.repository.Item import Item
from application.repository.Event import Event

from mx import DateTime

repository = Repository()
#repository.PrintTriples()

event = Event()
event.startTime = DateTime.today()
event.endTime = DateTime.now()
event.headline = 'Games night'
repository.AddThing(event)

repository.Commit()
repository.PrintTriples()

print "Duration: " + str(event.duration)





