<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:exsl="http://exslt.org/common"
     xmlns:func="http://exslt.org/functions"
     extension-element-prefixes="exsl func" 
     xmlns:core="//Schema/Core">
    
	<xsl:output method="html" encoding="ISO-8859-1"/>
	
    <xsl:include href="includes/helperFunctions.xsl"/>
    <xsl:include href="includes/constants.xsl"/>

    <xsl:variable name="pagetype" select="'Type'"/>
    <xsl:variable name="title" select="func:pluralize($pagetype)"/>
    <xsl:variable name="filename" select="concat($title, '.html')"/>
    
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
					<a href="index.html">
					   <xsl:apply-templates select="." mode="getDisplayName"/>
					</a>
					<xsl:text> - </xsl:text>
					<xsl:apply-templates select="$coreDoc/core:Parcel/*[@itemName=$pagetype]" mode="getHrefAnchor">
					   <xsl:with-param name="text" select="$title"/>
					</xsl:apply-templates>
				</h1>
				<ul>
					<li>
						<span class="attributeTitle">description: </span>
						<xsl:value-of select="core:description"/>
					</li>
					<li>
						<span class="attributeTitle">version: </span>
						<xsl:value-of select="core:version"/>
					</li>
					<li>
						<span class="attributeTitle">author: </span>
						<xsl:value-of select="core:author"/>
					</li>
				</ul>
				<xsl:apply-templates select="core:Type"/>
			</body>
		</html>
	</xsl:template>
	<xsl:template match="core:Type">
		<hr/>
		<h2>
            <xsl:apply-templates select="." mode="getHrefAnchor">
               <xsl:with-param name="text" select="'#'"/>
            </xsl:apply-templates>
            <xsl:apply-templates select = "." mode="getNameAnchor"/>
            <xsl:if test = "core:superKinds">
               <xsl:text> &lt;= </xsl:text>
               <xsl:apply-templates select="core:superKinds" mode="derefHref"/>
            </xsl:if>
			<br/>
		</h2>
		<ul>
            <xsl:for-each select="*">
               <xsl:variable name="relpath">
                  <xsl:call-template name="createRelativePath">
                     <xsl:with-param name="src" select="/core:Parcel/@describes" />
                     <xsl:with-param name="target">
                        <xsl:apply-templates mode="getURIFromQName" select="@itemref" />
                     </xsl:with-param>
                  </xsl:call-template>
               </xsl:variable>
               <xsl:variable name="ref">
                  <xsl:apply-templates select = "@itemref" mode="quickRef"/>
               </xsl:variable>
               <li><span class="attributeTitle">
                  <xsl:value-of select="local-name(.)" />
                  <xsl:text>: </xsl:text>
                  </span>
                  <xsl:value-of select="." />
                  <xsl:apply-templates select = "." mode="derefHref"/>
               </li>    
            </xsl:for-each>
		</ul>
	</xsl:template>
</xsl:stylesheet>