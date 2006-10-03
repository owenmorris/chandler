
VERSION=0.9.8d
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
OPENSSL=$(BUILD_ROOT)/openssl
SRC=$(OPENSSL)/openssl-$(VERSION)
BUILD=build_$(SNAP)
TARBALL=openssl-$(SNAP)-$(RELVER).tar.gz

include ../Makefile.inc

ifeq ($(OS),Cygwin)
# Build using Visual C++ compiler
ifeq ($(DEBUG),1)
MK1MF=sed -e "s/mk1mf\.pl/mk1mf\.pl debug/" ms/do_masm.bat > ms/do_masm_debug.bat
OUT32DLL=out32dll.dbg
DOMASM=do_masm_debug.bat
else
MK1MF=echo "Defaults work"
OUT32DLL=out32dll
DOMASM=do_masm.bat
endif

$(SRC)/$(BUILD)/ms/$(DOMASM):
	cd $(SRC); \
      mkdir -p $(BUILD); \
      cp Makefile.org Makefile.shared *.h $(BUILD)/; \
      cp -r crypto ssl apps certs tools util ms include test config engines $(BUILD)/; \
      cd $(BUILD); \
      $(MK1MF)
	chmod a+x $(SRC)/$(BUILD)/ms/$(DOMASM)

config:
	cd $(SRC)/$(BUILD); \
      MAKEFLAGS=; \
      perl ../Configure --openssldir=$(PREFIX) --install_prefix=$(PREFIX) $(CONF_OPT) VC-WIN32

masm:
	cd $(SRC)/$(BUILD); \
      MAKEFLAGS=; \
      ms/$(DOMASM)

ntdll:
	cd $(SRC)/$(BUILD); \
      MAKEFLAGS=; \
      nmake -f ms/ntdll.mak

copy:
	mkdir -p $(BUILD_ROOT)/$(SNAP)/$(SITE)/M2Crypto
	cp -f $(SRC)/$(BUILD)/$(OUT32DLL)/ssleay32.dll $(BUILD_ROOT)/$(SNAP)/$(SITE)/M2Crypto/
	cp -f $(SRC)/$(BUILD)/$(OUT32DLL)/libeay32.dll $(BUILD_ROOT)/$(SNAP)/$(SITE)/M2Crypto/
	cp -f $(SRC)/$(BUILD)/$(OUT32DLL)/ssleay32.lib $(PREFIX)/lib/
	cp -f $(SRC)/$(BUILD)/$(OUT32DLL)/libeay32.lib $(PREFIX)/lib/
	cp -fr $(SRC)/$(BUILD)/inc32/openssl $(PREFIX)/Include

openssl: apply $(SRC)/$(BUILD)/ms/$(DOMASM) config masm ntdll copy

# Need to put the files into M2Crypto dir so that Windows finds our versions
binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(OPENSSL)/$(TARBALL) \
          $(SNAP)/$(SITE)/M2Crypto/ssleay32.dll \
          $(SNAP)/$(SITE)/M2Crypto/libeay32.dll

tests:
	cd $(SRC)/$(BUILD)/$(OUT32DLL); \
	../ms/test.bat

else

$(SRC)/$(BUILD):
	cd $(SRC); \
      mkdir $(BUILD); \
      cp -R -P Configure Makefile.org Makefile.shared *.h crypto ssl apps certs tools util doc include test config engines $(BUILD)/

openssl: apply $(SRC)/$(BUILD)
	cd $(SRC)/$(BUILD); ../config shared --openssldir=$(PREFIX) $(CONF_OPT)
	$(MAKE) -C $(SRC)/$(BUILD)
	$(MAKE) -C $(SRC)/$(BUILD) install

tests:
	cd $(SRC)/$(BUILD); \
      $(MAKE) test

ifeq ($(OS),Darwin)

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(OPENSSL)/$(TARBALL) \
          $(SNAP)/lib/libcrypto.0.9.8.dylib \
          $(SNAP)/lib/libcrypto.dylib \
          $(SNAP)/lib/libssl.0.9.8.dylib \
          $(SNAP)/lib/libssl.dylib

else

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(OPENSSL)/$(TARBALL) \
          $(SNAP)/lib/libcrypto.so.0.9.8 \
          $(SNAP)/lib/libcrypto.so \
          $(SNAP)/lib/libssl.so.0.9.8 \
          $(SNAP)/lib/libssl.so

endif # if OS X or linux
endif # if Cygwin or not

openssl-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/openssl-$(VERSION).tar.gz

sources: openssl-$(VERSION).tar.gz

openssl-$(VERSION)-expanded: openssl-$(VERSION).tar.gz
	tar xvzf openssl-$(VERSION).tar.gz
	touch openssl-$(VERSION)-expanded

expand: openssl-$(VERSION)-expanded

apply:
	patch -Nup0 < patches-$(VERSION); echo ok

build: expand openssl

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

test: tests

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
