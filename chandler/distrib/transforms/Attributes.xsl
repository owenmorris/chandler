<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:core="//Schema/Core">
	<xsl:output method="html" encoding="ISO-8859-1"/>
	<xsl:key name="attr" match="core:Attribute" use="@itemName"/>
	<!-- Originally contributed by Micah Dubinko -->
	<!-- starting point -->
	<xsl:template match="core:Parcel">
		<html>
			<head>
				<title>
					<xsl:value-of select="core:displayName"/>
				</title>
			</head>
			<body>
				<h1>
					<xsl:value-of select="core:displayName"/>
				</h1>
				<xsl:apply-templates select="core:Kind"/>
			</body>
		</html>
	</xsl:template>
	<!-- match once here for each Kind -->
	<xsl:template match="core:Kind">
		<hr/>
		<h2>
			<a>
				<xsl:attribute name="href">
					<xsl:text>Detail.html#</xsl:text>
					<!-- Link to the relevant anchor by removing spaces in the displayName -->
					<xsl:value-of select="@itemName"/>
				</xsl:attribute>
				<xsl:value-of select="core:displayName"/>
			</a>
		</h2>
		<ul>
			<xsl:for-each select="core:attributes">
				<li>
					<a>
						<xsl:attribute name="href">
							<xsl:text>Detail.html#</xsl:text>
							<xsl:value-of select="../@itemName"/>
							<xsl:text>_</xsl:text>
							<xsl:value-of select="substring-after(@itemref, ':')"/>
						</xsl:attribute>
						<xsl:value-of select="key('attr', substring-after(@itemref, ':'))/core:displayName"/>
					</a>
				</li>
			</xsl:for-each>
		</ul>
	</xsl:template>
</xsl:stylesheet>