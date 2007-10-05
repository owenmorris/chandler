
JDK_VERSION=7-ea-j2sdk-b21
JRE_VERSION=7-ea-j2re-b21
ANT_VERSION=1.7.0
RELVER=$(JRE_VERSION)-$(BRANCH_REV_PREFIX)1
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

$(TARBALL):
ifeq ($(OS),Cygwin)
	find j2re-image -name '*.pdb' | xargs rm -f
	find j2re-image -name '*.map' | xargs rm -f
endif
	tar -cvzf $@ j2re-image

binaries: $(TARBALL)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

default: expand
all: expand

_realclean::
	rm -rf j2re* j2sdk* apache-ant* openjdk*.tar.gz *expanded
