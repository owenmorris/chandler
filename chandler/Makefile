
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
BIN_ARCHIVES=../Launchers-$(SNAP)-0.4-9.tar.gz \
             ../chandlerdb-$(SNAP)-0.5-5.tar.gz \
             ../db-$(SNAP)-4.3.27-1.tar.gz \
             ../egenix-mx-base-$(SNAP)-2.1.0-3.tar.gz \
             ../epydoc-$(SNAP)-2.1-2.tar.gz \
             ../jabberpy-$(SNAP)-0.4-0-2.tar.gz \
             ../libxml2-$(SNAP)-2.6.16-3.tar.gz \
             ../m2crypto-$(SNAP)-0.12-9.tar.gz \
             ../pychecker-$(SNAP)-0.8.13-2.tar.gz \
             ../pylucene-$(SNAP)-0.9.8-1.tar.gz \
             ../python-$(SNAP)-2.4-2.tar.gz \
             ../soappy-$(SNAP)-0.10.2-2.tar.gz \
             ../twisted-$(SNAP)-r11303-4.tar.gz \
             ../wxPython-$(SNAP)-2.5.3.1-12.tar.gz \
             ../yapps-$(SNAP)-2.1.1-2.tar.gz \
             ../zopeinterface-$(SNAP)-3.0.0b1-2.tar.gz \
             ../dateutil-$(SNAP)-0.5-1.tar.gz \
             ../vobject-$(SNAP)-0.1.1-1.tar.gz

# OpenSSL gets bundled into M2Crypto on Windows
ifneq ($(OS),Cygwin)
BIN_ARCHIVES += ../openssl-$(SNAP)-0.9.7d-1.tar.gz
endif

# these get installed into chandler
HOME_ARCHIVES=../QueryParser-$(SNAP)-0.4-3.tar.gz

ARCHIVES = $(BIN_ARCHIVES) $(HOME_ARCHIVES)
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

HOST=builds.osafoundation.org
URL=http://$(HOST)/external/$(PLATFORM)

BIN_ARCHIVES_INST = \
    $(addsuffix .inst, \
                $(addprefix $(CHANDLERBIN)/$(SNAP)/, \
                            $(notdir $(BIN_ARCHIVES))))

HOME_ARCHIVES_INST = \
    $(addsuffix .inst, \
                $(addprefix $(CHANDLERHOME)/, \
                            $(notdir $(HOME_ARCHIVES))))

.PHONY: default install clean realclean downloads

default: install

downloads: $(ARCHIVES)

$(ARCHIVES):
	$(CURL) $@ $(URL)/$(notdir $@)
	$(CURL) $@.md5 $(URL)/$(notdir $@.md5)

#	cd ..; $(MD5CHECK) $(notdir $@.md5)

$(BIN_ARCHIVES_INST):
	tar -C $(CHANDLERBIN) -xvzf ../$(notdir $(basename $@))
	touch $@

$(HOME_ARCHIVES_INST):
	tar -C $(CHANDLERHOME) -xvzf ../$(notdir $(basename $@))
	touch $@

checkout:
	cd ..; \
	rm -f cvsco.log;\
	cvs co chandler-python 2>&1 | tee -a cvsco.log; \
	@echo 'Do |grep "^C " ../cvsco.log| to check for potential conflicts'

install: $(ARCHIVES) $(BIN_ARCHIVES_INST) $(HOME_ARCHIVES_INST)

clean:
	rm -rf $(CHANDLERBIN)/$(SNAP) __repository__
	rm -f chandler.log randpool.dat

realclean: clean
	rm -rf $(CHANDLERBIN)/debug $(CHANDLERBIN)/release
	rm -f $(ARCHIVES) $(BIN_ARCHIVES_INST) $(HOME_ARCHIVES_INST)
	rm -f $(ARCHIVES_MD5)
