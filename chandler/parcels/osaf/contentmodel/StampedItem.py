
""" 
StampedItem.py Classes for Stamped Items - combinations of other Kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.item.Item as Item
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.tasks.Task as Task

class TaskEventExtraAspect(Item.Item):
    """
      Task Event Extra Aspect is the extra bag of attributes
    that exists due to the synergy between Task and Event.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    pass

class TaskEvent (ContentModel.ContentItem, 
                 Task.TaskAspect, 
                 Calendar.CalendarEventAspect):
    """
      An Item that is both a Task and an Event.  The Taskness takes priority.
    """
    pass

class MailedTask (ContentModel.ContentItem, 
                  Task.TaskAspect, 
                  Mail.MailMessageAspect):
    """
      An Item that is both a Task and a Mail message.  The Taskness takes priority.
    """
    pass

class EventTask (ContentModel.ContentItem, 
                 Task.TaskAspect, 
                 Calendar.CalendarEventAspect):
    """
      An Item that is both a Task and a Calendar Event.  The Taskness takes priority.
    """
    pass

class MailedEvent (ContentModel.ContentItem, 
                   Mail.MailMessageAspect, 
                   Calendar.CalendarEventAspect):
    """
      An Item that is both a Mail Message and a Calendar Event.  
    The Mail Message takes priority.
    """
    pass

class MailedEventTask (ContentModel.ContentItem, 
                       Task.TaskAspect, 
                       Mail.MailMessageAspect, 
                       Calendar.CalendarEventAspect):
    """
      An Item that is the union of a Task, a Mail Message and 
    a Calendar Event, with priority in that order.
    """
    pass
