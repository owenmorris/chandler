__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from Action import Action

"""
The Condition Class is a persistent object that's a kind of action.  Conditions are periodically evaluated,
and trigger a set if actions they evaluate positively
"""
class ConditionFactory:
    def __init__(self, repository):
        self._container = repository.find("//Agents")
        self._kind = repository.find("//Schema/AgentsSchema/Condition")
        self.repository = repository
        
    def NewItem(self, name):
        item = Condition(name, self._container, self._kind)                            
        return item

class Condition(Action):

    def __init__(self, name, parent, kind, **_kwds):
        super(Condition, self).__init__(name, parent, kind, **_kwds)

    def GetNotifications(self):
        """
          return a list of notifications used by this condition
        """
        resultList = []
        if self.conditionType == 'notification':
            try:
                resultList = self.conditionNotification.split(',')  
            except AttributeError:
                resultList = []
                
        return resultList
         
    def DetermineCondition(self, notificationList):
        """
           this is the key routine that evaluates a condition based on it's type.
           For now, we only handle notification type conditions, but that will change soon
        """        
        notificationData = None
        
        if self.conditionType == 'notification':
            conditionList = self.conditionNotification.split(',')  
            for notification in notificationList:
                try:
                    notificationName = notification.GetName()
                    index = conditionList.index(notificationName)
                    return (True, notification.data)
                except ValueError:
                    pass
                    
        return (False, None)
    
    