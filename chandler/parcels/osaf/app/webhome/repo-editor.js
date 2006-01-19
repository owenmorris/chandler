var xmlrpc = null;
try {
    var xmlrpc = importModule("xmlrpc");
} catch(e) {
    reportException(e);
    throw "importing of xmlrpc module failed.";
}


var xmlRpcUrl = 'http://localhost:1888/xmlrpc';
var remoteChandler = 
  new xmlrpc.ServiceProxy(xmlRpcUrl, 
			  ["setAttribute", 
			   "getAttribute", 
			   "delAttribute", "commit"]);


var statusArea;


function onDocumentLoad() {
  statusArea = document.getElementById("status-area")
}

function resetStatusArea(err) {
    if (err == null) {
      statusArea.setAttribute("class", "idle");
    } else{
      statusArea.setAttribute("class", "error");
    }
}

/*
 * public interface to XML-RPC server - mostly boiler plate right now,
 * would be nice if we could just wrap the remoteChandler object to do
 * some of the statusArea work
 */

function setAttribute(itemPath, attrName, value) {
  var callback = function(result, err) {
    resetStatusArea(err);
  }
  statusArea.setAttribute("class", "busy")
  remoteChandler.setAttribute(itemPath, attrName, value, callback)
}

function getAttribute(itemPath, attrName, value) {
  var callback = function(result, err) {
    resetStatusArea(err);
  }

  statusArea.setAttribute("class", "busy")
  remoteChandler.getAttribute(itemPath, attrName, value, callback)
}

function delAttribute(itemPath, attrName) {
  var callback = function(result, err) {
    resetStatusArea(err);
  }
  statusArea.setAttribute("class", "busy")
  remoteChandler.delAttribute(itemPath, attrName, value, callback)
}

function commit() {
  var callback = function(result, err) {
    resetStatusArea(err);
  }
  statusArea.setAttribute("class", "busy");
  remoteChandler.commit(callback)
}



function TestMe(path) {
  setAttribute(path, "displayName", "set via XML-RPC")
}
