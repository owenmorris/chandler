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
         <title><xsl:value-of select="core:displayName"/></title>
       </head>
       <body>
         <h1><xsl:value-of select="core:displayName"/></h1>
         <xsl:apply-templates select="core:Kind"/>
       </body>
     </html>
   </xsl:template>
   
   <!-- match once here for each Kind -->
   <xsl:template match="core:Kind">
     <hr/>
     <h2><xsl:value-of select="core:displayName"/></h2>
     <ul>
     <xsl:for-each select="core:attributes">
        <li><xsl:value-of select="key('attr', @itemref)/core:displayName"/></li>
     </xsl:for-each>
     </ul>
   </xsl:template>
   
 </xsl:stylesheet>
