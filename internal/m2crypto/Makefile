
include ../Makefile.inc

RELVER=0.12
M2CRYPTO=$(INTERNAL)/m2crypto

BUILD=build_$(SNAP)

build: $(PYTHON)
	PATH="$(BUILD_ROOT)/$(SNAP)/bin:$(BUILD_ROOT)/$(SNAP)/bin/swig:$(PATH)" \
	$(PYTHON) setup.py \
		build_ext --library-dirs=$(BUILD_ROOT)/$(SNAP)/lib \
			--include-dirs=$(BUILD_ROOT)/$(SNAP)/include \
		build --build-base=$(BUILD) $(DIST_OPT) \
		install --force

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(M2CRYPTO)/m2crypto-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/M2Crypto

upload: m2crypto-$(SNAP)-$(RELVER).tar.gz
	scp m2crypto-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

install:
	cd $(BUILD_ROOT)/..; \
	tar -zxvf $(M2CRYPTO)/m2crypto-$(SNAP)-$(RELVER).tar.gz

clean:
	rm -rf $(BUILD)
	rm -f _m2crypto.py
	rm -f SWIG/_m2crypto.c


