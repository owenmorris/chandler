import re
import application.Application
from application.agents.model.Action import Action

# this should come from the jabber client itself
whitelist = [ ".*osafoundation.*" ]

class ApproveAction(Action):
    def _Execute(self, agent, notification):
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
