
VERSION=0.4.5
SVN_REVISION=172
RELVER=$(VERSION)-r$(SVN_REVISION)-$(BRANCH_REV_PREFIX)1
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

ifeq ($(OS),Cygwin)
build: expand apply
	cd $(SRC); \
    MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
        build --build-base=$(BUILD) $(DIST_OPT) \
        install_lib --force --install-dir=`cygpath -aw $(BUILD_ROOT)/$(SNAP)/$(SITE)`
else
build: expand apply
	cd $(SRC); \
    MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
        build --build-base=$(BUILD) $(DIST_OPT) \
        install_lib --force --install-dir=$(BUILD_ROOT)/$(SNAP)/$(SITE)
endif

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(VOBJECT)/$(TARBALL) \
        --exclude '*.py?' \
        $(MANIFEST)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

test:
	cd $(SRC); \
    MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) tests/tests.py -v

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
