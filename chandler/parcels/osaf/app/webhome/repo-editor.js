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
      clear();
    } else{
      statusArea.setAttribute("class", "error");
      print(err);
    }
}

/*
 * public interface to XML-RPC server - mostly boiler plate right now,
 * would be nice if we could just wrap the remoteChandler object to do
 * some of the statusArea work
 */

function setChandlerAttribute(itemPath, attrName, value, resultcallback) {
  var callback = function(result, err) {
    resetStatusArea(err);
    if (resultcallback)
      resultcallback(result, err);
  }
  statusArea.setAttribute("class", "busy");
  remoteChandler.setAttribute(repoView, itemPath, attrName, value, callback);
}

function getChandlerAttribute(itemPath, attrName, resultcallback) {
  var callback = function(result, err) {
    resetStatusArea(err);
    if (resultcallback)
      resultcallback(result, err);
  }

  statusArea.setAttribute("class", "busy");
  remoteChandler.getAttribute(repoView, itemPath, attrName, callback);
}

function delAttribute(itemPath, attrName) {
  var callback = function(result, err) {
    resetStatusArea(err);
  }
  statusArea.setAttribute("class", "busy");
  remoteChandler.delAttribute(repoView, itemPath, attrName, value, callback)
}

function commit() {
  var callback = function(result, err) {
    resetStatusArea(err);
  }
  statusArea.setAttribute("class", "busy");
  remoteChandler.commit(repoView, callback)
}

function print(txt) {
  statusArea.appendChild(document.createElement("br"));
  statusArea.appendChild(document.createTextNode(txt));
}

function clear() {
  /* clear all but the first text node */
  children = statusArea.childNodes;
  for (var i=children.length-1; i>0; --i)
    statusArea.removeChild(children[i]);
}

var editInProgress = false;

function makeEditor(txt, originalNode, values) {
  editor = document.createElement("INPUT");
  editor.setAttribute("type", "text");

  editor.value = txt;
  
  for (var key in values) {
    editor["chandler" + key] = values[key];
  }
  editor.originalNode = originalNode;

  editor.style.width = originalNode.offsetWidth + "px";
  editor.style.height = originalNode.offsetHeight + "px";
  return editor;
}

function finishEdit(event) {

  /* first reset the node to the new value */
  editor = event.target;
  newValue = editor.value;
  
  newText = document.createTextNode(newValue);
  
  /* swap the editor back in */
  originalNode = replaceNode(editor);

  /* swap the value into the original object */
  originalText = originalNode.firstChild;
  originalNode.replaceChild(newText, originalText)

  /* now send an XMLRPC request to change the data in the database */
  undo = function(result, err) {
    if (err != null) 
      originalNode.replaceChild(originalText, newText);
  }

  setChandlerAttribute(itemPath, editor.chandlerattr, editor.value, undo);

  /* finally, allow edits elswhere */
  editInProgress = false;
}

function replaceNode(oldNode) {

  oldNode.parentNode.replaceChild(oldNode.originalNode, oldNode);
  return oldNode.originalNode
}

function isContainingNode(node) {
  nodeName = node.nodeName.toLowerCase();
  return (nodeName == "td" ||
	  nodeName == "li");
}

function extractValues(str) {
  /* extracts values from a string in the form "a-b c-d" to an array where
     v.a = 'b', v.c = 'd' */

  var result = Object();
  var valuePairs = str.split(" ");

  for (var i = 0; i<valuePairs.length; i++) {
    nv = valuePairs[i].split("-", 2);
    if (nv.length == 2)
      result[nv[0]] = nv[1];
  }
  return result;
}

function onValueTableClick(event) {

  /* disable attribute editing for now */
  return;

  if (editInProgress==true) 
    return;

  node = event.target;

  editNode = node.firstChild;
  /* walk up the tree till we hit the containing div */
  while (node.className.indexOf("editable") == -1 &&
	 !isContainingNode(node)) {

    /* if we're in a link, let it just be handled */
    if (node.nodeName.toLowerCase() == "a") {
      return;
    }
    node = node.parentNode;
  }
  
  if (!node || isContainingNode(node)) return;

  editNode = node;

  /* now we have our "editNode", we need to find the type */
  while (node.className.indexOf("type-") == -1 &&
	 !isContainingNode(node)) {
    node = node.parentNode;
  }
  if (!node) return;

  if (node.className.indexOf("type-") == -1) {
    return;
  }

  typeNode = node;
  

  editInProgress = true;
  
  valuePairs = extractValues(node.className);

  editor = makeEditor(editNode.innerHTML, editNode, valuePairs);
  
  /* the editable point is a <span class="editable"> */

  editNode.parentNode.replaceChild(editor, editNode);
  editor.focus();

  editor.addEventListener("blur", finishEdit, false);


  /* don't let other event handlers deal with this */
  event.preventBubble()
}
