
# This Makefile requires cygwin on Windows
# It should *not* be made to depend on external/internal
# When a version changes, the ARCHIVES list below needs to be updated.
#
ARCHIVES=../$(SNAP)-0.3-10.tar.gz \
         ../wxPython-$(SNAP)-2.5-2.tar.gz \
         ../UUIDext-$(SNAP)-0.3-2.tar.gz \
         ../m2crypto-$(SNAP)-0.12-1.tar.gz \
         ../Launchers-$(SNAP)-0.3-3.tar.gz

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
else
ifeq ($(OS),Cygwin)
PLATFORM=windows
else
PLATFORM=linux
endif
endif

HOST=builds.osafoundation.org
URL=http://$(HOST)/external/$(PLATFORM)

.PHONY: install $(notdir $(ARCHIVES))

default: install

downloads: $(ARCHIVES)

$(ARCHIVES):
	curl -o $@ $(URL)/$(notdir $@)

$(notdir $(ARCHIVES)):
	tar -C ../chandler -xvzf ../$@

checkout:
	cd ..; \
	rm -f cvsco.log;\
	cvs co chandler-python 2>&1 | tee -a cvsco.log; \
	echo 'Do |grep "^C " ../cvsco.log| to check for potential conflicts'

install: $(ARCHIVES) $(notdir $(ARCHIVES))

