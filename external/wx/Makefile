
VERSION=2.7.0.0
SVN_REVISION=65
RELVER_FLAGS=-r$(SVN_REVISION)-$(BRANCH_REV_PREFIX)1
RELVER=$(VERSION)$(RELVER_FLAGS)
WX=$(BUILD_ROOT)/wx
BUILD=build_$(SNAP)
SRC=wxPython-$(RELVER)
TARBALL=wxPython-$(SNAP)-$(RELVER).tar.gz
SVNROOT=http://svn.osafoundation.org/wx/trunk

include $(BUILD_ROOT)/Makefile.inc

$(SRC).tar.gz: $(SRC)-expanded
	tar czf $(SRC).tar.gz $(SRC)

sources: $(SRC).tar.gz

$(SRC)-expanded:
	svn export $(SVNROOT) -r $(SVN_REVISION) $(SRC)
	touch $@

expand: $(SRC)-expanded

build: expand
	$(MAKE) -C $(SRC) DEBUG=$(DEBUG) RELVER_FLAGS=$(RELVER_FLAGS) RELVER=$(RELVER) build

binaries: strip
	$(MAKE) -C $(SRC) DEBUG=$(DEBUG) RELVER_FLAGS=$(RELVER_FLAGS) RELVER=$(RELVER) snap
	cp $(SRC)/$(TARBALL) $(WX)

install: $(TARBALL)
	$(MAKE) -C $(SRC) DEBUG=$(DEBUG) RELVER_FLAGS=$(RELVER_FLAGS) RELVER=$(RELVER) install

clean:
	$(MAKE) -C $(SRC) DEBUG=$(DEBUG) RELVER_FLAGS=$(RELVER_FLAGS) RELVER=$(RELVER) clean
