
# This Makefile requires cygwin on Windows
# It should *not* be made to depend on external/internal
# When a version changes, the ARCHIVES list below needs to be updated.
#
ARCHIVES=../$(SNAP)-0.3-13.tar.gz \
         ../wxPython-$(SNAP)-2.5-4.tar.gz \
         ../UUIDext-$(SNAP)-0.3-2.tar.gz \
         ../m2crypto-$(SNAP)-0.12-1.tar.gz \
         ../QueryParser-$(SNAP)-0.1-1.tar.gz \
         ../Launchers-$(SNAP)-0.3-4.tar.gz

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
else
ifeq ($(OS),Cygwin)
PLATFORM=windows
SITE=bin/Lib/site-packages
else
PLATFORM=linux
SITE=lib/python2.3/site-packages
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
	cp $(SNAP)/$(SITE)/QueryParser.py repository/query/parser/

clean:
	rm -rf $(SNAP); \
	rm -f chandler.log; \
	rm -rf __repository__ ; \
	rm -f randpool.dat
