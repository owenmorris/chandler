__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import re
from OSAF.framework.agents.schema.Action import Action
from OSAF.framework.agents.schema.Condition import Condition


# this should come from the jabber client itself
whitelist = [ ".*osafoundation.*" ]


class ApproveAction(Action):
    def Execute(self, agent, notification):
        print 'Executing', self.getItemDisplayName()

        data = notification.GetData()
        jabberClient = application.Application.app.jabberClient

        who = data['who']
        subscriptionType = data['subscriptionType']

        for i in whitelist:
            matchResult = re.match(i, who)
            if matchResult != None:
                print "was in whitelist"
                if subscriptionType == 'subscribe':
                    jabberClient.AcceptSubscriptionRequest(who)
                elif subscriptionType == 'unsubscribe':
                    jabberClient.DeclineSubscriptionRequest(who)
                return True

        return False


class ApproveAction2(Action):
    def Execute(self, agent, notification):
        print 'Executing', self.getItemDisplayName()

        data = notification.GetData()
        jabberClient = application.Application.app.jabberClient
        
        who = data['who']
        subscriptionType = data['subscriptionType']

        if subscriptionType == 'subscribe':
            jabberClient.AcceptSubscriptionRequest(who)
        elif subscriptionType == 'unsubscribe':
            jabberClient.DeclineSubscriptionRequest(who)

        jabberClient.NotifyPresenceChanged(who)

        return True



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
