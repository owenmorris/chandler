<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:exsl="http://exslt.org/common"
     xmlns:func="http://exslt.org/functions"
     extension-element-prefixes="exsl func" 
     xmlns:core="//Schema/Core">
    
	<xsl:output method="html" encoding="ISO-8859-1"/>
	
    <xsl:include href="includes/helperFunctions.xsl"/>
    <xsl:include href="includes/constants.xsl"/>

    <xsl:variable name="pagetype" select="'Index'"/>
    <xsl:variable name="filename" select="'index.html'"/>
    <xsl:variable name="title" select="concat($pagetype, ' page')"/>
    
    <xsl:variable name = "coreRelpath">
       <xsl:call-template name="createRelativePath">
          <xsl:with-param name="src">
             <xsl:apply-templates mode="translateURI" select="/core:Parcel/@describes" />
          </xsl:with-param>
          <xsl:with-param name="target" select="$constants.corePath"/>
       </xsl:call-template>       
    </xsl:variable>
    <xsl:variable name = "coreDoc" select = "document(concat($coreRelpath, $constants.parcelFileName), /)" />
	
	<xsl:template match="core:Parcel">
		<html>
			<head>
				<title>
					<xsl:apply-templates select="." mode="getDisplayName"/>
					<xsl:text> - </xsl:text>
					<xsl:value-of select="$title"/>
				</title>
				<link rel="stylesheet" type="text/css">
				   <xsl:attribute  name = "href" >
				      <xsl:value-of select="$constants.cssPath" />
				   </xsl:attribute>
				</link>
			</head>

			<body>
				<h1>
					<xsl:apply-templates select="." mode="getDisplayName"/>
				</h1>
				<a>
				<xsl:attribute  name = "href" >
      <xsl:call-template name="createRelativePath">
         <xsl:with-param name="src" select="/core:Parcel/@describes" />
         <xsl:with-param name="target" select="'///'"/>
      </xsl:call-template>
				</xsl:attribute>
				Back to the main index
				</a>
				
				
				<h2><a href="Kinds.html">Kinds</a></h2>
                <ul>
                   <xsl:for-each select = "core:Kind">
                      <li>
				         <xsl:apply-templates select="." mode="getHrefAnchor"/>
				      </li>
				   </xsl:for-each>
                </ul>
				<h2><a href="Attributes.html">Attributes</a></h2>
                <ul>
                   <xsl:for-each select = "//core:Attribute">
                      <li>
				         <xsl:apply-templates select="." mode="getHrefAnchor"/>
				      </li>
				   </xsl:for-each>
                </ul>
				<h2><a href="Types.html">Types</a></h2>
                <ul>
                   <xsl:for-each select = "core:Type">
                      <li>
				         <xsl:apply-templates select="." mode="getHrefAnchor"/>
				      </li>
				   </xsl:for-each>
                </ul>
				<h2><a href="Aliases.html">Aliases</a></h2>
                <ul>
                   <xsl:for-each select = "core:Alias">
                      <li>
				         <xsl:apply-templates select="." mode="getHrefAnchor"/>
				      </li>
				   </xsl:for-each>
                </ul>
				<h2><a href="Enumerations.html">Enumerations</a></h2>
                <ul>
                   <xsl:for-each select = "core:Enumeration">
                      <li>
				         <xsl:apply-templates select="." mode="getHrefAnchor"/>
				      </li>
				   </xsl:for-each>
                </ul>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>