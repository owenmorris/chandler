<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:core="//Schema/Core">
    
	<xsl:output method="html" encoding="ISO-8859-1"/>
	
    <xsl:include href="includes/helperFunctions.xsl"/>
    <xsl:include href="includes/constants.xsl"/>

    <xsl:variable name="pagetype" select="'Kind'"/>
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
					<xsl:value-of select="core:displayName"/>
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
					   <xsl:value-of select="core:displayName"/>
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
            <xsl:if test = "core:superKinds">
               <xsl:text> &lt;= </xsl:text>
               <xsl:apply-templates select="core:superKinds" mode="derefHref"/>
            </xsl:if>
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
                <xsl:apply-templates select = "core:displayAttribute" mode="derefHref"/>
			</li>
		</ul>
		<table cellpadding="5" cellspacing="0" border="0"
 style="width: 100%; text-align: left;">
			<tbody>
		<tr>
			<td class="tableHeaderCell">displayName</td>
			<td class="tableHeaderCell">itemName</td>
			<td class="tableHeaderCell">cardinality</td>
			<td class="tableHeaderCell">type</td>
			<td class="tableHeaderCell">inverseAttribute</td>
			<td class="tableHeaderCell">required</td>
			<td class="tableHeaderCell">defaultValue</td>
			<td class="tableHeaderCell">hidden</td>
		</tr>
				<xsl:for-each select="core:attributes">
					<tr class="row{position() mod 2}">
						<td class="attributeTitle">
						    <!-- displayName -->
                            <xsl:apply-templates select = "@itemref" mode="derefDisplayName"/>
						</td>
						<td>
						    <!-- itemName -->
						    <xsl:apply-templates select = "." mode="derefHref">
                               <xsl:with-param name="text">
                                  <xsl:apply-templates mode="quickRef" select = "@itemref" />
                               </xsl:with-param>
							</xsl:apply-templates>
						</td>
						<td>
						    <!-- cardinality -->
						          <xsl:apply-templates select = "@itemref" mode="derefChild">
						             <xsl:with-param name="child" select="'cardinality'" />
						          </xsl:apply-templates>
						</td>
						<td>
						    <!-- type -->
                            <xsl:apply-templates select = "@itemref" mode="doubleDerefHref">
                               <xsl:with-param name="child" select="'type'" />
                            </xsl:apply-templates>
						    <xsl:text> (</xsl:text>
						    <xsl:apply-templates select = "@itemref" mode="getTypeSchema"/>
						    <xsl:text>)</xsl:text>
						</td>
						<td>
							<!-- inverseAttribute -->
                            <xsl:apply-templates select = "@itemref" mode="doubleDerefHref">
                               <xsl:with-param name="child" select="'inverseAttribute'" />
                            </xsl:apply-templates>
                        </td>
						<td>
							<!-- required -->
						</td>
						<td>
							<!-- defaultValue -->
						</td>
						<td>
							<!-- hidden -->
						</td>
					</tr>
				</xsl:for-each>
			</tbody>
		</table>
	</xsl:template>
	
   <xsl:template match="@itemref" mode="getTypeSchema">
      <xsl:variable name="ref">
         <xsl:apply-templates select="." mode="quickRef" />
      </xsl:variable>
      <xsl:variable name="relpath">
         <xsl:apply-templates select="." mode="quickRelpath" />
      </xsl:variable>
      <xsl:choose>
         <xsl:when test="$relpath=''">
            <xsl:apply-templates select="/core:Parcel/*[@itemName=$ref]/core:type/@itemref" mode="getSchema"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:variable name="otherdoc" select="document(concat($relpath, $constants.parcelFileName), /)" />
            <xsl:apply-templates select="$otherdoc/core:Parcel/*[@itemName=$ref]/core:type/@itemref" mode="getSchema"/>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   
   <xsl:template match="@itemref" mode="getSchema">
      <xsl:variable name="relpath">
         <xsl:apply-templates select="." mode="quickRelpath" />
      </xsl:variable>
      <xsl:choose>
         <xsl:when test="$relpath=''">
            <xsl:value-of select="/core:Parcel/core:displayName"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:variable name="otherdoc" select="document(concat($relpath, $constants.parcelFileName), /)" />
            <xsl:value-of select="$otherdoc/core:Parcel/core:displayName" />
         </xsl:otherwise>
      </xsl:choose>
      <xsl:value-of select="./core:Parcel/core:displayName"/>
   </xsl:template>   
   
</xsl:stylesheet>