include ../../Makefile.inc

CHANDLER_CFLAGS = -Wall -Werror -I/usr/include/python$(PYTHON_VER) -lpython$(PYTHON_VER) -framework Foundation

ifeq ($(SNAP),debug)
CHANDLER_CFLAGS += -g3 -DDEBUG
else
CHANDLER_CFLAGS += -g -O2
endif

build: $(BUILD_ROOT)/$(SNAP)/Chandler

$(BUILD_ROOT)/$(SNAP)/Chandler: Chandler
	@cp -v $< $@

Chandler: Chandler.m
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(CC) $< -o $@ $(CHANDLER_CFLAGS)

clean:
	@echo Cleaning up in $$(pwd); rm -rvf Chandler.dSYM Chandler
include ../../Makefile.inc

CHANDLER_CFLAGS = -Wall -Werror -I/usr/include/python$(PYTHON_VER) -lpython$(PYTHON_VER) -framework Foundation

ifeq ($(SNAP),debug)
CHANDLER_CFLAGS += -g3 -DDEBUG
else
CHANDLER_CFLAGS += -g -O2
endif

build: $(BUILD_ROOT)/$(SNAP)/Chandler

$(BUILD_ROOT)/$(SNAP)/Chandler: Chandler
	@cp -v $< $@

Chandler: Chandler.m
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(CC) $< -o $@ $(CHANDLER_CFLAGS)

clean:
	@echo Cleaning up in $$(pwd); rm -rvf Chandler.dSYM Chandler
