
VERSION=3.1.0c1
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)4
ZOPE=$(BUILD_ROOT)/zope
SRC=$(ZOPE)/ZopeInterface-$(VERSION)
BUILD=build_$(SNAP)
TARBALL=zopeinterface-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

.PHONY: patches-$(VERSION)

apply: patches-$(VERSION)
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION);echo ok; \
        fi

build: expand apply
	cd $(SRC); \
      MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install --force

ZopeInterface-$(VERSION).tgz:
	$(CURL) http://builds.osafoundation.org/external/ZopeInterface-$(VERSION).tgz

sources: ZopeInterface-$(VERSION).tgz

ZopeInterface-$(VERSION)-expanded: ZopeInterface-$(VERSION).tgz
	tar xzvf ZopeInterface-$(VERSION).tgz
	touch ZopeInterface-$(VERSION)-expanded

expand: ZopeInterface-$(VERSION)-expanded

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(ZOPE)/$(TARBALL) \
        --exclude tests --exclude testing --exclude '*.py?' \
        $(SNAP)/$(SITE)/zope

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
