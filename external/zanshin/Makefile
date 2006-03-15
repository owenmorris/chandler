
VERSION=141
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1

ZANSHIN=$(BUILD_ROOT)/zanshin
SRC=$(ZANSHIN)/zanshin-$(VERSION)
TARBALL=zanshin-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

build: expand
	cd $(SRC); \
      MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install --force

zanshin-$(VERSION).tar.gz:
	svn export http://svn.osafoundation.org/zanshin/trunk -r $(VERSION) zanshin-$(VERSION)
	tar czf zanshin-$(VERSION).tar.gz zanshin-$(VERSION)

sources: zanshin-$(VERSION).tar.gz

zanshin-$(VERSION)-expanded: zanshin-$(VERSION).tar.gz
	touch zanshin-$(VERSION)-expanded

expand: zanshin-$(VERSION)-expanded

binaries: 
	cd $(BUILD_ROOT); \
      find $(SNAP)/$(SITE)/zanshin -name "*.pyc" | xargs rm -f; \
      find $(SNAP)/$(SITE)/zanshin -name "*.pyo" | xargs rm -f; \
      tar -cvzf $(ZANSHIN)/$(TARBALL) \
          --exclude tests \
          $(SNAP)/$(SITE)/zanshin

install: $(TARBALL)
	cp $(TARBALL) $(CHANDLERARCHIVES)

upload: $(TARBALL)
	scp $(TARBALL) $(UPLOAD)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
