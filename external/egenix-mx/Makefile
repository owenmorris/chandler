
VERSION=2.1.0
RELVER=$(VERSION)-3
EGENIX=$(BUILD_ROOT)/egenix-mx
SRC=$(EGENIX)/egenix-mx-base-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

build: expand apply
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

egenix-mx-base-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/egenix-mx-base-$(VERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/egenix-mx-base-$(VERSION).tar.gz.md5

sources: egenix-mx-base-$(VERSION).tar.gz

egenix-mx-base-$(VERSION)-expanded: egenix-mx-base-$(VERSION).tar.gz
	tar xvzf egenix-mx-base-$(VERSION).tar.gz
	touch egenix-mx-base-$(VERSION)-expanded

expand: egenix-mx-base-$(VERSION)-expanded

snap: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/mx -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/mx -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(EGENIX)/egenix-mx-base-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/mx \
            --exclude Examples; \
	$(MD5) $(EGENIX)/egenix-mx-base-$(SNAP)-$(RELVER).tar.gz > $(EGENIX)/egenix-mx-base-$(SNAP)-$(RELVER).tar.gz.md5

install: egenix-mx-base-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf egenix-mx-base-$(SNAP)-$(RELVER).tar.gz

clean:
	rm -rf $(SRC)/$(BUILD)

upload: egenix-mx-base-$(SNAP)-$(RELVER).tar.gz
	scp egenix-mx-base-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp egenix-mx-base-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)
