import application.Application
from application.agents.model.Action import Action

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
