include ../Makefile.inc

VERSION=1.0
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
DATEUTIL=$(BUILD_ROOT)/dateutil
MANIFEST=$(SNAP)/$(SITE)/dateutil
BUILD=build_$(SNAP)
SRC=python-dateutil-$(VERSION)

$(SRC).tar.bz2:
	$(CURL) http://builds.o11n.org/external/$(SRC).tar.bz2

sources: python-dateutil-$(VERSION).tar.bz2

$(SRC)-expanded: $(SRC).tar.bz2
	tar xvjf $(SRC).tar.bz2
	touch $(SRC)-expanded

expand: $(SRC)-expanded

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

build: expand #apply
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install --force

binaries:
	cd $(BUILD_ROOT); \
      find $(MANIFEST) -name "*.pyc" | xargs rm -f; \
      find $(MANIFEST) -name "*.pyo" | xargs rm -f; \
      tar -C $(BUILD_ROOT) -cvzf $(DATEUTIL)/dateutil-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)

upload: dateutil-$(SNAP)-$(RELVER).tar.gz
	scp dateutil-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

install:
	cd $(BUILD_ROOT); \
        tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
