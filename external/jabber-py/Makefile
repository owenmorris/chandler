
VERSION=0.4-0
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)4
JABBERPY=$(BUILD_ROOT)/jabber-py
SRC=$(JABBERPY)/jabberpy$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


apply: patches
	patch -Nup0 < patches; echo ok

build: expand apply
	cd $(SRC); \
      MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build           --build-base=$(BUILD) $(DIST_OPT) \
          install --force

jabberpy$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/jabberpy$(VERSION).tar.gz

sources: jabberpy$(VERSION).tar.gz

jabberpy$(VERSION)-expanded: jabberpy$(VERSION).tar.gz
	tar xvzf jabberpy$(VERSION).tar.gz
	touch jabberpy$(VERSION)-expanded

expand: jabberpy$(VERSION)-expanded

binaries: 
	cd $(BUILD_ROOT); \
      tar -cvzf $(JABBERPY)/jabberpy-$(SNAP)-$(RELVER).tar.gz \
          $(SNAP)/$(SITE)/jabber.py \
          $(SNAP)/$(SITE)/xmlstream.py

install: jabberpy-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf jabberpy-$(SNAP)-$(RELVER).tar.gz

upload: jabberpy-$(SNAP)-$(RELVER).tar.gz
	scp jabberpy-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
