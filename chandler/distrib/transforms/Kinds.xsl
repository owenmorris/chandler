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
				<div style="float: right; border-style: solid; border-width: 1px; padding: 5px;">
				<a>
				<xsl:attribute  name = "href" >
                   <xsl:call-template name="createRelativePath">
                      <xsl:with-param name="src">
                         <xsl:apply-templates mode="translateURI" select="/core:Parcel/@describes" />
                      </xsl:with-param>
                      <xsl:with-param name="target" select="$constants.topURI"/>
                   </xsl:call-template>
                   <xsl:value-of select = "$constants.helpFile" />
				</xsl:attribute>
                Help</a>
                with this page
				--
				
				Back to the 
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

				<xsl:call-template name="hierarchyTop"/>
                <div class="topDetailBox">
                   <xsl:apply-templates select = "core:description" />
                   <xsl:apply-templates select = "core:version" />
                   <xsl:apply-templates select = "core:author" />
                   <xsl:apply-templates select = "core:examples" />
                   <xsl:apply-templates select = "core:issues" />
                </div>				
				<xsl:apply-templates select="core:Kind"/>
			</body>
		</html>
	</xsl:template>

	<xsl:template match="core:description">
       <div class="description">
       <span class="detailLabel">Description </span>
       <xsl:value-of select="."/>
       </div>
	</xsl:template>

	<xsl:template match="core:author">
       <div class="author">
       <span class="detailLabel">Author </span>
       <xsl:value-of select="."/>
       </div>
	</xsl:template>

	<xsl:template match="core:version">
       <div class="version">
       <span class="detailLabel">Version </span>
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

	<xsl:template name="displayAttribute">
       <div class="displayAttribute">
       <span class="detailLabel">displayAttribute </span>
				<xsl:variable name = "displayAttribute" select = "func:getAttributeValue(., 'displayAttribute')" />
				
 				<xsl:choose>
					<xsl:when test="$displayAttribute/@itemName">
					   <xsl:apply-templates select="$displayAttribute" mode="getHrefAnchor" />
					</xsl:when>
				  
					<xsl:otherwise>
					   <xsl:value-of select="$displayAttribute" />
					</xsl:otherwise>
				</xsl:choose>
       </div>
	</xsl:template>

	<xsl:template name="hierarchyTop">
	<xsl:variable name = "isCore" select = "$root/core:Parcel/@describes = $constants.coreURI" />
	<div class="inheritanceBox">
	   <div class="detailLabel">Inheritance Structure </div>
	   <div class="inheritanceBranch">
       <xsl:apply-templates select = "$coreDoc//core:Kind[@itemName='Item']" mode="hierarchy">
          <xsl:with-param name="local" select="$isCore"/>
       </xsl:apply-templates>
       </div>

       <xsl:if test = "not($isCore)">
	      <div class="inheritanceBranch">
          <xsl:apply-templates select = "func:accumulateNonLocalParents($root//core:Kind[core:superKinds])" mode="hierarchy">
             <xsl:with-param name="local" select="false()"/>
          </xsl:apply-templates>
          </div>
       </xsl:if>
       <div class="rightSpacer"><xsl:text disable-output-escaping="yes">&amp;nbsp;</xsl:text>
       </div>
    </div>
       <br clear="all"/>

	</xsl:template>
	
<func:function name="func:accumulateNonLocalParents">
   <xsl:param name="set" />
   <xsl:param name="parents" select="/empty"/> 
   <xsl:choose>
   	<xsl:when test="$set">
   <xsl:variable name = "currentParent" select = "func:deref($set[func:deref(core:superKinds/@itemref)/@itemName!='Item'
   	    and func:deref(core:superKinds/@itemref)/ancestor::core:Parcel/@describes != $root//core:Parcel/@describes][1]/core:superKinds/@itemref)" />

   	 <func:result select="func:accumulateNonLocalParents($set[func:refPrimary(core:superKinds/@itemref)!=$currentParent/@itemName], $parents | $currentParent)"/>
   	</xsl:when>
     
   	<xsl:otherwise>
   	 <func:result select="$parents"/>
   	</xsl:otherwise>
   </xsl:choose>   
</func:function>


	<xsl:template match="*" mode="hierarchy">
	   <xsl:param name="local" select="true()" />
       <xsl:variable name = "name" select = "@itemName" />
	      
	      <xsl:choose>
	      	<xsl:when test="$local">
	      	   <xsl:choose>
	      	   	<xsl:when test="$name='Item'">
                  <xsl:apply-templates select="." mode="getHrefAnchor">
                     <xsl:with-param name="text" select="'#'"/>
                  </xsl:apply-templates>
                  <xsl:text> </xsl:text>
                  <xsl:apply-templates select = "." mode="getDisplayName"/>
	      	   	</xsl:when>
	      	     
	      	   	<xsl:otherwise>
               <li class="inheritanceTreeItem">
                  <xsl:apply-templates select="." mode="getHrefAnchor">
                     <xsl:with-param name="text" select="'#'"/>
                  </xsl:apply-templates>
                  <xsl:text> </xsl:text>
                  <xsl:apply-templates select = "." mode="getDisplayName"/>
	           </li>	      	   	 
	      	   	</xsl:otherwise>
	      	   </xsl:choose>
	      	</xsl:when>
	        
	      	<xsl:otherwise>
                  <xsl:apply-templates select = "." mode="getDisplayName"/>
	      	</xsl:otherwise>
	      </xsl:choose>
	      <xsl:variable name = "children" select = "$root//core:Kind[func:getAttributeValue(.,'superKinds')/@itemName=$name and ./@itemName != $name]" />
	      <xsl:if test = "$children">
             <ul class="inheritanceTreeItem">
                <xsl:apply-templates select = "$children" mode="hierarchy"/>
             </ul>
	      </xsl:if>
	</xsl:template>

	
	<xsl:template match="core:Kind">
       <div class="sectionBox">
		<h2>
            <xsl:apply-templates select = "." mode="getNameAnchor"/>
            <xsl:if test = "@itemName != 'Item'">
               <xsl:text> - inherits from </xsl:text>
               
               <xsl:choose>
                  <xsl:when test="core:superKinds">
                     <xsl:apply-templates select="core:superKinds" mode="derefHref"/>
                  </xsl:when>
              
                  <xsl:otherwise>
                     <xsl:apply-templates select="$coreDoc//core:Kind[@itemName='Item']" mode="getHrefAnchor"/>
                  </xsl:otherwise>
               </xsl:choose>
            </xsl:if>
		</h2>
		<div class="detailBox">
				<xsl:call-template name="displayAttribute" select="."/>
				<xsl:apply-templates select = "core:description" />
				<xsl:apply-templates select = "core:examples" />
				<xsl:apply-templates select = "core:issues" />
		</div>
		   <div class="tableBox">
           <table cellpadding="2" cellspacing="2" border="0" style="width: 100%; text-align: left;">
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
           </div>
       </div>
	</xsl:template>


<xsl:variable name = "columns">
  <column>displayName</column>
  <column>itemName</column>
  <column>type</column>
  <column>cardinality</column>
  <column>inverseAttribute</column>
  <column>superAttribute</column>
  <column>required</column>
  <column>defaultValue</column>
</xsl:variable>

<xsl:template name="attributesTableTitleRow">
   <xsl:param name="text" select="'Attributes'"/>
   <tr><td class="tableTitleRow" colspan="{count(exsl:node-set($columns)/column)}"
           style="width: 100%; text-align: left; font-weight: bold;">
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
         <!-- type -->
         <xsl:apply-templates select = "func:getAspect(., 'type')" mode="derefHref"/>
      </td>
      <td>
         <!-- cardinality -->
         <xsl:value-of select="func:getAspect(., 'cardinality')" />
      </td>
      <td>
         <!-- inverseAttribute -->
         <xsl:apply-templates select = "core:inverseAttribute" mode="derefHref"/>
      </td>
      <td>
         <!-- superAttribute -->
         <xsl:apply-templates select = "core:superAttribute" mode="derefHref"/>
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