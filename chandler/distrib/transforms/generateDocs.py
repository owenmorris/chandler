import os, time, libxml2, libxslt, sys

def _transformFilesXslt(transformFile, srcDir, destDir, outFile, 
 fileList):
    """ Run the list of files through an XSLT transform
    """
    
    print "Running XSLT processor using ", transformFile
    if not os.path.exists(destDir):
        os.mkdir(destDir)

    for file in fileList:
        srcFile = srcDir + os.sep + file
        destFile = destDir + os.sep + file
        destFile = os.path.join(os.path.dirname(destFile), outFile)
        try:
            os.makedirs(os.path.dirname(destFile))
        except Exception, e:
            pass
        if os.path.exists(srcFile):
            print ("Transforming " + srcFile)
            styledoc = libxml2.parseFile(transformFile)
            style = libxslt.parseStylesheetDoc(styledoc)
            doc = libxml2.parseFile(srcFile)
            result = style.applyStylesheet(doc, None)
            style.saveResultToFilename(destFile, result, 0)
            style.freeStylesheet()
            doc.freeDoc()
            result.freeDoc()
            
def _findFiles(root, filename, path=""):
    fileList = []
    if os.path.isfile(os.path.join(root, path, filename)):
        fileList.append(os.path.join(path, filename))
    for name in os.listdir(os.path.join(root, path)):
        full_name = os.path.join(path, name)
        if os.path.isdir(os.path.join(root,full_name)) and name != 'tests':
            fileList = fileList + _findFiles(root, filename, full_name)
    return fileList

def generateDocs(docDir, xslDir, chandlerDir):
    import urllib
    def pluralize(string):
        if string == 'Alias':
            return 'Aliases'
        else:
            return string + 's'
    objectList = ["Kind", "Attribute", "Enumeration", "Alias", "Type"]
    pluralList = map(pluralize, objectList)
    xslFiles   =  pluralList + ["sentences"]

    fileList   = _findFiles(chandlerDir, "parcel.xml")


    for xsl in xslFiles:
        _transformFilesXslt(os.path.join(xslDir,xsl+".xsl"), chandlerDir,
                            docDir, xsl+".html", fileList)

    indexFile = file(os.path.join(docDir, "index.html"), 'w+')
    indexFile.write("<html><head><title>Chandler Schema Documents</title>")
    indexFile.write("<link rel=\"stylesheet\" type=\"text/css\" \
                     href=\"schema.css\"/></head>")

    indexFile.write('<body><div style="float: left;">')
    indexFile.write('<h1>Chandler Schema Documentation</h1></div>')
    
    indexFile.write('<div style="float: right; border-style: solid;')
    indexFile.write('border-width: 1px; padding: 5px;">')
    indexFile.write('<a href="automatic-docs-help.html">Help</a> ')
    indexFile.write('with this page -- ')
    indexFile.write('Back to the <a href="">Parcel Index</a></div>')
    indexFile.write('<br clear="all"/>')
    
    indexFile.write('<div class="topDetailBox"><span class="detailLabel">')
    indexFile.write('Generated </span>')
    indexFile.write(time.strftime("%m/%d %I:%M%p") + ' </div>')        
    indexFile.write('<div class="sectionBox">')
    indexFile.write('<h2>Parcels</h2>')
    indexFile.write('<div class="tableBox">')
    indexFile.write('<table cellpadding="2" cellspacing="2" border="0"')
    indexFile.write(' style="width: 100%; text-align: left;">')
    #output a header row
    indexFile.write('<tr>')
    indexFile.write('<td class="tableHeaderCell">Parcel Name</td>')
    indexFile.write('<td class="tableHeaderCell">Path</td>')
    indexFile.write('<td class="tableHeaderCell">Summary</td>')
    for type in pluralList:
        indexFile.write('<td class="tableHeaderCell">%s</td>' % type)
    indexFile.write('</tr>')

    for xmlFile in fileList:
        doc=libxml2.parseFile(os.path.join(chandlerDir, xmlFile))
        ctxt = doc.xpathNewContext()
        ctxt.xpathRegisterNs('core', '//Schema/Core')
        content = {}
        #determine which objects are present in the file
        for type in objectList:
            content[type]=len(ctxt.xpathEval("//core:%s" % type))
        displayNameNode=ctxt.xpathEval("/core:Parcel/core:displayName")
        #ignore the file if no objects are present
        if not filter(None, content.values()):
            doc.freeDoc()
            ctxt.xpathFreeContext()
            continue
        (head, tail) = os.path.split(xmlFile)
        head=urllib.pathname2url(head)
        indexFile.write('<tr>')
        indexFile.write('<td>')
        if displayNameNode:
            indexFile.write(displayNameNode[0].content)
        indexFile.write('</td>')
        indexFile.write('<td>%s</td>' % head)
        indexFile.write('<td><a href="%s/sentences.html">Summary</a>' % head)
        indexFile.write('</td>')
        for name in objectList:
            indexFile.write('<td>')
            if content[name]:
                p=pluralize(name)
                indexFile.write('<a href="%s/%s.html">%s</a>' % (head,p,p))
            indexFile.write('</td>')
        indexFile.write('</tr>')
        doc.freeDoc()
        ctxt.xpathFreeContext()
        
    indexFile.write("</table>")
    indexFile.write("</body>")
    indexFile.write("</html>")
    indexFile.close()



def main():
    (docDir, xslDir, chandlerDir) = sys.argv[1:]
    generateDocs(docDir, xslDir, chandlerDir)

if __name__ == '__main__':
    main()
