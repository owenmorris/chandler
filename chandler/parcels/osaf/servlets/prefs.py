
from application import schema

from osaf import webserver
from osaf.framework import Preferences

from twisted.web import static

def tag(tagName, **kwds):
    """
    quick and dirty way to do a start-tag. I'm using lower() so that
    you can pass in Class='foo' as a parameter, since class is a
    python reserved word
    """
    result = u'<' + unicode(tagName)
    for attr, value in kwds.iteritems():
        if value is not None:
            result += ' %s="%s"' % (attr.lower(), value)
    result += '>'
    return result

def tagged(tagName, text, *args, **kwds):
    result = tag(tagName, *args, **kwds)
    result += unicode(text)
    result += u'</%s>' % unicode(tagName)
    return result
    

class PrefResource(webserver.AuthenticatedResource):
    """
    First cut at this is just a preference viewer
    """

    def render_GET(self, request):
        result = """<html>
<head>
  <title>Chandler Preference Editor</title>
  <link rel='stylesheet' href='/site.css' type='text/css' />
  <link rel='stylesheet' href='/prefs.css' type='text/css' />
</head>
<body>
<h1>Chandler Preference Editor</h1>
"""

        for prefObj in Preferences.iterItems(self.repositoryView):
            specificKind = prefObj.itsKind
            result += u'<h2>%s.%s (%s)</h2>\n' % \
                      (schema.parcel_name(prefObj.__module__),
                       prefObj.itsName,
                       specificKind.itsName)

            result += "<ul>\n"
            for attrName, attr, k in specificKind.iterAttributes(inherited=False):
                result += "<li>"
                try:
                    value = getattr(prefObj, attrName)
                except AttributeError:
                    value = "(none)"

                result += tagged('span', attrName, Class='name')

                Class = 'value'
                if prefObj.hasLocalAttributeValue(attrName):
                    Class+=' local-value'
                    
                result += tagged('span', value, Class=Class)

                result += "</li>"
                
            result += "</ul>\n"
                
        result += "</body></html>"

        return result.encode('utf-8')

    def getChild(self, path, request):
        """
        I'm trying to figure out a way to make 'prefs.css' return
        prefs.css inside this module's directory, but I haven't quite
        figured it out yet
        """
        if path:
            webserverpath = self.resourceItem.server.path
            if path in ("prefs.css",):
                return static.File(os.path.join(webserverpath, path))

            return self
        else:
            return self
