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
                   <xsl:call-template name="createRelativePath">
                      <xsl:with-param name="src">
                         <xsl:apply-templates mode="translateURI" select="/core:Parcel/@describes" />
                      </xsl:with-param>
                      <xsl:with-param name="target" select="$constants.topURI"/>
                   </xsl:call-template>
				   <xsl:value-of select="$constants.cssFile" />
				   </xsl:attribute>
				</link>
			</head>
			<body>
			    <div style="float: left;">
				<h1>
					<xsl:apply-templates select="." mode="getDisplayName"/>
					<xsl:text> - </xsl:text>
					<xsl:apply-templates select="$coreDoc/core:Parcel/*[@itemName=$pagetype]" mode="getHrefAnchor">
					   <xsl:with-param name="text" select="$title"/>
					</xsl:apply-templates>
				</h1>
				</div>
				<div style="float: right;">Back to the 
				<a>
				<xsl:attribute  name = "href" >
                   <xsl:call-template name="createRelativePath">
                      <xsl:with-param name="src">
                         <xsl:apply-templates mode="translateURI" select="/core:Parcel/@describes" />
                      </xsl:with-param>
                      <xsl:with-param name="target" select="$constants.topURI"/>
                   </xsl:call-template>
				</xsl:attribute>
                Parcel Index
				</a>
				</div>
				<br clear="all"/>
		<div class="topDetailBox">
				<xsl:apply-templates select = "core:description" />
				<xsl:apply-templates select = "core:examples" />
				<xsl:apply-templates select = "core:issues" />
		</div>
				
				<xsl:for-each select = "core:Attribute">
                   <div class="sectionBox">
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
				   </div>
				</xsl:for-each>

				<xsl:for-each select = "core:Kind/core:Attribute">
                   <div class="sectionBox">
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
				   </div>
				</xsl:for-each>
				
			</body>
		</html>
	</xsl:template>

	<xsl:template match="core:Attribute">
	    <xsl:param name="done" select="exsl:node-set($empty)"/>
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

	<xsl:template match="core:description">
       <div class="description">
       <span class="detailLabel">Description </span>
       <xsl:value-of select="."/>
       </div>
	</xsl:template>

	<xsl:template match="core:examples">
	   <xsl:if test = "position()=1">
          <div class="detailLabel">Examples </div>
	   </xsl:if>
       <li class="examples"><xsl:value-of select="."/></li>	
	</xsl:template>

	<xsl:template match="core:issues">	   
	   <xsl:if test = "position()=1">
          <div class="detailLabel">Issues </div>
	   </xsl:if>
       <li class="issues"><xsl:value-of select="."/></li>	
	</xsl:template>

	
</xsl:stylesheet>