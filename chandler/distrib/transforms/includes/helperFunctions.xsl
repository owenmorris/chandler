<xsl:stylesheet version="1.0"
     xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
     xmlns:core="//Schema/Core"
     xmlns:exsl="http://exslt.org/common"
     xmlns:func="http://exslt.org/functions"
     extension-element-prefixes="exsl func">

   <xsl:variable name = "root" select = "/" />
   <xsl:variable name = "empty">
      <empty/>
   </xsl:variable>


<xsl:template match="a">
              <xsl:call-template name="createRelativePath">
                 <xsl:with-param name="src" select="b/@a"/>
                 <xsl:with-param name="target" select="c/@a"/>
              </xsl:call-template>           
</xsl:template>

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
           <xsl:when test = "$src='' or $target=''">
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
           <xsl:when test = "$src='/' or $target='/'">
              <xsl:call-template name="createRelativePath">
                 <xsl:with-param name="src" select="substring-after($src, '/')"/>
                 <xsl:with-param name="target" select="substring-after($target, '/')"/>
              </xsl:call-template>           
           </xsl:when>
           <xsl:when test = "substring-after($src, '/')='' or substring-after($target, '/')=''">
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
                 <xsl:if test = "substring($target, string-length($target))!='/'">
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
	<xsl:template name="translateURI">
	   <xsl:param name="uri" />
	   <xsl:choose>
	   	<xsl:when test="string($uri)=$constants.coreURI">
	   	   <xsl:value-of select="$constants.corePath" />
	   	</xsl:when>
	     
	   	<xsl:otherwise>
	   	   <xsl:value-of select="string($uri)" />
	   	</xsl:otherwise>
	   </xsl:choose>
	</xsl:template>

<!-- Map QNames to their associated URI, except when the URI is for core.
     Note that prefix may be an empty string
-->
	<xsl:template match="@itemref" mode="getURIFromQName">
	   <xsl:variable name="prefix" select="substring-before(.,':')"/>
	   <xsl:variable name="uri" select="../namespace::*[local-name()=$prefix]"/>
	   <xsl:call-template name="translateURI">
	      <xsl:with-param name="uri" select="$uri"/>
	   </xsl:call-template>
	</xsl:template>

	
<!-- quickRelPath takes a attribute whose value is a reference and creates
     a relative path to it, assuming that the current documents URI is
     accurately described by /core:Parcel/@describes
-->
   <xsl:template match="@itemref" mode="quickRelpath">
      <xsl:call-template name="createRelativePath">
         <xsl:with-param name="src" select="$root/core:Parcel/@describes" />

         <xsl:with-param name="target">
            <xsl:apply-templates mode="getURIFromQName" select="." />
         </xsl:with-param>
      </xsl:call-template>
   </xsl:template>
   
<!-- Remove text up to and including a ':', remove everything after a '/' 
     to get the name of the Kind being referred to.
-->
<xsl:template match="@itemref" mode="quickRef">
   <xsl:variable name="full">
      <xsl:choose>
         <xsl:when test="substring-after(., ':')=''">
            <xsl:value-of select="." />
         </xsl:when>

         <xsl:otherwise>
            <xsl:value-of select="substring-after(., ':')" />
         </xsl:otherwise>
      </xsl:choose>
   </xsl:variable>

   <xsl:choose>
      <xsl:when test="substring-before($full, '/')">
         <xsl:value-of select="substring-before($full, '/')" />
      </xsl:when>

      <xsl:otherwise>
         <xsl:value-of select="$full" />
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
            <xsl:variable name="otherdoc" select="document(concat($relpath, $constants.parcelFileName), $root)" />
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

<!-- Dereference the given itemref, look at the child matching the child paramater,
     dereference that itemref, then return the resulting item's displayName-->
   <xsl:template match="@itemref" mode="doubleDerefDisplayName">
      <xsl:param name="child"/>
      <xsl:variable name="ref">
         <xsl:apply-templates select="." mode="quickRef" />
      </xsl:variable>
      <xsl:variable name="relpath">
         <xsl:apply-templates select="." mode="quickRelpath" />
      </xsl:variable>
      <xsl:choose>
         <xsl:when test="$relpath=''">
            <xsl:apply-templates select="/core:Parcel/*[@itemName=$ref]/*[local-name()=$child]/@itemref" mode="derefDisplayName"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:variable name="otherdoc" select="document(concat($relpath, $constants.parcelFileName), $root)" />
            <xsl:apply-templates select="$otherdoc/core:Parcel/*[@itemName=$ref]/*[local-name()=$child]/@itemref" mode="derefDisplayName"/>
         </xsl:otherwise>
      </xsl:choose>
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

<!-- Get the file type.  This is the pluralized local name + .html.-->
   <xsl:template match="*" mode="getFilename">
      <xsl:value-of select="func:pluralize(local-name(.))"/>
      <xsl:text>.html</xsl:text>	
   </xsl:template>
   
<!-- Return the plural of the given word.  Currently just deals with returning Aliases instead
     of Aliass.
-->
<func:function name="func:pluralize">
   <xsl:param name="name" />
   <xsl:choose>
      <xsl:when test="$name='Alias'">
         <func:result select="'Aliases'"/>
      </xsl:when>
      <xsl:otherwise>
         <func:result select="concat($name,'s')"/>	
      </xsl:otherwise>
   </xsl:choose>    
</func:function>


   <xsl:template name="pluralize">
      <xsl:param name="name" />
      <xsl:choose>
      	<xsl:when test="$name='Alias'">
      	   <xsl:value-of select="'Aliases'"/>
      	</xsl:when>
      	<xsl:otherwise>
      	   <xsl:value-of select="concat($name,'s')"/>	
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
                     <xsl:call-template name="translateURI">
                        <xsl:with-param name="uri" select="$root/core:Parcel/@describes"/>
                     </xsl:call-template>
                  </xsl:with-param>
                  <xsl:with-param name="target">
                     <xsl:call-template name="translateURI">
                        <xsl:with-param name="uri" select="/core:Parcel/@describes"/>
                     </xsl:call-template>
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
            <xsl:value-of select="@itemName" />
         </xsl:attribute>
         <xsl:apply-templates select="." mode="getDisplayName"/>
      </a>
   </xsl:template>

<!-- Dereference the given item reference (not the itemref attribute itself)
     and create an href to the resulting item
-->
   <xsl:template match="*" mode="derefHref">
      <xsl:param name="text" />
      <xsl:variable name="ref">
         <xsl:apply-templates select="@itemref" mode="quickRef" />
      </xsl:variable>
      <xsl:variable name="relpath">
         <xsl:apply-templates select="@itemref" mode="quickRelpath" />
      </xsl:variable>
      <xsl:choose>
         <xsl:when test="$relpath=''">
            <xsl:apply-templates select="/core:Parcel/*[@itemName=$ref]" mode="getHrefAnchor">
               <xsl:with-param name="text" select="$text" />
            </xsl:apply-templates>
         </xsl:when>
         <xsl:otherwise>
            <xsl:variable name="otherdoc" select="document(concat($relpath, $constants.parcelFileName), $root)" />
            <xsl:apply-templates select="$otherdoc/core:Parcel/*[@itemName=$ref]" mode="getHrefAnchor">
               <xsl:with-param name="text" select="$text" />
            </xsl:apply-templates>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>

<!-- Remove text up to and including a ':', remove everything after a '/' 
     to get the name of the Kind being referred to.
-->
<func:function name="func:refPrimary">
   <xsl:param name="ref" />
   <xsl:variable name="full">
      <xsl:choose>
         <xsl:when test="substring-after($ref, ':')=''">
            <xsl:value-of select="$ref" />
         </xsl:when>

         <xsl:otherwise>
            <xsl:value-of select="substring-after($ref, ':')" />
         </xsl:otherwise>
      </xsl:choose>
   </xsl:variable>

   <xsl:choose>
      <xsl:when test="substring-before($full, '/')">
         <func:result select="substring-before($full, '/')" />
      </xsl:when>

      <xsl:otherwise>
         <func:result select="$full" />
      </xsl:otherwise>
   </xsl:choose>
</func:function>

<!-- Remove everything before a '/' to get the name of the Local Attribute being referred to. -->
<func:function name="func:refLocalAttribute">
   <xsl:param name="ref" />
   <func:result select="substring-after($ref, '/')" />
</func:function>


<func:function name="func:deref">
   <xsl:param name="itemrefAttribute" />

   <xsl:variable name="kind" select="func:refPrimary($itemrefAttribute)"/>
   <xsl:variable name="local" select="func:refLocalAttribute($itemrefAttribute)"/>

   <xsl:variable name="relpath">
      <xsl:apply-templates select="$itemrefAttribute" mode="quickRelpath" />
   </xsl:variable>
   
   <xsl:variable name="otherdoc" select="document(concat($relpath, $constants.parcelFileName), $root)" />

   <xsl:choose>
      <xsl:when test="$local=''">
         <func:result select="$otherdoc/core:Parcel/*[@itemName=$kind]" />
      </xsl:when>

      <xsl:otherwise>
         <func:result select="$otherdoc/core:Parcel/*[@itemName=$kind]/core:Attribute[@itemName=$local]" />
      </xsl:otherwise>
   </xsl:choose>
</func:function>

<!-- Return the inherited attribute's value, or if it's an itemref,
     dereference that and return the object.  superKinds is a special case, if it doesn't exist,
     return core:Item -->
<func:function name="func:getAttributeValue">
   <xsl:param name="context"/>
   <xsl:param name="attribute"/>
      <xsl:choose>
      	<xsl:when test="$context/*[local-name()=$attribute]">
      	   <xsl:choose>
      	   	<xsl:when test="$context/*[local-name()=$attribute]/@itemref">
      	   	   <func:result select="func:deref($context/*[local-name()=$attribute]/@itemref)" />
      	   	</xsl:when>
      	   	<xsl:otherwise>
               <func:result select="$context/*[local-name()=$attribute]/text()" />
      	   	</xsl:otherwise>
      	   </xsl:choose>
      	</xsl:when>
      	<xsl:when test = "$context/core:attributes/@itemref[func:refLocalAttribute(.)=$attribute]">
           <func:result select="func:getDefaultNode(func:deref($context/core:attributes/@itemref[func:refLocalAttribute(.)=$attribute]))" />
      	</xsl:when>
      	<xsl:when test = "$context/core:attributes/@itemref[func:refPrimary(.)=$attribute]">
           <func:result select="func:getDefaultNode(func:deref($context/core:attributes/@itemref[func:refPrimary(.)=$attribute]))" />
      	</xsl:when>

      	<xsl:when test = "$context/core:superKinds">
      	   <func:result select="func:getAttributeValue(func:deref($context/core:superKinds/@itemref),$attribute)" />
      	</xsl:when>
      	<xsl:when test = "$attribute = 'superKinds'">
      	   <func:result select="$coreDoc//core:Kind[@itemName='Item']"/>
      	</xsl:when>
      	<xsl:when test = "func:hasSuperKind($context)">
      	   <func:result select="func:getAttributeValue($coreDoc//core:Kind[@itemName='Item'],$attribute)" />
      	</xsl:when>
      	<xsl:otherwise>
      	   <func:result select="exsl:node-set($empty)"/>
      	</xsl:otherwise>
      </xsl:choose>
</func:function>

<func:function name="func:hasSuperKind">
   <xsl:param name="context" />

   <xsl:choose>
      <xsl:when test="$context/@itemName='Item'">
         <func:result select="false()" />
      </xsl:when>

      <xsl:otherwise>
         <func:result select="true()" />
      </xsl:otherwise>
   </xsl:choose>
</func:function>

<func:function name="func:getDefaultNode">
   <xsl:param name="context" />

   <xsl:choose>
      <xsl:when test="$context/core:defaultValue">
         <func:result select="$context/core:defaultValue" />
      </xsl:when>

      <xsl:when test="$context/core:superAttribute">
         <func:result select="func:getDefaultNode(func:deref($context/core:superAttribute/@itemref))" />
      </xsl:when>
   </xsl:choose>
</func:function>

<func:function name="func:getAspect">
   <xsl:param name="context" />

   <xsl:param name="attribute" />

   <xsl:choose>
      <xsl:when test="$context/*[local-name()=$attribute]">
         <func:result select="$context/*[local-name()=$attribute]" />
      </xsl:when>

      <xsl:when test="$context/core:superAttribute">
         <func:result select="func:getAspect(func:deref($context/core:superAttribute/@itemref), $attribute)" />
      </xsl:when>

      <xsl:otherwise>
         <func:result select="func:getDefaultNode($coreDoc//core:Kind[@itemName='Attribute']/core:Attribute[@itemName=$attribute])" />
      </xsl:otherwise>
   </xsl:choose>
</func:function>


<!-- 

does inverseAttribute want to point to otherName?

* inherit from Items, not just Kinds (and others?)
* deal with local attribute references, in addition to displaying local attributes, especially in getHrefAnchor etc.

* display "is a subAttribute of" for subAttributes

-->

   
</xsl:stylesheet>