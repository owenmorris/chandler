
# This Makefile requires cygwin on Windows
# It should *not* be made to depend on external/internal
# When a version changes, the ARCHIVES lists below needs to be updated.
#

# these get installed into release or debug
BIN_ARCHIVES=../$(SNAP)-0.3-15.tar.gz \
             ../wxPython-$(SNAP)-2.5-4.tar.gz \
             ../UUIDext-$(SNAP)-0.3-2.tar.gz \
             ../m2crypto-$(SNAP)-0.12-1.tar.gz \
             ../Launchers-$(SNAP)-0.3-7.tar.gz

# these get installed into chandler
HOME_ARCHIVES=../QueryParser-$(SNAP)-0.1-4.tar.gz

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


OS=$(shell uname)

ifeq ($(findstring CYGWIN,$(OS)),CYGWIN)
OS=Cygwin
endif

ifeq ($(findstring WINNT,$(OS)),WINNT)
OS=Cygwin
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
	$(CURL) $(@:=.md5) $(URL)/$(notdir $(@:=.md5))

#	(cd ..; $(MD5CHECK) $(notdir $(@:=.md5)))

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
