
# r458 == M2Crypto 0.16
VERSION=458
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)3
SRC=$(BUILD_ROOT)/m2crypto/M2Crypto-$(VERSION)
BUILD=build_$(SNAP)
TARBALL=m2crypto-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

apply: patches
	patch -Nup0 < patches || true
	cd $(SRC); patch -Nup0 < ../bug7068.diff || true


ifeq ($(OS),Cygwin)
build: expand apply
	cd $(SRC); \
	$(PYTHON) setup.py \
	      --openssl=`cygpath -aw $(BUILD_ROOT)/$(SNAP)` \
          build_ext --swig=`cygpath -aw $(SWIG)` \
                    --library-dirs=`cygpath -aw $(BUILD_ROOT)/$(SNAP)/lib` \
                    --include-dirs=`cygpath -aw $(BUILD_ROOT)/$(SNAP)/include` \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install --force

else
build: expand apply
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
	      --openssl=$(BUILD_ROOT)/$(SNAP) \
          build_ext --swig=$(SWIG) \
                    --library-dirs=$(BUILD_ROOT)/$(SNAP)/lib \
                    --include-dirs=$(BUILD_ROOT)/$(SNAP)/include \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install --force

endif

tests:
	cd $(SRC)/tests; $(PYTHON) alltests.py

M2Crypto-$(VERSION).tar.gz:
	svn export -r $(VERSION) http://svn.osafoundation.org/m2crypto/trunk M2Crypto-$(VERSION)
	tar czf M2Crypto-$(VERSION).tar.gz M2Crypto-$(VERSION)

sources: M2Crypto-$(VERSION).tar.gz

M2Crypto-$(VERSION)-expanded: M2Crypto-$(VERSION).tar.gz
	tar zxvf M2Crypto-$(VERSION).tar.gz
	touch M2Crypto-$(VERSION)-expanded

expand: M2Crypto-$(VERSION)-expanded

binaries: strip
	cd $(BUILD_ROOT); \
      find $(SNAP)/$(SITE)/M2Crypto -name "*.py[co]" -delete; \
      tar -cvzf $(BUILD_ROOT)/m2crypto/$(TARBALL) \
          $(SNAP)/$(SITE)/M2Crypto

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

test: tests

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
