
VERSION=2.8.7.1
SVNVER=215
RELVER_FLAGS=-r$(SVNVER)-$(BRANCH_REV_PREFIX)1
RELVER=$(VERSION)$(RELVER_FLAGS)
WX=$(BUILD_ROOT)/wx
BUILD=build_$(SNAP)
SRC=$(WX)/wxPython-r$(SVNVER)
TARBALL=wxPython-$(SNAP)-$(RELVER).tar.gz
SVNROOT=http://svn.osafoundation.org/wx/branches/chandler_1.0

include $(BUILD_ROOT)/Makefile.inc

wxPython-r$(SVNVER).tar.gz:
ifeq ($(WXSVN),)
	if [ ! -d wxPython-r$(SVNVER) ]; then \
            svn export $(SVNROOT) -r $(SVNVER) wxPython-r$(SVNVER); \
        fi
else
	if [ ! -d wxPython-r$(SVNVER) ]; then \
            cd $(WXSVN); svn update -r $(SVNVER); cd $(WX); \
            mkdir wxPython-r$(SVNVER) ; \
            tar -C $(WXSVN) -cf - --exclude .svn . | \
            tar -C wxPython-r$(SVNVER) -xf - ; \
        fi
endif
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
