import traceback
import sys
import cStringIO
import twisted
import logging

logger = logging.getLogger('Blog')
logger.setLevel(logging.INFO)

activate = True
try:
    import pybl_config as config
except ImportError:
    logger.info("Couldn't import pybl_config -- did you remember to copy pybl_config.py.dist to pybl_config.py?")
    activate = False

if activate:
    if config.py['codebase'] not in sys.path:
        sys.path.insert(0, config.py['codebase'])

    from Pyblosxom.pyblosxom import Request, PyBlosxom as pyblMain

class BlogResource(twisted.web.resource.Resource):
    isLeaf = True
    def render_GET(self, request):
        if not activate:
            return "Blog servlet not configured.  Remember to copy servlets/blog/pybl_config.py.dist to pybl_config.py and edit it accordingly."

        try:
            # Prepare a Pyblosxom request object
            pyblRequest = Request()
            pyblRequest.addConfiguration(config.py)

            httpDict = {}
            hdrs = request.received_headers
            httpDict["HTTP_HOST"] = hdrs.get('host', 'unknown')
            httpDict["HTTP_USER_AGENT"] = hdrs.get('user-agent', 'unknown')
            httpDict["HTTP_REFERER"] = hdrs.get('referer', '')
            httpDict["PATH_INFO"] = "/".join(request.postpath)
            httpDict["REMOTE_ADDR"] = request.client.host
            httpDict["REQUEST_METHOD"] = request.method
            httpDict["REQUEST_URI"] = request.uri
            httpDict["SCRIPT_NAME"] = "/%s" % "/".join(request.prepath)
            httpDict["HTTP_IF_NONE_MATCH"] = None
            httpDict["HTTP_IF_MODIFIED_SINCE"] = None
            pyblRequest.addHttp(httpDict)

            # Here are parameters for our pybl_plugin
            outputIO = cStringIO.StringIO()
            pluginData = {
                'chandlerOutput'  : outputIO,
                'chandlerRequest' : request,
            }
            pyblRequest.addData(pluginData)

            p = pyblMain(pyblRequest)
            p.run()

            # this is cheesy--we need to remove the HTTP headers
            # from the file.
            outputIO.seek(0)
            output = outputIO.getvalue().splitlines()
            while 1:
                if len(output[0].strip()) == 0:
                    break
                output.pop(0)
            output.pop(0)

            return "\n".join(output)

        except Exception, e:
            result = "<html>Caught an exception: %s<br> %s</html>" % (e, "<br>".join(traceback.format_tb(sys.exc_traceback)))
            return str(result)
