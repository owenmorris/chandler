
include ../Makefile.inc

VERSION=0.9.7d
RELVER=$(VERSION)-1
OPENSSL=$(BUILD_ROOT)/openssl
SRC=$(OPENSSL)/openssl-$(VERSION)

BUILD=build_$(SNAP)

.PHONY: openssl

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(SRC)/openssl-$(SNAP)-$(RELVER).tar.gz \
                   $(SNAP)/openssl.cnf \
                   $(SNAP)/bin/c_rehash \
                   $(SNAP)/bin/openssl \
                   $(SNAP)/include/openssl \
                   $(SNAP)/misc \
                   $(SNAP)/certs

upload: openssl-$(SNAP)-$(RELVER).tar.gz
	scp openssl-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

$(SRC)/Makefile:
	cd $(SRC); \
	./config --prefix=$(PREFIX) --openssldir=$(PREFIX) $(CONF_OPT)

openssl:   $(SRC)/Makefile
	cd $(SRC); \
        $(MAKE) ; $(MAKE) install 

expand: openssl-$(VERSION).tar.gz
	tar xvzf openssl-$(VERSION).tar.gz
	rm -f openssl-$(VERSION)/Makefile

apply: $(SRC)/Makefile.ssl patches
	patch -Nup0 < patches; echo ok

clean:
	cd $(SRC); make clean; rm -f Makefile

build: apply openssl
