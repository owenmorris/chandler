<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:core="//Schema/Core">

   <xsl:variable name = "root" select = "/" />     

<!-- 
     createRelativePath creates a relative path from two absolute (UNIX style) paths.
     The algorithm assumes that src and target are absolute paths
       (protocol and host information will be ignored as long as they're
       identical, if they aren't, you couldn't get a relative path anyway)
     and it assumes that those paths DO NOT have trailing slashes.
     
     createRelativePath recurses, discarding matching roots, then adddotdots
     takes target and prepends ../ for each remaining directory in the source path
-->
	<xsl:template name="createRelativePath">
		<xsl:param name="src"/>
		<xsl:param name="target"/>
		<xsl:choose>
           <xsl:when test = "$src=$target"/>
           <xsl:when test = "substring-after($src, '/')='' or substring-after($target, '/')=''">
              <xsl:choose>
                 <xsl:when test = "substring-before($src, '/')=$target or substring-before($target, '/')=$src">
                    <xsl:call-template name="adddotdots">
                       <xsl:with-param name="src" select="substring-after($src, '/')"/>
                       <xsl:with-param name="target" select="substring-after($target, '/')"/>
                    </xsl:call-template>
                 </xsl:when>
                 <xsl:otherwise>
                    <xsl:call-template name="adddotdots">
                       <xsl:with-param name="src" select="$src"/>
                       <xsl:with-param name="target" select="$target"/>
                    </xsl:call-template>
                 </xsl:otherwise>
              </xsl:choose>
           </xsl:when>           
           <xsl:when test = "substring-before($src, '/')!=substring-before($target, '/')">
              <xsl:call-template name="adddotdots">
                 <xsl:with-param name="src" select="$src"/>
                 <xsl:with-param name="target" select="$target"/>
              </xsl:call-template>
           </xsl:when>
           <xsl:otherwise>
              <xsl:call-template name="createRelativePath">
                 <xsl:with-param name="src" select="substring-after($src, '/')"/>
                 <xsl:with-param name="target" select="substring-after($target, '/')"/>
              </xsl:call-template>           
           </xsl:otherwise> 
		</xsl:choose>
	</xsl:template>

	<xsl:template name="adddotdots">
		<xsl:param name="src"/>
		<xsl:param name="target"/>
		<xsl:choose>
           <xsl:when test = "$src=''">
              <xsl:value-of select="$target" />
                 <xsl:if test = "substring($target, string-length($target)!='/')">
              <xsl:text>/</xsl:text>
              </xsl:if>
           </xsl:when>           
           <xsl:otherwise>
              <xsl:call-template name="adddotdots">
                 <xsl:with-param name="src" select="substring-after($src, '/')"/>
                 <xsl:with-param name="target" select="concat('../', $target)"/>
              </xsl:call-template>           
           </xsl:otherwise> 
		</xsl:choose>
	</xsl:template>

<!-- translateURI returns the given string, unless it's a special URI
     like core
-->
	<xsl:template match="*|@*|text()" mode="translateURI">
	   <xsl:choose>
	   	<xsl:when test="string(.)=$constants.coreURI">
	   	   <xsl:value-of select="$constants.corePath" />
	   	</xsl:when>
	     
	   	<xsl:otherwise>
	   	   <xsl:value-of select="string(.)" />
	   	</xsl:otherwise>
	   </xsl:choose>
	</xsl:template>

<!-- Map QNames to their associated URI, except when the URI is for core.
     Note that prefix may be an empty string
-->
	<xsl:template match="@itemref" mode="getURIFromQName">
	   <xsl:variable name="prefix" select="substring-before(.,':')"/>
	   <xsl:variable name="uri" select="../namespace::*[local-name()=$prefix]"/>
	   <xsl:apply-templates mode="translateURI" select="$uri"/>
	</xsl:template>

	
<!-- quickRelPath takes a attribute whose value is a reference and creates
     a relative path to it, assuming that the current documents URI is
     accurately described by /core:Parcel/@describes
-->
   <xsl:template match="@itemref" mode="quickRelpath">
      <xsl:call-template name="createRelativePath">
         <xsl:with-param name="src" select="/core:Parcel/@describes" />

         <xsl:with-param name="target">
            <xsl:apply-templates mode="getURIFromQName" select="." />
         </xsl:with-param>
      </xsl:call-template>
   </xsl:template>
   
<!-- Remove text up to and including a ':' character to get the local name
     of the object being referred to.
-->
   <xsl:template match="@itemref" mode="quickRef">
      <xsl:choose>
         <xsl:when test="substring-after(., ':')=''">
            <xsl:value-of select="." />   
   	     </xsl:when>
   	     <xsl:otherwise>
            <xsl:value-of select="substring-after(., ':')" />   	 
   	     </xsl:otherwise>
      </xsl:choose>
   </xsl:template>	

<!-- Get the content of the referenced item's child -->
   <xsl:template match="@itemref" mode="derefChild">
      <xsl:param name="child"/>
      <xsl:variable name="ref">
         <xsl:apply-templates select="." mode="quickRef" />
      </xsl:variable>
      <xsl:variable name="relpath">
         <xsl:apply-templates select="." mode="quickRelpath" />
      </xsl:variable>
      <xsl:choose>
         <xsl:when test="$relpath=''">
            <xsl:value-of select="/core:Parcel/*[@itemName=$ref]/*[local-name()=$child]"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:variable name="otherdoc" select="document(concat($relpath, $constants.parcelFileName), /)" />
            <xsl:value-of select="$otherdoc/core:Parcel/*[@itemName=$ref]/*[local-name()=$child]"/>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>

<!-- derefDisplayName defaults to using the itemName if no
     displayName exists, as is the case for many items in Core.
-->
   <xsl:template match="@itemref" mode="derefDisplayName">
      <xsl:variable name="display">         
         <xsl:apply-templates select="." mode="derefChild">
            <xsl:with-param name="child" select="'displayName'"/>
         </xsl:apply-templates>
      </xsl:variable>
      <xsl:value-of select="$display" />
      <xsl:if test = "$display=''">
         <xsl:apply-templates select="." mode="quickRef" />
      </xsl:if>
   </xsl:template>

<!-- getDisplayName defaults to using the itemName if no
     displayName exists, as is the case for many items in Core.
-->
   <xsl:template match="*" mode="getDisplayName">
      <xsl:choose>
         <xsl:when test="string-length(core:displayName)>0">
            <xsl:value-of select="core:displayName" />
         </xsl:when>
         <xsl:otherwise>
            <xsl:value-of select="@itemName" />
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>

<!-- Return the name that hrefs should link to.  Names for Attributes and Kinds
     should just be the itemName,unless the attribute is a local attribute, in
     which case it should be named (parent itemName)_(itemName)
-->
   <xsl:template match="*" mode="getHrefName">
      <xsl:if test = "local-name(..)='Kind'">
      <xsl:value-of select="../@itemName"/>
         <xsl:text>_</xsl:text>
      </xsl:if>
      <xsl:value-of select="@itemName"/>
   </xsl:template>

<!-- Get the file type.  This is the local name + s.html, unless this is a 
     local attribute, in which case return Kinds.html.
-->
   <xsl:template match="*" mode="getFilename">
      <xsl:choose>
      	<xsl:when test="local-name(..)='Kind'">
      	   <xsl:value-of select="'Kinds.html'"/>
      	</xsl:when>
      	<xsl:otherwise>
      	   <xsl:value-of select="concat(local-name(.),'s.html')"/>
      	</xsl:otherwise>
      </xsl:choose>
   </xsl:template>

<!-- create an anchor linking to the given item -->
   <xsl:template match="*" mode="getHrefAnchor">
      <xsl:param name="text" />
      <a>
         <xsl:attribute name="href">
            <xsl:variable name="relpath">
               <xsl:call-template name="createRelativePath">
                  <xsl:with-param name="src">
                     <xsl:apply-templates mode="translateURI" select="$root/core:Parcel/@describes" />
                  </xsl:with-param>
                  <xsl:with-param name="target">
                     <xsl:apply-templates mode="translateURI" select="/core:Parcel/@describes" />
                  </xsl:with-param>
               </xsl:call-template>
            </xsl:variable>
            <xsl:value-of select = "$relpath"/>
            <xsl:variable name="targetFilename">
               <xsl:apply-templates mode="getFilename" select="." />
            </xsl:variable>
            <xsl:if test="$relpath!='' or $targetFilename!=$filename">
               <xsl:apply-templates mode="getFilename" select="." />
            </xsl:if>
            <xsl:text>#</xsl:text>
            <xsl:value-of select = "@itemName"/>
   
         </xsl:attribute>
         <xsl:choose>
         	<xsl:when test="$text=''">
         	   <xsl:apply-templates select = "." mode="getDisplayName" />
         	</xsl:when>
         	<xsl:otherwise>
         	   <xsl:value-of select="$text"/>
         	</xsl:otherwise>
         </xsl:choose>
      </a>
   </xsl:template>

<!-- Create an HTML anchor tag with appropriate name for this item. -->
   <xsl:template match="*" mode="getNameAnchor">
      <a>
         <xsl:attribute name="name">
            <xsl:apply-templates select="." mode="getHrefName" />
         </xsl:attribute>
         <xsl:apply-templates select="." mode="getDisplayName"/>
      </a>
   </xsl:template>

<!-- Dereference the given itemref and create an href to the resulting item-->
   <xsl:template match="*" mode="derefHref">
      <xsl:variable name="ref">
         <xsl:apply-templates select="@itemref" mode="quickRef" />
      </xsl:variable>
      <xsl:variable name="relpath">
         <xsl:apply-templates select="@itemref" mode="quickRelpath" />
      </xsl:variable>
      <xsl:choose>
         <xsl:when test="$relpath=''">
            <xsl:apply-templates select="/core:Parcel/*[@itemName=$ref]" mode="getHrefAnchor"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:variable name="otherdoc" select="document(concat($relpath, $constants.parcelFileName), /)" />
            <xsl:apply-templates select="$otherdoc/core:Parcel/*[@itemName=$ref]" mode="getHrefAnchor"/>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>

<!-- Dereference the given item's child matching the child paramater
     and create an href to the resulting item-->
   <xsl:template match="*" mode="derefChildHref">
      <xsl:param name="child"/>
      <xsl:apply-templates select="./*[local-name()=$child]" mode="derefHref" />
   </xsl:template>

<!-- Dereference the given itemref, look at the child matching the child paramater,
     dereference that itemref, then create an href to the resulting item-->
   <xsl:template match="@itemref" mode="doubleDerefHref">
      <xsl:param name="child"/>
      <xsl:variable name="ref">
         <xsl:apply-templates select="." mode="quickRef" />
      </xsl:variable>
      <xsl:variable name="relpath">
         <xsl:apply-templates select="." mode="quickRelpath" />
      </xsl:variable>
      <xsl:choose>
         <xsl:when test="$relpath=''">
            <xsl:apply-templates select="/core:Parcel/*[@itemName=$ref]" mode="derefChildHref">
               <xsl:with-param name="child" select="$child"/>
            </xsl:apply-templates>
         </xsl:when>
         <xsl:otherwise>
            <xsl:variable name="otherdoc" select="document(concat($relpath, $constants.parcelFileName), /)" />
            <xsl:apply-templates select="$otherdoc/core:Parcel/*[@itemName=$ref]" mode="derefChildHref">
               <xsl:with-param name="child" select="$child"/>
            </xsl:apply-templates>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   
</xsl:stylesheet>