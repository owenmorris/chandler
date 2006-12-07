
VERSION=2.7.2.0
SVNVER=127
RELVER_FLAGS=-r$(SVNVER)-$(BRANCH_REV_PREFIX)2
RELVER=$(VERSION)$(RELVER_FLAGS)
WX=$(BUILD_ROOT)/wx
BUILD=build_$(SNAP)
SRC=$(WX)/wxPython-r$(SVNVER)
TARBALL=wxPython-$(SNAP)-$(RELVER).tar.gz
SVNROOT=http://svn.osafoundation.org/wx/trunk

include $(BUILD_ROOT)/Makefile.inc

wxPython-r$(SVNVER).tar.gz:
	if [ ! -d wxPython-r$(SVNVER) ]; then \
            svn export $(SVNROOT) -r $(SVNVER) wxPython-r$(SVNVER); \
        fi
	tar -czf $@ wxPython-r$(SVNVER)
	touch wxPython-r$(SVNVER)-expanded

sources: wxPython-r$(SVNVER).tar.gz

wxPython-r$(SVNVER)-expanded: wxPython-r$(SVNVER).tar.gz
	if [ ! -f $@ ]; then \
            tar -xvzf $<; \
            touch $@; \
        fi

expand: wxPython-r$(SVNVER)-expanded

build: expand
	$(MAKE) -C $(SRC) DEBUG=$(DEBUG) RELVER_FLAGS=$(RELVER_FLAGS) RELVER=$(RELVER) build

binaries: strip
	$(MAKE) -C $(SRC) DEBUG=$(DEBUG) RELVER_FLAGS=$(RELVER_FLAGS) RELVER=$(RELVER) snap
	cp -p $(SRC)/$(TARBALL) $(WX)

install: $(TARBALL)
	$(MAKE) -C $(SRC) DEBUG=$(DEBUG) RELVER_FLAGS=$(RELVER_FLAGS) RELVER=$(RELVER) install

clean:
	$(MAKE) -C $(SRC) DEBUG=$(DEBUG) RELVER_FLAGS=$(RELVER_FLAGS) RELVER=$(RELVER) clean
