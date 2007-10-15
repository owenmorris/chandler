
VERSION=1.0
SVN_REVISION=10
RELVER=$(VERSION)-r$(SVN_REVISION)-$(BRANCH_REV_PREFIX)1
EGGTRANSLATIONS=$(BUILD_ROOT)/eggtranslations
BUILD=build_$(SNAP)
EGG=EggTranslations-$(subst -,_,$(VERSION))-py$(PYTHON_VER).egg
TARBALL=eggtranslations-$(SNAP)-$(RELVER).tar.gz
SRC=eggtranslations-$(RELVER)

include $(BUILD_ROOT)/Makefile.inc

build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
            $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                               install --force

$(SRC).tar.gz:
	svn export http://svn.osafoundation.org/eggtranslations/trunk -r $(SVN_REVISION) $(SRC)
	tar -czf $(SRC).tar.gz $(SRC)

sources: $(SRC).tar.gz

eggtranslations-$(VERSION)-expanded: $(SRC).tar.gz
	tar -xvzf $(SRC).tar.gz
	touch eggtranslations-$(VERSION)-expanded

expand: eggtranslations-$(VERSION)-expanded

binaries: build
	echo "./$(EGG)" > $(BUILD_ROOT)/$(SNAP)/$(SITE)/EggTranslations.pth
	tar -C $(BUILD_ROOT) -cvzf $(EGGTRANSLATIONS)/$(TARBALL) \
                             $(SNAP)/$(SITE)/$(EGG) \
                             $(SNAP)/$(SITE)/EggTranslations.pth

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
