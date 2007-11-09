
include $(BUILD_ROOT)/Makefile.inc

SRC=none

ifeq ($(PYTHON_BUILD),)

$(PREFIX)/$(SITE)/distutils.cfg:
	mkdir -p $(PREFIX)/$(SITE)
	$(PYTHON) $(BUILD_ROOT)/config.py "$(PREFIX)/$(SITE)" "$(PREFIX)/bin"

build: $(PREFIX)/$(SITE)/distutils.cfg

else

build:

endif

sources:
expand:
binaries:
install:
clean:
