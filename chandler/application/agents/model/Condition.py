__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import re
from repository.item.Item import Item

"""
The Condition Class is a persistent object that's a kind of action.  Conditions are periodically evaluated,
and trigger a set if actions they evaluate positively
"""
class Condition(Item):

    def GetNotifications(self):
        """
          return a list of notifications used by this condition
        """
        try:
            return self.conditionNotification.split(',')
        except AttributeError:
            return []
         
    def IsSatisfied(self, notification):
        """
           this is the key routine that evaluates a condition based on it's type,
           returning True if the condition is satisifed
           For now, we only handle notification type conditions, but that will change soon
        """

        # we know that the condition fired, but check to make sure it's in our list
        # as a redundancy check
        notificationList = self.GetNotifications()
   
        try:
            index = notificationList.index(notification.GetName())
        except ValueError:
            return False
        
        # if there's no filter mode, we're done, so return True
        if not self.hasAttributeValue('conditionFilterMode'):
            return True
        
        compareMode = self.conditionFilterMode
        if compareMode == 'none':
            return True
        
        # handle the listequals mode specially, which treats the conditionAttribute and conditionValue as a
        # comma-delimited list, where all the comparisons in the list must be true for the condition to be true
        
        if compareMode == 'listequals':
            attributes = self.conditionAttribute.split(',')
            values = self.conditionValue.split(',')
            index = 0; length = len(attributes)
            
            while index < length:
                thisAttribute = attributes[index]
                thisNotificationValue = str(notification.data[thisAttribute])
                thisValue = str(values[index])
                if thisNotificationValue != thisValue:
                    return False
                index += 1
                
            return True
                
        attributeValue = str(notification.data[self.conditionAttribute])
        conditionValue = str(self.conditionValue)
                
        if compareMode == 'equals':
            return attributeValue == conditionValue
        
        if compareMode == 'notequals':
            return attributeValue != conditionValue
        
        if compareMode == 'contains':
            return attributeValue.find(conditionValue) >= 0
        
        if compareMode == 'matches':
            try:
                result = re.match(conditionValue, attributeValue)
                return result != None
            except:
               return False               
        
        return False
