import sys, traceback
import threading
from twisted.web import resource
import repository
from osaf.examples.zaobao.RSSData import RSSChannel
import wx

class ZaoBaoResource(resource.Resource):
    isLeaf = True
    def render_GET(self, request):

        if not hasattr(self, "myView"):
            repo = wx.GetApp().repository
            self.myView = repo.createView("ZaoBaoServletThread")

        repoView = self.myView
        prevView = None

        try: # Outer try to render any exceptions

            try: # Inner try/finally to handle restoration of current view

                mode = request.args.get('mode', [None])[0]

                # The Server item will give us the repositoryView during
                # startup.  Set it to be the current view and restore the
                # previous view when we're done.
                # repoView = self.repositoryView

                prevView = repoView.setCurrentView()
                repoView.refresh()

                result = "<html><head><title>ZaoBaoWeb</title><link rel='stylesheet' href='/site.css' type='text/css' /></head>"
                result += "<body>"

                if not request.postpath or not request.postpath[0]:
                    item = None
                else:
                    uuid = request.postpath[0]
                    item = repoView.findUUID(uuid)

                    if isinstance(item, RSSChannel):
                        item.markAllItemsRead()
                        item = None

                result += RenderChannelList(repoView, item)


            finally: # inner try
                if repoView is not None:
                    repoView.commit()
                if prevView is not None:
                    prevView.setCurrentView()

        except Exception, e: # outer try
            result = "<html>Caught an exception: %s<br> %s</html>" % (e, "<br>".join(traceback.format_tb(sys.exc_traceback)))

        return str(result)



def RenderChannelList(repoView, theItem):
    result = ""

    ChannelKind = repoView.findPath("//parcels/osaf/examples/zaobao/schema/RSSChannel")

    data = []
    # data is a list of dictionaries containing info about channels; each
    # dictionary has values for channel, items, and unread

    channels = []
    for channel in repository.item.Query.KindQuery().run([ChannelKind]):
        if hasattr(channel, 'displayName'):
            channels.append(channel)
    channels.sort(lambda x, y: cmp(x.displayName, y.displayName))

    if theItem is not None:
        theItem.isRead = True

    nextItem = None

    for channel in channels:
        channelData = { 'channel' : channel, 'items' : [], 'unread' : 0 }
        for item in channel.items:
            if not item.isRead:
                channelData['items'].append(item)
                channelData['unread'] += 1
 
        channelData['items'].sort(lambda x, y: cmp(y.date, x.date))

        if nextItem is None:
            try:
                nextItem = channelData['items'][0]
            except:
                pass
 
        data.append(channelData)

    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"

    if nextItem is not None:
        nextLink = " | <a href=/zaobao/%s>Next&gt;</a>" % nextItem.itsUUID
    else:
        nextLink = ""

    result += "<tr class='headingsrow'>\n"
    result += "<td colspan=2><a href=/zaobao/><b>ZaoBaoWeb</b></a>%s</td>\n" % nextLink
    result += "</tr>\n"


    result += "<tr>"

    result += "<td valign=top><table width=300 border=0 cellpadding=4 cellspacing=0>"

    for channelData in data:

        channel = channelData['channel']
        unread = channelData['unread']
        items = channelData['items']

        result += "<tr class='headingsrow'>"
        result += "<td><b>%s</b>" % channel.displayName
        if unread > 0:
            result += " (%d) | <a href=/zaobao/%s>Mark as read</a>" % (unread, channel.itsUUID)
        result += "</td>"
        result += "</tr>"

        count = 0
        for item in items:
            result += oddEvenRow(count)
            result += "<td>"
            result += "&nbsp;<a href=/zaobao/%s>%s</a>" % (item.itsUUID,
              item.displayName)
            result += "</td></tr>"
            count += 1

    result += "</table></td>"

    result += "<td valign=top width=100% class=rssitem>"

    if theItem is not None:
        item = theItem
        result += "<span class=header><a href=%s>%s</a></span></br>" % (item.link, item.displayName)
        result += "<b>%s</b> | %s</br>" % (item.channel.displayName, item.date.localtime().strftime('%A, %B %d @ %I:%M %p'))

        try:
            uStr = item.content.getReader().read()
            content = uStr.encode('ascii', 'replace')
        except:
            content = ""
        result += "<p>%s</p>" % content


    result += "</td></tr></table>"

    return result


def RenderChannel(repoView, channel):

    result = ""

    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td><b>%s</b>" % channel.displayName
    result += "</td>\n"
    result += "</tr>\n"

    items = []
    for item in channel:
        items.append(item)
    items.sort(lambda x, y: cmp(x.date, y.date))

    for item in items:
        if item.isRead:
            continue

        result += "<tr class='oddrow'>"
        result += "<td>"
        result += "<a href='%s'><b>%s</b></a><br>%s" % (item.link, item.displayName,  item.date)
        result += "</td>"
        result += "</tr>"
        result += "<tr class='evenrow'>"
        result += "<td>"
        try:
            uStr = item.content.getReader().read()
            content = uStr.encode('ascii', 'replace')
        except:
            content = ""
        result += content
        result += "</td>"
        result += "</tr>"
        item.isRead = True

    result += "</table>\n"

    return result

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def oddEvenRow(count):
    if count % 2:
        return "<tr class='oddrow'>\n"
    else:
        return "<tr class='evenrow'>\n"

