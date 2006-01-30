
VERSION=r15399
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
TWISTED=$(BUILD_ROOT)/twisted
SRC=$(TWISTED)/Twisted-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

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

Twisted-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/Twisted-$(VERSION).tar.gz

sources: Twisted-$(VERSION).tar.gz

Twisted-$(VERSION)-expanded: Twisted-$(VERSION).tar.gz
	tar xvzf Twisted-$(VERSION).tar.gz
	touch Twisted-$(VERSION)-expanded

expand: Twisted-$(VERSION)-expanded

binaries: 
	cd $(BUILD_ROOT); \
      find $(SNAP)/$(SITE)/twisted -name "*.pyc" | xargs rm -f; \
      find $(SNAP)/$(SITE)/twisted -name "*.pyo" | xargs rm -f; \
      tar -cvzf $(TWISTED)/twisted-$(SNAP)-$(RELVER).tar.gz \
          --exclude test \
          $(SNAP)/$(SITE)/twisted

install: twisted-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf twisted-$(SNAP)-$(RELVER).tar.gz

upload: twisted-$(SNAP)-$(RELVER).tar.gz
	scp twisted-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
