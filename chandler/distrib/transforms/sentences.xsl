<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:core="//Schema/Core"
     xmlns:exsl="http://exslt.org/common"
     xmlns:func="http://exslt.org/functions"
     extension-element-prefixes="exsl func" 
     >
    
	<xsl:output method="html" encoding="ISO-8859-1"/>
	
    <xsl:include href="includes/helperFunctions.xsl"/>
    <xsl:include href="includes/constants.xsl"/>

    <xsl:variable name="pagetype" select="'sentence'"/>
    <xsl:variable name="filename" select="concat($pagetype, 's.html')"/>
    <xsl:variable name="title" select="concat($pagetype, 's')"/>
    
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
					<xsl:text> - Sentence descriptions</xsl:text>
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



<xsl:template match="core:attributes">

	   <xsl:if test = "position()=1">
          <div class="indentTitle">Attributes</div>
	   </xsl:if>
	   <xsl:variable name = "attribute" select="func:deref(@itemref)"/>
		<div class="detailBox">

<xsl:choose>
	<xsl:when test="$attribute">
                        <xsl:variable name = "type">
					       <xsl:apply-templates select="func:deref($attribute/core:type/@itemref)" mode="getDisplayName"/>
					    </xsl:variable>
                        <xsl:variable name = "cardinality" select="func:getAspect($attribute, 'cardinality')"/>
					    <xsl:apply-templates select = "$attribute" mode="getHrefAnchor"/>
					    is a
					    <xsl:choose>
					      <xsl:when test = "$cardinality='single'">
					         <xsl:choose>
					         	<xsl:when test="$attribute/@itemref">
					         	   single
					         	   <xsl:value-of select="$type"/>
					         	   value.
					         	</xsl:when>
					         	<xsl:otherwise>
					         	   reference to a single
					         	   <xsl:value-of select="$type"/>
					         	   item.					         	 
					         	</xsl:otherwise>
					         </xsl:choose>
					      </xsl:when>
					      <xsl:when test = "$cardinality='list'">
					         <xsl:choose>
					         	<xsl:when test="$attribute/@itemref">
					         	   list of
					         	   <xsl:value-of select="$type"/>
					         	   values.
					         	</xsl:when>
					         	<xsl:otherwise>
					         	   list of references to
					         	   <xsl:value-of select="$type"/>
					         	   items.					         	 
					         	</xsl:otherwise>
					         </xsl:choose>
					      </xsl:when>
					      <xsl:when test = "$cardinality='dict'">
					         <xsl:choose>
					         	<xsl:when test="$attribute/@itemref">
					         	   dictionary of
					         	   <xsl:value-of select="$type"/>
					         	   values.
					         	</xsl:when>
					         	<xsl:otherwise>
					         	   dictionary of references to
					         	   <xsl:value-of select="$type"/>
					         	   items.					         	 
					         	</xsl:otherwise>
					         </xsl:choose>
					      </xsl:when>
					      <xsl:otherwise>
					         <b>possible mistake, it has cardinality other than single, list, or dictionary.</b>
					         Its cardinality is "<xsl:value-of select="$cardinality" />".
					      </xsl:otherwise>					      
					    </xsl:choose>

<xsl:if test = "$attribute/core:description or $attribute/core:issues">
		<xsl:apply-templates select = "$attribute/core:description" />
        <xsl:if test = "$attribute/core:issues">
				<ul>
				<xsl:apply-templates select = "$attribute/core:issues" />
				</ul>
        </xsl:if>
</xsl:if>

	</xsl:when>
  
	<xsl:otherwise>

	  <li>The attribute referred to as <xsl:value-of select="@itemref" /> can't be found.</li>

	</xsl:otherwise>
</xsl:choose>
</div>

</xsl:template>
	
	<xsl:template match="core:Kind">
		<div class="sectionBox">
        <div class="kindDetailBox">

	    <span class="sentenceHeader">		
            <xsl:apply-templates select="." mode="getHrefAnchor"/>
		    is a Kind defined in 
					<xsl:apply-templates select="/core:Parcel" mode="getDisplayName"/>
		</span><br/><br/>
        <xsl:if test = "core:description or core:examples or core:issues">
				<xsl:apply-templates select = "core:description" />
				<xsl:apply-templates select = "core:examples" />
				<xsl:apply-templates select = "core:issues" />
		</xsl:if>
		</div>

				<xsl:apply-templates select = "core:attributes" />
		</div>

	</xsl:template>	
   
</xsl:stylesheet>
