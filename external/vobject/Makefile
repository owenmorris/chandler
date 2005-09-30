include ../Makefile.inc

VERSION=0.1.4
RELVER=$(VERSION)-1
VOBJECT=$(BUILD_ROOT)/vobject
MANIFEST=$(SNAP)/$(SITE)/vobject
BUILD=build_$(SNAP)
SRC=vobject-$(VERSION)

.PHONY: patches-$(VERSION)

$(SRC).tar.gz:
	$(CURL) http://builds.o11n.org/external/$(SRC).tar.gz

sources: vobject-$(VERSION).tar.gz

$(SRC)-expanded: $(SRC).tar.gz
	tar xzf $(SRC).tar.gz
	touch $(SRC)-expanded

expand: $(SRC)-expanded

apply: patches-$(VERSION)
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION);echo ok; \
        fi

build: expand apply
	cd $(SRC); \
    MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
        build --build-base=$(BUILD) $(DIST_OPT) \
        install --force

binaries: 
	cd $(BUILD_ROOT); \
      find $(MANIFEST) -name "*.pyc" | xargs rm -f; \
      find $(MANIFEST) -name "*.pyo" | xargs rm -f
	tar -C $(BUILD_ROOT) -cvzf $(VOBJECT)/vobject-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)

upload: vobject-$(SNAP)-$(RELVER).tar.gz
	scp vobject-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

install:
	cd $(BUILD_ROOT); \
      tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -

clean:
	@if [ -f $(PYTHON) ]; then \
      cd $(SRC); \
      $(PYTHON) setup.py clean --all; \
  fi
