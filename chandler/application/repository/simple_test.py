""" Unit tests
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, sys, os, gettext

gettext.install('Chandler')

# sys.path.append(os.environ['OSAFROOT'] + "\\Chandler")

from application.repository.Repository import Repository
from application.repository.Thing import Thing
from application.repository.KindOfThing import KindOfThing
from application.repository.AttributeTemplate import AttributeTemplate
from application.repository.Namespace import chandler

from application.repository.Item import Item
from application.repository.Event import Event
from application.repository.Contact import Contact
from application.repository.ContactMethod import ContactMethod
from application.repository.ContactName import ContactName

from mx import DateTime

repository = Repository()
#repository.PrintTriples()

event = Event()
event.startTime = DateTime.today()
event.endTime = DateTime.now()
event.headline = 'Games night'
repository.AddThing(event)

print "Duration: " + str(event.duration)

contact = Contact('Person')
contactName = ContactName(contact)
contact.SetAttribute(chandler.contactName, contactName)
repository.AddThing(contact)

repository.Commit()
repository.PrintTriples()

contactName.SetAttribute(chandler.firstname, "Sally")
lastName = contactName.GetAttribute(chandler.lastname)

print "Last Name: " + str(lastName)

contact.PrintTriples()
contactName.PrintTriples()





