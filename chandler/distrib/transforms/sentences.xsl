<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:core="//Schema/Core">
    
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
				      <xsl:value-of select="$constants.cssPath" />
				   </xsl:attribute>
				</link>
			</head>
			<body>
				<h1>
					<xsl:apply-templates select="." mode="getDisplayName"/>
				</h1>
      <xsl:if test = "core:description!=''">
						<i><xsl:value-of select="core:description"/></i>
      </xsl:if>
				<xsl:apply-templates select="core:Kind"/>
			</body>
		</html>
	</xsl:template>
	
	<xsl:template match="core:Kind">
		<hr/>
		<h2>
            <xsl:apply-templates select="." mode="getHrefAnchor"/>
		</h2>
      <xsl:if test = "core:description!=''">
			<i><xsl:value-of select="core:description"/></i>
      </xsl:if>
				<ul>
				<xsl:for-each select="core:attributes">
					<li>
					    <xsl:variable name = "typeSchema">
					       <xsl:apply-templates select = "@itemref" mode="getTypeSchema"/>
					    </xsl:variable>
                        <xsl:variable name = "isValue" select="$coreDoc/core:Parcel/core:displayName=$typeSchema"/>
					    <xsl:variable name = "cardinality">
					          <xsl:apply-templates select = "@itemref" mode="derefChild">
					             <xsl:with-param name="child" select="'cardinality'" />
					          </xsl:apply-templates>
						</xsl:variable>

					    <xsl:variable name = "description">
					          <xsl:apply-templates select = "@itemref" mode="derefChild">
					             <xsl:with-param name="child" select="'description'" />
					          </xsl:apply-templates>
						</xsl:variable>

					    <xsl:variable name = "issues">
					          <xsl:apply-templates select = "@itemref" mode="derefChild">
					             <xsl:with-param name="child" select="'issues'" />
					          </xsl:apply-templates>
						</xsl:variable>

						<xsl:variable name="type">
                            <xsl:apply-templates select = "@itemref" mode="doubleDerefDisplayName">
                               <xsl:with-param name="child" select="'type'" />
                            </xsl:apply-templates>
						</xsl:variable>

					    <xsl:apply-templates select = "." mode="derefHref"/>
					    is a
					    <xsl:choose>
					      <xsl:when test = "$cardinality='single' or $cardinality=''">
					         <xsl:choose>
					         	<xsl:when test="$isValue">
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
					         	<xsl:when test="$isValue">
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
					         	<xsl:when test="$isValue">
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
						<xsl:value-of select="$description"/>
						<xsl:value-of select="$issues"/>
					</li>
				</xsl:for-each>
			</ul>
	</xsl:template>	
   
</xsl:stylesheet>
