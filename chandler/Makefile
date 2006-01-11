
# Copyright (c) 2005 Open Source Applications Foundation
# License: http://osafoundation.org/Chandler_0.1_license_terms.htm
#
# This Makefile requires cygwin on Windows
# It should *not* be made to depend on external/internal

OS=$(shell uname)

ifeq ($(findstring CYGWIN,$(OS)),CYGWIN)
OS=Cygwin
endif

ifeq ($(findstring WINNT,$(OS)),WINNT)
OS=Cygwin
endif

BP=

# When a version changes, the ARCHIVES lists below needs to be updated.

# these get installed into release or debug
ARCHIVES=$(CHANDLERARCHIVES)/Launchers-$(SNAP)-0.6-$(BP)1.tar.gz \
         $(CHANDLERARCHIVES)/chandlerdb-$(SNAP)-0.6-$(BP)8.tar.gz \
         $(CHANDLERARCHIVES)/db-$(SNAP)-4.4.16-$(BP)2.tar.gz \
         $(CHANDLERARCHIVES)/epydoc-$(SNAP)-2.1-$(BP)6.tar.gz \
         $(CHANDLERARCHIVES)/icu-$(SNAP)-3.4-$(BP)1.tar.gz \
         $(CHANDLERARCHIVES)/jabberpy-$(SNAP)-0.4-0-$(BP)4.tar.gz \
         $(CHANDLERARCHIVES)/libxml2-$(SNAP)-2.6.16-$(BP)5.tar.gz \
         $(CHANDLERARCHIVES)/m2crypto-$(SNAP)-310-$(BP)3.tar.gz \
         $(CHANDLERARCHIVES)/pychecker-$(SNAP)-0.8.13-$(BP)4.tar.gz \
         $(CHANDLERARCHIVES)/PyICU-$(SNAP)-0.4-49-$(BP)1.tar.gz \
         $(CHANDLERARCHIVES)/PyLucene-$(SNAP)-1.9rc1-7-$(BP)1.tar.gz \
         $(CHANDLERARCHIVES)/python-$(SNAP)-2.4.2-$(BP)4.tar.gz \
         $(CHANDLERARCHIVES)/soappy-$(SNAP)-0.10.2-$(BP)4.tar.gz \
         $(CHANDLERARCHIVES)/twisted-$(SNAP)-r15399-$(BP)1.tar.gz \
         $(CHANDLERARCHIVES)/wxPython-$(SNAP)-2.6.2.0-$(BP)30.tar.gz \
         $(CHANDLERARCHIVES)/zopeinterface-$(SNAP)-3.1.0c1-$(BP)1.tar.gz \
         $(CHANDLERARCHIVES)/dateutil-$(SNAP)-1.1-$(BP)1.tar.gz \
         $(CHANDLERARCHIVES)/vobject-$(SNAP)-0.2.2-$(BP)2.tar.gz \
         $(CHANDLERARCHIVES)/zanshin-$(SNAP)-131-$(BP)2.tar.gz \
         $(CHANDLERARCHIVES)/optik-$(SNAP)-1.5-$(BP)2.tar.gz \
         $(CHANDLERARCHIVES)/common-$(SNAP)-0.12.0-$(BP)2.tar.gz \
         $(CHANDLERARCHIVES)/pylint-$(SNAP)-0.7.0-$(BP)2.tar.gz


# OpenSSL gets bundled into M2Crypto on Windows
ifneq ($(OS),Cygwin)
ARCHIVES += $(CHANDLERARCHIVES)/openssl-$(SNAP)-0.9.7i-$(BP)1.tar.gz
endif

# readline is only needed for OSX
ifeq ($(OS),Darwin)
ARCHIVES += $(CHANDLERARCHIVES)/readline-$(SNAP)-5.0-$(BP)1.tar.gz
endif

# We download some pretty big files, which can clog your network. You can now
# control the download options (well, any options) for curl. For example:
#   CHANDLER_CURL_OPTIONS="--limit-rate 200K"
#
# You can also replace curl with something else, for example wget:
#   CURL="wget -r -P .. -nd"

ifeq ($(CURL),)
CURL=curl $(CHANDLER_CURL_OPTIONS) -f -o
endif

ifeq ($(DEBUG),1)
SNAP=debug
else
SNAP=release
endif

ifeq ($(OS),Darwin)
PLATFORM=macosx
FRAMEWORK=Library/Frameworks/Python.framework/Versions/2.3
SITE=$(FRAMEWORK)/lib/python2.3/site-packages
else
ifeq ($(OS),Cygwin)
PLATFORM=windows
SITE=bin/Lib/site-packages
else
PLATFORM=linux
SITE=lib/python2.3/site-packages
endif
endif

ifeq ($(CHANDLERHOME),)
CHANDLERHOME=.
endif

ifeq ($(CHANDLERBIN),)
CHANDLERBIN=$(CHANDLERHOME)
endif               

ifeq ($(CHANDLERARCHIVES),)
CHANDLERARCHIVES=../downloads
endif

ifeq ($(OS),Cygwin)
CHANDLERBIN:=$(shell cygpath -au $(CHANDLERBIN))
CHANDLERHOME:=$(shell cygpath -au $(CHANDLERHOME))
CHANDLERARCHIVES:=$(shell cygpath -au $(CHANDLERARCHIVES))
endif

HOST=builds.osafoundation.org
URL=http://$(HOST)/external/$(PLATFORM)

ARCHIVES_INST = \
    $(addsuffix .inst, \
                $(addprefix $(CHANDLERBIN)/$(SNAP)/, \
                            $(notdir $(ARCHIVES))))

.PHONY: default install clean realclean downloads

default: install

downloads: $(ARCHIVES)

$(CHANDLERARCHIVES):
	mkdir -p $(CHANDLERARCHIVES)

$(ARCHIVES): $(CHANDLERARCHIVES)
	$(CURL) $@ $(URL)/$(notdir $@)

$(ARCHIVES_INST):
	tar -C $(CHANDLERBIN) -xvzf $(CHANDLERARCHIVES)/$(notdir $(basename $@))
	touch $@

ifeq ($(OS),Cygwin)
manifest_exe:
	if [ -f "$(CHANDLERBIN)/$(SNAP)/bin/chandler.exe.manifest" ]; \
	then \
	    chmod +x $(CHANDLERBIN)/$(SNAP)/bin/chandler.exe.manifest; \
	fi
else
manifest_exe:
endif

install: $(ARCHIVES) $(ARCHIVES_INST) manifest_exe

download: $(ARCHIVES)

# to install individual binaries, for example: make chandlerdb

$(notdir $(shell echo $(ARCHIVES) | sed "s/-$(SNAP)[^ ]*//g")):
	$(MAKE) $(shell echo $(ARCHIVES) | sed "s=.*\($(CHANDLERARCHIVES)/$@-[^ ]*\).*=\1=")
	$(MAKE) $(shell echo $(ARCHIVES_INST) | sed "s=.*\($(CHANDLERBIN)/$(SNAP)/$@-[^ ]*\).*=\1=")

ifeq ($(OS),Cygwin)
strip:
else
ifeq ($(DEBUG),1)
strip:
else
ifeq ($(OS),Darwin)
  # we could use -x as an option to strip but it needs testing to
  # see if it gives any performance gains
STRIP_OPTIONS=-S
STRIP_OP=\( -name '*.dylib' -o -name '*.so' \)
else
STRIP_OPTIONS=
STRIP_OP=-name '*.so'
endif
strip:
	find $(CHANDLERBIN)/release $(STRIP_OP) | xargs chmod +w
	find $(CHANDLERBIN)/release $(STRIP_OP) | xargs strip $(STRIP_OPTIONS)
endif
endif

purge:
	python $(CHANDLERHOME)/tools/purge.py $(CHANDLERHOME)

tests:
	$(CHANDLERHOME)/tools/do_tests.sh $(CHANDLERHOME)

clean: purge
	rm -rf $(CHANDLERBIN)/$(SNAP) __repository__
	rm -f chandler.log randpool.dat
	find . -name '*.pyc' | xargs rm -f
	find . -name '*.pyo' | xargs rm -f

realclean: clean
	rm -rf $(CHANDLERBIN)/debug $(CHANDLERBIN)/release
	rm -f $(ARCHIVES) $(ARCHIVES_INST)
