
VERSION=0.3.0
SVN_REVISION=139
RELVER=$(VERSION)-r$(SVN_REVISION)-$(BRANCH_REV_PREFIX)5
VOBJECT=$(BUILD_ROOT)/vobject
BUILD=build_$(SNAP)
SRC=vobject-$(RELVER)
TARBALL=vobject-$(SNAP)-$(RELVER).tar.gz

MANIFEST=$(SNAP)/$(SITE)/vobject
#MANIFEST=$(SNAP)/$(SITE)/vobject-$(VERSION)-py$(PYTHON_VER).egg

include ../Makefile.inc

.PHONY: patches-$(VERSION)

$(SRC).tar.gz:
	svn export http://svn.osafoundation.org/vobject/trunk -r $(SVN_REVISION) $(SRC)
	tar czf $(SRC).tar.gz $(SRC)

sources: $(SRC).tar.gz

$(SRC)-expanded: $(SRC).tar.gz
	touch $(SRC)-expanded

expand: $(SRC)-expanded

apply: patches-$(VERSION)
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION);echo ok; \
        fi

build: expand apply
	cd $(SRC); \
    MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
        build --build-base=$(BUILD) $(DIST_OPT) \
        install --force

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(VOBJECT)/$(TARBALL) $(MANIFEST)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
