
VERSION=55
RELVER=$(VERSION)-1

ZANSHIN=$(BUILD_ROOT)/zanshin
SRC=$(ZANSHIN)/zanshin-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

zanshin-$(VERSION).tar.gz:
	svn export http://svn.osafoundation.org/zanshin/trunk -r $(VERSION) zanshin-$(VERSION)
	tar czf zanshin-$(VERSION).tar.gz zanshin-$(VERSION)

sources: zanshin-$(VERSION).tar.gz

zanshin-$(VERSION)-expanded: zanshin-$(VERSION).tar.gz
	touch zanshin-$(VERSION)-expanded

expand: zanshin-$(VERSION)-expanded

snap: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/zanshin -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/zanshin -name "*.pyo" | xargs rm -f; \
	tar -cvzf $(ZANSHIN)/zanshin-$(SNAP)-$(RELVER).tar.gz \
		$(SNAP)/$(SITE)/zanshin \
		--exclude tests; \
	$(MD5) $(ZANSHIN)/zanshin-$(SNAP)-$(RELVER).tar.gz > $(ZANSHIN)/zanshin-$(SNAP)-$(RELVER).tar.gz.md5

install: zanshin-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf zanshin-$(SNAP)-$(RELVER).tar.gz

upload: zanshin-$(SNAP)-$(RELVER).tar.gz
	scp zanshin-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp zanshin-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

clean:
	rm -rf  $(SRC)/$(BUILD)

