
include ../Makefile.inc

VERSION=0.9.7d
RELVER=$(VERSION)-1
OPENSSL=$(BUILD_ROOT)/openssl
SRC=$(OPENSSL)/openssl-$(VERSION)

BUILD=build_$(SNAP)

.PHONY: openssl

ifeq ($(OS),Cygwin)
BINFILE=openssl.exe
else
BINFILE=openssl
endif

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(SRC)/openssl-$(SNAP)-$(RELVER).tar.gz \
                   $(SNAP)/openssl.cnf \
                   $(SNAP)/bin/c_rehash \
                   $(SNAP)/bin/$(BINFILE) \
                   $(SNAP)/include/ \
                   $(SNAP)/lib/libcrypto.a \
                   $(SNAP)/lib/libssl.a  \
                   $(SNAP)/lib/pkgconfig/openssl.pc \
                   $(SNAP)/misc \
                   $(SNAP)/private \
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

apply: expand patches
	patch -Nup0 < patches; echo ok

clean:
	rm -rf $(SRC)

build: apply openssl
