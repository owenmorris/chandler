
include ../Makefile.inc

VERSION=20Feb04
SWIG=$(BUILD_ROOT)/swig
SRC=$(SWIG)/SWIG-$(VERSION)

BUILD=build_$(SNAP)

.PHONY: swig

ifeq ($(OS),Cygwin)

$(SRC)/$(BUILD)/Makefile:
	mkdir -p $(SRC)/$(BUILD); \
	cd $(SRC)/$(BUILD); \
	PATH="$(GCJ_HOME)/bin:$(PATH)"; \
	../configure --prefix=`cygpath -am $(PREFIX)` \
                     --with-python=`cygpath -am $(PYTHON)` \
                     --build=i386-pc-cygwin

swig: $(SRC)/$(BUILD)/Makefile
	PATH="$(GCJ_HOME)/bin:$(PATH)"; $(MAKE) -C $(SRC)/$(BUILD)
	$(MAKE) -C $(SRC)/$(BUILD) install

else

$(SRC)/$(BUILD)/Makefile:
	mkdir -p $(SRC)/$(BUILD); \
	cd $(SRC)/$(BUILD); \
	../configure --prefix=$(PREFIX) \
                     --with-python=$(PYTHON)

swig: $(SRC)/$(BUILD)/Makefile
	$(MAKE) -C $(SRC)/$(BUILD)
	$(MAKE) -C $(SRC)/$(BUILD) install

endif


apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

snap:
	tar -cvzf $(SNAP).tar.gz . --no-recursion

clean:
	rm -rf $(SRC)/$(BUILD)

expand: SWIG-$(VERSION).tar.gz 
	tar xvzf SWIG-$(VERSION).tar.gz

build: apply swig

