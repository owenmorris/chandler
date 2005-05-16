
VERSION=0.10.2
RELVER=$(VERSION)-3
SOAPPY=$(BUILD_ROOT)/SOAPpy
SRC=$(SOAPPY)/SOAPpy-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


apply: patches
	patch -Nup0 < patches; echo ok

build: expand apply
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

SOAPpy-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/SOAPpy-$(VERSION).tar.gz
	$(CURL) http://builds.osafoundation.org/external/SOAPpy-$(VERSION).tar.gz.md5

sources: SOAPpy-$(VERSION).tar.gz

SOAPpy-$(VERSION)-expanded: SOAPpy-$(VERSION).tar.gz
	tar xvzf SOAPpy-$(VERSION).tar.gz
	touch SOAPpy-$(VERSION)-expanded

expand: SOAPpy-$(VERSION)-expanded

snap: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/SOAPpy -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/SOAPpy -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(SOAPPY)/soappy-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/SOAPpy; \
	$(MD5) $(SOAPPY)/soappy-$(SNAP)-$(RELVER).tar.gz > $(SOAPPY)/soappy-$(SNAP)-$(RELVER).tar.gz.md5

install: soappy-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf soappy-$(SNAP)-$(RELVER).tar.gz

clean:
	rm -rf $(SRC)/$(BUILD)

upload: soappy-$(SNAP)-$(RELVER).tar.gz
	scp soappy-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp soappy-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)
