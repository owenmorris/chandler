
include ../Makefile.inc

RELVER=0.12
M2CRYPTO=$(INTERNAL)/m2crypto

BUILD=build_$(SNAP)

build: $(PYTHON)
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(M2CRYPTO)/m2crypto-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/m2crypto*

upload: m2crypto-$(SNAP)-$(RELVER).tar.gz
	scp m2crypto-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)


clean:
	rm -rf $(BUILD)


