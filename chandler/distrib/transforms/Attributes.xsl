<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:exsl="http://exslt.org/common"
     xmlns:func="http://exslt.org/functions"
     extension-element-prefixes="exsl func" 
     xmlns:core="//Schema/Core">
    
	<xsl:output method="html" encoding="ISO-8859-1"/>
	
    <xsl:include href="includes/helperFunctions.xsl"/>
    <xsl:include href="includes/constants.xsl"/>

    <xsl:variable name="pagetype" select="'Attribute'"/>
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
				
				<xsl:for-each select = "core:Attribute">
                   <hr/>
		           <h2>
                      <xsl:apply-templates select="." mode="getHrefAnchor">
                         <xsl:with-param name="text" select="'#'"/>
                      </xsl:apply-templates>
                      <xsl:apply-templates select = "." mode="getNameAnchor"/>
                      <xsl:if test = "core:superAttribute">
                         <xsl:text> - subAttribute of </xsl:text>
                         <xsl:apply-templates select="core:superAttribute" mode="derefHref"/>
                      </xsl:if>
		           </h2>

                   <em>itemName:
                   <xsl:value-of select="@itemName" />
                   </em>
			       <br/>
		           <h3>Aspects</h3>
				   <xsl:apply-templates select="."/>
				</xsl:for-each>

				<xsl:for-each select = "core:Kind/core:Attribute">
                   <hr/>
		           <h2>
                      <xsl:apply-templates select="." mode="getHrefAnchor">
                         <xsl:with-param name="text" select="'#'"/>
                      </xsl:apply-templates>
                      <xsl:apply-templates select = "." mode="getNameAnchor"/>

                      <xsl:if test = "core:superAttribute">
                         <xsl:text> - subAttribute of </xsl:text>
                         <xsl:apply-templates select="core:superAttribute" mode="derefHref"/>
                      </xsl:if>
		           </h2>
                   <em>
                   <xsl:text>itemName: </xsl:text>
                   <xsl:value-of select="@itemName" />
                   </em>
			       <br/>
                   <xsl:text>Local Attribute of </xsl:text>
                   <xsl:apply-templates select=".." mode="getHrefAnchor"/>
		           <h3>Aspects</h3>
				   <xsl:apply-templates select="."/>
				</xsl:for-each>
				
			</body>
		</html>
	</xsl:template>
	
	<xsl:template match="core:Attribute">
	    <xsl:param name="done" select="exsl:node-set('')"/>
		<ul>
            <xsl:for-each select="*">
               <xsl:variable name = "x" select = "." />
               <xsl:if test="not($done[local-name()=local-name($x)])">
               <li><span class="attributeTitle">
                  <xsl:value-of select="local-name(.)" />
                  <xsl:text>: </xsl:text>
                  </span>
                  <xsl:value-of select="." />
                  <xsl:apply-templates select = "." mode="derefHref"/>
               </li>
               </xsl:if>
            </xsl:for-each>
		</ul>
		<xsl:apply-templates select = "core:superAttribute">
		   <xsl:with-param name="done" select="$done|child::*"/>
		</xsl:apply-templates>
	</xsl:template>
	

<xsl:template match="core:superAttribute">
   <xsl:param name="done"/>
   <h3>Inherited Aspects</h3>
   <xsl:apply-templates select = "func:deref(@itemref)">
      <xsl:with-param name="done" select="$done"/>
   </xsl:apply-templates>
   
</xsl:template>
	
</xsl:stylesheet>