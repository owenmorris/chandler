<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:exsl="http://exslt.org/common"
     xmlns:func="http://exslt.org/functions"
     extension-element-prefixes="exsl func" 
     xmlns:core="//Schema/Core">
    
	<xsl:output method="html" encoding="ISO-8859-1"/>
	
    <xsl:include href="includes/helperFunctions.xsl"/>
    <xsl:include href="includes/constants.xsl"/>

    <xsl:variable name="pagetype" select="'Kind'"/>
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
					<li>
					    <span class="attributeTitle">issues:</span>
					    <xsl:if test = "core:issues">
					       <br/>
					       <ul>
					           <xsl:for-each select = "core:issues">
					              <li><xsl:value-of select="."/></li>
					           </xsl:for-each>
					       </ul>
					    </xsl:if>
					</li>
				</ul>
				<xsl:apply-templates select="core:Kind"/>
			</body>
		</html>
	</xsl:template>
	
	<xsl:template match="core:Kind">
		<hr/>
		<h2>
            <xsl:apply-templates select="." mode="getHrefAnchor">
               <xsl:with-param name="text" select="'#'"/>
            </xsl:apply-templates>
            <xsl:apply-templates select = "." mode="getNameAnchor"/>
            <xsl:text> - inherits from </xsl:text>
            
            <xsl:choose>
            	<xsl:when test="core:superKinds">
            	   <xsl:apply-templates select="core:superKinds" mode="derefHref"/>
            	</xsl:when>
              
            	<xsl:otherwise>
                   <xsl:apply-templates select="$coreDoc//core:Kind[@itemName='Item']" mode="getHrefAnchor"/>
            	</xsl:otherwise>
            </xsl:choose>

       
			<br/>
		</h2>
		<ul>
			<li>
				<span class="attributeTitle">description: </span>
				<xsl:value-of select="core:description"/>
			</li>
			<li>
				<span class="attributeTitle">examples: </span>
                <ul>
				<xsl:for-each select="core:examples">
					<li><xsl:value-of select="." /></li>
				</xsl:for-each>
                </ul>
            </li>
			<li>
				<span class="attributeTitle">issues: </span>
				<ul>
				<xsl:for-each select="core:issues">
					<li><xsl:value-of select="." /></li>
				</xsl:for-each>
				</ul>
			</li>
			<li>
				<span class="attributeTitle">displayAttribute: </span>
				
				<xsl:variable name = "displayAttribute" select = "func:getAttributeValue(., 'displayAttribute')" />
				
 				<xsl:choose>
					<xsl:when test="$displayAttribute/@itemName">
					   <xsl:apply-templates select="$displayAttribute" mode="getHrefAnchor" />
					</xsl:when>
				  
					<xsl:otherwise>
					   <xsl:value-of select="$displayAttribute" />
					</xsl:otherwise>
				</xsl:choose>
			
			</li>
		</ul>
		
           <table cellpadding="5" cellspacing="0" border="0" style="width: 100%; text-align: left;">
              <tbody>
                 <xsl:call-template name = "attributesTableHeaderRow" />
                 <xsl:if test = "core:attributes">
                    <xsl:call-template name = "attributesTableTitleRow" />
                    <xsl:apply-templates select="core:attributes"/>
                 </xsl:if>
                 
                 <xsl:if test = "func:hasSuperKind(.)">
                    <xsl:call-template name = "attributesTableTitleRow" >
                       <xsl:with-param name="text" select="'Inherited Attributes'"/>
                    </xsl:call-template>
                    <xsl:apply-templates select="." mode="inheritAttributes"/>
                 </xsl:if>
              </tbody>
           </table>
		
	</xsl:template>


<xsl:variable name = "columns">
  <column>displayName</column>
  <column>itemName</column>
  <column>cardinality</column>
  <column>type</column>
  <column>inverseAttribute</column>
  <column>required</column>
  <column>defaultValue</column>
</xsl:variable>

<xsl:template name="attributesTableTitleRow">
   <xsl:param name="text" select="'Attributes'"/>
   <tr><td class="tableHeaderCell" colspan="{count(exsl:node-set($columns)/column)}"
           style="width: 100%; text-align: center;">
           <xsl:copy-of select="$text" />
       </td>
   </tr>
</xsl:template>


<xsl:template name="attributesTableHeaderRow">
   <tr>
      <xsl:for-each select = "exsl:node-set($columns)/column">
         <td class="tableHeaderCell">
         
         <xsl:choose>
         	<xsl:when test="$coreDoc//*[@itemName=current()]">
               <xsl:apply-templates select = "$coreDoc//*[@itemName=current()]" mode="getHrefAnchor">
                  <xsl:with-param name="text" select="."/>
               </xsl:apply-templates>         	
         	</xsl:when>
         	<xsl:otherwise>
         	   <xsl:value-of select="." />
         	</xsl:otherwise>
         </xsl:choose>
         </td>
      </xsl:for-each>
   </tr>
</xsl:template>


<xsl:template match="core:Attribute">
   <xsl:param name="position" select="position()"/>
   <tr class="row{$position mod 2}">
      <td class="attributeTitle">
         <!-- displayName -->
         <xsl:apply-templates select = "." mode="getDisplayName"/>
      </td>
      <td>
         <!-- itemName -->
         <xsl:apply-templates select = "." mode="getHrefAnchor">
            <xsl:with-param name="text" select="@itemName"/>
         </xsl:apply-templates>
      </td>
      <td>
         <!-- cardinality -->
         <xsl:value-of select="func:getAspect(., 'cardinality')" />
      </td>
      <td>
         <!-- type -->
         <xsl:apply-templates select = "func:getAspect(., 'type')" mode="derefHref"/>
         <xsl:text> (</xsl:text>
         <xsl:apply-templates select = "func:getAspect(., 'type')/@itemref" mode="getSchema"/>
         <xsl:text>)</xsl:text>
      </td>
      <td>
         <!-- inverseAttribute -->
         <xsl:apply-templates select = "core:inverseAttribute" mode="derefHref"/>
      </td>
      <td>
         <!-- required -->
         <xsl:value-of select = "func:getAspect(., 'required')" />
      </td>
      <td>
         <!-- defaultValue -->
         <xsl:value-of select = "func:getAspect(., 'defaultValue')" />
      </td>
   </tr>
</xsl:template>


<xsl:template match="core:attributes">
   <xsl:apply-templates select="func:deref(@itemref)">
      <xsl:with-param name="position" select="position()"/>
   </xsl:apply-templates>
</xsl:template>


   <xsl:template match="core:Kind" mode="inheritAttributes">
      <xsl:choose>
      	<xsl:when test = "core:superKinds">
           <xsl:apply-templates select = "func:deref(core:superKinds/@itemref)/core:attributes" />
           <xsl:apply-templates select = "func:deref(core:superKinds/@itemref)" mode="inheritAttributes"/>
      	</xsl:when>
      	<xsl:when test="func:hasSuperKind(.)">
           <xsl:apply-templates select = "$coreDoc//core:Kind[@itemName='Item']/core:attributes"/>
           <xsl:apply-templates select = "$coreDoc//core:Kind[@itemName='Item']" mode="inheritAttributes"/>
      	</xsl:when>
      </xsl:choose>         
   </xsl:template>

</xsl:stylesheet>