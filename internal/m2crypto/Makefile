
include ../Makefile.inc

RELVER=0.12-3
M2CRYPTO=$(INTERNAL)/m2crypto

MANIFEST=$(SNAP)/$(SITE)/M2Crypto

BUILD=build_$(SNAP)

ifeq ($(OS),Cygwin)

build: $(PYTHON)
	PATH="$(BUILD_ROOT)/$(SNAP)/bin:$(PATH)" \
	$(PYTHON) setup.py \
		build_ext --library-dirs=`cygpath -aw $(BUILD_ROOT)/$(SNAP)/lib` \
			--include-dirs=`cygpath -aw $(BUILD_ROOT)/$(SNAP)/include` \
		build --build-base=$(BUILD) $(DIST_OPT) \
		install --force; \
	cp -f $(BUILD_ROOT)/$(SNAP)/bin/libeay32.dll $(BUILD_ROOT)/$(MANIFEST); \
	cp -f $(BUILD_ROOT)/$(SNAP)/bin/ssleay32.dll $(BUILD_ROOT)/$(MANIFEST)

else

build: $(PYTHON)
	PATH="$(BUILD_ROOT)/$(SNAP)/bin:$(PATH)" \
	$(PYTHON) setup.py \
		build_ext --library-dirs=$(BUILD_ROOT)/$(SNAP)/lib \
			--include-dirs=$(BUILD_ROOT)/$(SNAP)/include \
		build --build-base=$(BUILD) $(DIST_OPT) \
		install --force

endif

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(M2CRYPTO)/m2crypto-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)
	$(MD5) m2crypto-$(SNAP)-$(RELVER).tar.gz > m2crypto-$(SNAP)-$(RELVER).tar.gz.md5

upload: m2crypto-$(SNAP)-$(RELVER).tar.gz
	scp m2crypto-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp m2crypto-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

install:
	cd $(BUILD_ROOT); \
        tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -

clean:
	rm -rf $(BUILD)
	rm -f _m2crypto.py
	rm -f SWIG/_m2crypto.c

realclean: clean
	rm -fr build_debug build_release
	rm -f m2crypto-debug-*.tar.gz* m2crypto-release-*.tar.gz*
