__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application.agents.model.Condition import Condition

PEOPLE_NEEDED = ['pavlov1234@jabber.org']
class AvailableCondition(Condition):

    def GetNotifications(self):
        return []

    def IsSatisfied(self, notification):
        BASE_PATH = '//parcels/application/ChandlerJabber/'
        repository = self.getRepository()
        repository.commit()
        for i in PEOPLE_NEEDED:
            item = repository.find(BASE_PATH + i)
            if not item:
                return False
            if item.type != 'available':
                return False

        return True
