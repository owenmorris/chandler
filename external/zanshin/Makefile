
VERSION=150
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)3

ZANSHIN=$(BUILD_ROOT)/zanshin
SRC=$(ZANSHIN)/zanshin-$(VERSION)
BUILD=build_$(SNAP)
TARBALL=zanshin-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

build: expand
	cd $(SRC); \
      MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install_lib --force

zanshin-$(VERSION).tar.gz:
	svn export http://svn.osafoundation.org/zanshin/trunk -r $(VERSION) zanshin-$(VERSION)
	tar czf zanshin-$(VERSION).tar.gz zanshin-$(VERSION)

sources: zanshin-$(VERSION).tar.gz

zanshin-$(VERSION)-expanded: zanshin-$(VERSION).tar.gz
	touch zanshin-$(VERSION)-expanded

expand: zanshin-$(VERSION)-expanded

binaries: strip
	cd $(BUILD_ROOT); \
      find $(SNAP)/$(SITE)/zanshin -name "*.pyc" | xargs rm -f; \
      find $(SNAP)/$(SITE)/zanshin -name "*.pyo" | xargs rm -f; \
      tar -cvzf $(ZANSHIN)/$(TARBALL) \
          --exclude test \
          $(SNAP)/$(SITE)/zanshin

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
