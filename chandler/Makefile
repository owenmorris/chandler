
# This Makefile requires cygwin on Windows
# It should *not* be made to depend on external/internal

ARCHIVES=../$(SNAP)-0.3-3.tar.gz \
         ../wxPython-$(SNAP)-2.5-2.tar.gz \
         ../PyLucene-$(SNAP)-0.3-1.tar.gz \
         ../UUIDext-$(SNAP)-0.3-1.tar.gz

OS=$(shell uname)

ifeq ($(findstring CYGWIN,$(OS)),CYGWIN)
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

.PHONY: install

default: install

downloads: $(ARCHIVES)

$(ARCHIVES):
	curl -o $@ $(URL)/$(notdir $@)

install: $(ARCHIVES)
	@for archive in $(ARCHIVES); \
	do \
            echo tar -C .. -xvzf $$archive; \
            tar -C .. -xvzf $$archive; \
	done
