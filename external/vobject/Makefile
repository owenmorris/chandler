include ../Makefile.inc

VERSION=0.2.3
SVN_REVISION=116
RELVER=$(VERSION)-r$(SVN_REVISION)-$(BRANCH_REV_PREFIX)1
VOBJECT=$(BUILD_ROOT)/vobject
MANIFEST=$(SNAP)/$(SITE)/vobject
#MANIFEST=$(SNAP)/$(SITE)/vobject-$(VERSION)-py$(PYTHON_VER).egg
BUILD=build_$(SNAP)
SRC=vobject-$(RELVER)

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

binaries: 
	cd $(BUILD_ROOT); \
	tar -C $(BUILD_ROOT) -cvzf $(VOBJECT)/vobject-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)


upload: vobject-$(SNAP)-$(RELVER).tar.gz
	scp vobject-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

install:
	cd $(BUILD_ROOT); \
      tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
