
VERSION=$(PYICU_VER)-$(SVNVER)
PYICU_VER=0.8
SVNVER=87
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
PYICU=$(BUILD_ROOT)/PyICU
EGG=$(notdir $(shell cd $(BUILD_ROOT); find $(SNAP)/$(SITE) -name 'PyICU-$(PYICU_VER)-py$(PYTHON_VER)-*.egg'))
SRC=$(PYICU)/PyICU-$(VERSION)
BUILD=$(SNAP)
TARBALL=PyICU-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Cygwin)

ifeq ($(DEBUG),1)
ENV=\
  PYICU_LIBRARIES="icuind;icuucd;icudt"
else
ENV=
endif

ENV:=$(ENV) \
  PYICU_INCLUDES=`cygpath -am $(PREFIX)/include/icu` \
  PYICU_LFLAGS="/LIBPATH:"`cygpath -awp "$(PREFIX)/lib"`

apply:
	patch -Nup0 < patches-$(VERSION)-$(OS); echo ok

else

ifeq ($(ICU_BUILD),)
ENV=
else
ENV=\
  PYICU_INCLUDES=$(PREFIX)/icu/include \
  PYICU_LFLAGS=-L$(PREFIX)/icu/lib
endif

apply:

endif

build: expand apply
	cd $(SRC); \
	$(ENV) $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                  install --force

ifneq (/,$(SRC))
clean:
	rm -rf $(SRC)/$(BUILD)
endif

binaries: $(BUILD_ROOT)/$(SNAP)/$(SITE)/$(EGG)
	echo "./$(EGG)" > $(BUILD_ROOT)/$(SNAP)/$(SITE)/PyICU.pth
	tar -C $(BUILD_ROOT) -cvzf $(PYICU)/$(TARBALL) \
                             $(SNAP)/$(SITE)/$(EGG) \
                             $(SNAP)/$(SITE)/PyICU.pth


sources: PyICU-$(VERSION)-expanded

PyICU-$(VERSION)-expanded:
	svn export -r $(SVNVER) http://svn.osafoundation.org/pyicu/trunk PyICU-$(VERSION)
	touch PyICU-$(VERSION)-expanded

expand: PyICU-$(VERSION)-expanded

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

test:
	cd $(SRC); $(PYTHON) setup.py test
