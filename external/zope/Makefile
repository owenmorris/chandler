
VERSION=3.0.1
RELVER=$(VERSION)-2
ZOPE=$(BUILD_ROOT)/zope
SRC=$(ZOPE)/ZopeInterface-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION);echo ok

build: expand apply
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

ZopeInterface-$(VERSION).tgz:
	$(CURL) http://builds.o11n.org/external/ZopeInterface-$(VERSION).tgz
	$(CURL) http://builds.o11n.org/external/ZopeInterface-$(VERSION).tgz.md5

sources: ZopeInterface-$(VERSION).tgz

ZopeInterface-$(VERSION)-expanded: ZopeInterface-$(VERSION).tgz
	tar xzvf ZopeInterface-$(VERSION).tgz
	touch ZopeInterface-$(VERSION)-expanded

expand: ZopeInterface-$(VERSION)-expanded

snap: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/zope -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/zope -name "*.pyo" | xargs rm -f; \
	tar -cvzf $(ZOPE)/zopeinterface-$(SNAP)-$(RELVER).tar.gz \
		$(SNAP)/$(SITE)/zope \
		--exclude tests \
		--exclude testing; \
	$(MD5) $(ZOPE)/zopeinterface-$(SNAP)-$(RELVER).tar.gz > $(ZOPE)/zopeinterface-$(SNAP)-$(RELVER).tar.gz.md5

install: zopeinterface-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf zopeinterface-$(SNAP)-$(RELVER).tar.gz

upload: zopeinterface-$(SNAP)-$(RELVER).tar.gz
	scp zopeinterface-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp zopeinterface-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

clean:
	rm -rf  $(SRC)/$(BUILD)

