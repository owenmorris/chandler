<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:core="//Schema/Core">
	<xsl:output method="html" encoding="ISO-8859-1"/>
	<xsl:key name="attr" match="core:Attribute" use="@itemName"/>
	<xsl:template match="core:Parcel">
		<html>
			<head>
				<title>
					<xsl:value-of select="core:displayName"/>
					<xsl:text> - Detail</xsl:text>
				</title>
				<link rel="stylesheet" type="text/css" href="http://aloha.osafoundation.org/~skinner/2003/XSL/detail.css"/>
			</head>
			<body>
				<h1>
					<xsl:value-of select="core:displayName"/>
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
			<xsl:value-of select="core:displayName"/>
			<!-- What's wanted here?  Why <= Item? -->
			<xsl:text> &lt;= Item</xsl:text>
			<br/>
		</h2>
		<ul>
			<li>
				<span class="attributeTitle">description: </span>
				<xsl:value-of select="core:description"/>
			</li>
			<li>
				<span class="attributeTitle">examples: </span>
				<xsl:value-of select="core:examples"/>
			</li>
			<li>
				<span class="attributeTitle">issues: </span>
				<xsl:value-of select="core:issues"/>
			</li>
			<li>
				<span class="attributeTitle">displayAttribute: </span>
				<a>
					<xsl:attribute name="href">
						<xsl:text>#</xsl:text>
						<xsl:value-of select="@itemName"/>
						<xsl:text>_</xsl:text>
						<xsl:value-of select="substring-after(core:displayAttribute/@itemref, ':')"/>
					</xsl:attribute>
					<xsl:value-of select="key('attr', substring-after(core:displayAttribute/@itemref, ':'))/core:displayName"/>
				</a>
			</li>
		</ul>
		<table cellpadding="5" cellspacing="0" border="0"
 style="width: 100%; text-align: left;">
			<tbody>
				<xsl:call-template name="tableHeader"/>
				<xsl:for-each select="core:attributes">
					<tr class="row{position() mod 2}">
						<td class="attributeTitle">
							<a>
								<xsl:attribute name="name">
									<xsl:value-of select="../@itemName"/>
									<xsl:text>_</xsl:text>
									<xsl:value-of select="substring-after(@itemref, ':')"/>
								</xsl:attribute>
							</a>
							<xsl:value-of select="key('attr', substring-after(@itemref, ':'))/core:displayName"/>
						</td>
						<td>
							<xsl:value-of select="substring-after(@itemref, ':')"/>
						</td>
						<td>
							<xsl:value-of select="key('attr', substring-after(@itemref, ':'))/core:cardinality"/>
						</td>
						<!-- The itemref should be dereferenced, haven't dealt with this yet-->
						<td>
							<xsl:value-of select="key('attr', substring-after(@itemref, ':'))/core:type/@itemref"/>
						</td>
						<td>
							<!-- required -->
						</td>
						<td>
							<!-- defaultValue -->
						</td>
						<td>
							<!-- inheritFrom -->
						</td>
						<td>
							<!-- superAttribute -->
						</td>
						<td>
							<!-- hidden -->
						</td>
						<td>
							<!-- derivationNotes -->
						</td>
						<td>
							<!-- inverseAttribute -->
							<xsl:value-of select="key('attr', substring-after(@itemref, ':'))/core:inverseAttribute/@itemref"/>
						</td>
						<td>
							<!-- description -->
						</td>
						<td>
							<!-- examples -->
						</td>
						<td>
							<!-- issues -->
						</td>
					</tr>
				</xsl:for-each>
			</tbody>
		</table>
	</xsl:template>
	<xsl:template name="tableHeader">
		<tr>
			<td class="tableHeaderCell">displayName</td>
			<td class="tableHeaderCell">itemName</td>
			<td class="tableHeaderCell">cardinality</td>
			<td class="tableHeaderCell">type</td>
			<td class="tableHeaderCell">required</td>
			<td class="tableHeaderCell">defaultValue</td>
			<td class="tableHeaderCell">inheritFrom</td>
			<td class="tableHeaderCell">superAttribute</td>
			<td class="tableHeaderCell">hidden</td>
			<td class="tableHeaderCell">derivationNotes</td>
			<td class="tableHeaderCell">inverseAttribute</td>
			<td class="tableHeaderCell">description</td>
			<td class="tableHeaderCell">examples</td>
			<td class="tableHeaderCell">issues</td>
		</tr>
	</xsl:template>
</xsl:stylesheet>