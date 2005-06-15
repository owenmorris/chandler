
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

# When a version changes, the ARCHIVES lists below needs to be updated.

# these get installed into release or debug
ARCHIVES=$(CHANDLERARCHIVES)/Launchers-$(SNAP)-0.5-1.tar.gz \
         $(CHANDLERARCHIVES)/chandlerdb-$(SNAP)-0.5-9.tar.gz \
         $(CHANDLERARCHIVES)/db-$(SNAP)-4.3.28-1.tar.gz \
         $(CHANDLERARCHIVES)/epydoc-$(SNAP)-2.1-3.tar.gz \
         $(CHANDLERARCHIVES)/icu-$(SNAP)-3.2-1.tar.gz \
         $(CHANDLERARCHIVES)/jabberpy-$(SNAP)-0.4-0-3.tar.gz \
         $(CHANDLERARCHIVES)/libxml2-$(SNAP)-2.6.16-4.tar.gz \
         $(CHANDLERARCHIVES)/m2crypto-$(SNAP)-282-1.tar.gz \
         $(CHANDLERARCHIVES)/pychecker-$(SNAP)-0.8.13-3.tar.gz \
         $(CHANDLERARCHIVES)/pyicu-$(SNAP)-0.2-1.tar.gz \
         $(CHANDLERARCHIVES)/pylucene-$(SNAP)-0.9.9-192-3.tar.gz \
         $(CHANDLERARCHIVES)/python-$(SNAP)-2.4.1-2.tar.gz \
         $(CHANDLERARCHIVES)/soappy-$(SNAP)-0.10.2-3.tar.gz \
         $(CHANDLERARCHIVES)/twisted-$(SNAP)-r13651-8.tar.gz \
         $(CHANDLERARCHIVES)/wxPython-$(SNAP)-2.6.0.0-12.tar.gz \
         $(CHANDLERARCHIVES)/yapps-$(SNAP)-2.1.1-3.tar.gz \
         $(CHANDLERARCHIVES)/zopeinterface-$(SNAP)-3.0.1-2.tar.gz \
         $(CHANDLERARCHIVES)/dateutil-$(SNAP)-0.5-2.tar.gz \
         $(CHANDLERARCHIVES)/vobject-$(SNAP)-0.1.2-2.tar.gz \
         $(CHANDLERARCHIVES)/zanshin-$(SNAP)-46-1.tar.gz \
         $(CHANDLERARCHIVES)/QueryParser-$(SNAP)-0.4-4.tar.gz

# OpenSSL gets bundled into M2Crypto on Windows
ifneq ($(OS),Cygwin)
ARCHIVES += $(CHANDLERARCHIVES)/openssl-$(SNAP)-0.9.7g-1.tar.gz
endif

# readline is only needed for OSX
ifeq ($(OS),Darwin)
ARCHIVES += $(CHANDLERARCHIVES)/readline-$(SNAP)-5.0-1.tar.gz
endif

ARCHIVES_MD5 = $(addsuffix .md5,$(ARCHIVES))


# We download some pretty big files, which can clog your network. You can now
# control the download options (well, any options) for curl. For example:
#   CHANDLER_CURL_OPTIONS="--limit-rate 200K"
#
# You can also replace curl with something else, for example wget:
#   CURL="wget -r -P .. -nd"

ifeq ($(CURL),)
CURL=curl $(CHANDLER_CURL_OPTIONS) -o
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
MD5=md5
MD5CHECK=$(MD5) --check
else
ifeq ($(OS),Cygwin)
PLATFORM=windows
SITE=bin/Lib/site-packages
MD5=md5sum.exe
MD5CHECK=$(MD5) -c
else
PLATFORM=linux
SITE=lib/python2.3/site-packages
MD5=md5sum
MD5CHECK=$(MD5) -c
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

HOST=builds.osafoundation.org
URL=http://$(HOST)/external/$(PLATFORM)

ARCHIVES_INST = \
    $(addsuffix .inst, \
                $(addprefix $(CHANDLERBIN)/$(SNAP)/, \
                            $(notdir $(ARCHIVES))))

.PHONY: default install clean realclean downloads

default: install

downloads: $(ARCHIVES)

$(ARCHIVES): 
	mkdir -p $(CHANDLERARCHIVES)
	$(CURL) $@ $(URL)/$(notdir $@)
	$(CURL) $@.md5 $(URL)/$(notdir $@.md5)

#	cd $(CHANDLERARCHIVES); $(MD5CHECK) $(notdir $@.md5)

$(ARCHIVES_INST):
	tar -C $(CHANDLERBIN) -xvzf $(CHANDLERARCHIVES)/$(notdir $(basename $@))
	touch $@

checkout:
	cd ..; \
	rm -f cvsco.log;\
	cvs co chandler-python 2>&1 | tee -a cvsco.log; \
	@echo 'Do |grep "^C " ../cvsco.log| to check for potential conflicts'

install: $(ARCHIVES) $(ARCHIVES_INST)


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
STRIP_OPTIONS=-S
else
STRIP_OPTIONS=
endif
strip:
	find $(CHANDLERBIN)/release -name "*.so" |xargs strip $(STRIP_OPTIONS)
endif
endif

clean:
	rm -rf $(CHANDLERBIN)/$(SNAP) __repository__
	rm -f chandler.log randpool.dat

realclean: clean
	rm -rf $(CHANDLERBIN)/debug $(CHANDLERBIN)/release
	rm -f $(ARCHIVES) $(ARCHIVES_INST)
	rm -f $(ARCHIVES_MD5)
