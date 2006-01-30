include ../Makefile.inc

VERSION=0.6a9
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
SETUPTOOLS=$(BUILD_ROOT)/setuptools
BUILD=build_$(SNAP)
SRC=setuptools-$(VERSION)

MANIFEST=$(SNAP)/$(SITE)/setuptools \
         $(SNAP)/$(SITE)/pkg_resources.py \
         $(SNAP)/$(SITE)/easy_install.py \
         $(SNAP)/$(SITE)/site.py \
         $(SNAP)/$(SITE)/setuptools-$(VERSION)-py2.4.egg-info \
         $(SNAP)/bin/easy_install*

.PHONY: patches-$(VERSION)

$(SRC).zip:
	$(CURL) http://builds.osafoundation.org/external/$(SRC).zip

sources: setuptools-$(VERSION).zip

$(SRC)-expanded: $(SRC).zip
	unzip -o $(SRC).zip
	touch $(SRC)-expanded

expand: $(SRC)-expanded

apply: patches-$(VERSION)
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION); echo ok; \
        fi
ifeq ($(OS),Cygwin)

MFILE=`cygpath -aw $(SETUPTOOLS)/manifest.txt`

build: expand apply
	cd $(SRC); \
    $(PYTHON) setup.py -v \
        build --build-base=$(BUILD) $(DIST_OPT) \
        install --record=$(MFILE) --install-scripts=../../$(SNAP)/bin \
                --force --single-version-externally-managed 

else
build: expand apply
	cd $(SRC); \
    MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py -v \
        build --build-base=$(BUILD) $(DIST_OPT) \
        install --record=$(SETUPTOOLS)/manifest.txt --install-scripts=../../$(SNAP)/bin \
                --force --single-version-externally-managed 
endif

binaries: 
	cd $(BUILD_ROOT); \
	      find $(MANIFEST) -name "*.pyc" | xargs rm -f; n\
      find $(MANIFEST) -name "*.pyo" | xargs rm -f
	echo [$(BUILD_ROOT)] [$(MANIFEST)]
	tar -C $(BUILD_ROOT) -cvzf $(SETUPTOOLS)/setuptools-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)

upload: setuptools-$(SNAP)-$(RELVER).tar.gz
	scp setuptools-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

install:
	cd $(BUILD_ROOT); \
      tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
