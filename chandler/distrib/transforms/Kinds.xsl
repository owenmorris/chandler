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
         <hr/>
         <xsl:apply-templates select="core:Kind"/>
       </body>
     </html>
   </xsl:template>
   
   <!-- match once here for each Kind -->
   <xsl:template match="core:Kind">
     <h3><xsl:value-of select="core:displayName"/></h3>
   </xsl:template>
   
 </xsl:stylesheet>
