
JDK_VERSION=7-ea-j2sdk-b21
JRE_VERSION=7-ea-j2re-b21
ANT_VERSION=1.7.0
RELVER=$(JRE_VERSION)-$(BRANCH_REV_PREFIX)2
OPENJDK=$(BUILD_ROOT)/openjdk
JDK=$(OPENJDK)/j2sdk-image
JRE=$(OPENJDK)/j2re-image
SRC=$(OPENJDK)/none

include $(BUILD_ROOT)/Makefile.inc

TARBALL=openjdk-$(RELVER).tar.gz

openjdk-$(JDK_VERSION)-$(OS).tar.bz2:
	$(CURL) http://builds.osafoundation.org/external/$@

openjdk-$(JRE_VERSION)-$(OS).tar.bz2:
	$(CURL) http://builds.osafoundation.org/external/$@

apache-ant-$(ANT_VERSION)-bin.tar.bz2:
	$(CURL) http://builds.osafoundation.org/external/$@

# we're using pre-built openjdk and ant binaries as "sources" at the moment
sources: openjdk-$(JDK_VERSION)-$(OS).tar.bz2 \
         openjdk-$(JRE_VERSION)-$(OS).tar.bz2 \
         apache-ant-$(ANT_VERSION)-bin.tar.bz2

openjdk-$(JDK_VERSION)-expanded: openjdk-$(JDK_VERSION)-$(OS).tar.bz2
	tar -xvjf $<
	touch $@

openjdk-$(JRE_VERSION)-expanded: openjdk-$(JRE_VERSION)-$(OS).tar.bz2
	tar -xvjf $<
	touch $@

ant-$(ANT_VERSION)-expanded: apache-ant-$(ANT_VERSION)-bin.tar.bz2
	tar xvjf $<
	touch $@

expand: openjdk-$(JDK_VERSION)-expanded \
        openjdk-$(JRE_VERSION)-expanded \
        ant-$(ANT_VERSION)-expanded

rt.jar: j2sdk-image/jre/lib/rt.jar
	rm -rf rt; mkdir rt
	cp -p $< $@
	cd rt; ../j2sdk-image/bin/jar -xf ../rt.jar
	rm rt.jar
	rm -rf rt/com/sun/corba
	rm -rf rt/com/sun/java/swing
	rm -rf rt/com/sun/imageio
	rm -rf rt/com/sun/jmx
	rm -rf rt/com/sun/media
	rm -rf rt/com/sun/org
	rm -rf rt/com/sun/swing
	rm -rf rt/com/sun/xml
	rm -rf rt/java/applet
	rm -rf rt/java/sql
	rm -rf rt/javax
	rm -rf rt/java/awt
	rm -rf rt/org
	rm -rf rt/sun/awt
	rm -rf rt/sun/applet
	rm -rf rt/sun/font
	rm -rf rt/sun/java2d
	rm -rf rt/sun/print
	rm -rf rt/sun/swing
	cd rt; ../j2sdk-image/bin/jar -cf ../rt.jar .

$(TARBALL): rt.jar openjdk-$(JRE_VERSION)-expanded
	cp -p $< j2re-image/lib/rt.jar
ifeq ($(OS),Cygwin)
	find j2re-image -name '*.pdb' | xargs rm -f
	find j2re-image -name '*.map' | xargs rm -f
endif
	rm -rf j2re-image/man
	rm -rf j2re-image/lib/audio
	rm -rf j2re-image/lib/i386/server
ifeq ($(OS),Linux)
	rm -rf j2re-image/lib/i386/xawt
	rm -rf j2re-image/lib/i386/libawt.so
	rm -rf j2re-image/lib/i386/libjawt.so
	rm -rf j2re-image/lib/i386/libmlib_image.so
	rm -rf j2re-image/lib/i386/libmsound*.so
	rm -rf j2re-image/lib/i386/libfontmanager.so
endif
	tar -cvzf $@ j2re-image 

binaries: $(TARBALL)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

default: expand
all: expand

clean:
	rm -rf rt.jar rt
	rm -rf j2re-image openjdk-$(JRE_VERSION)-expanded

_realclean::
	rm -rf j2re* j2sdk* apache-ant* openjdk*.tar.gz *expanded
