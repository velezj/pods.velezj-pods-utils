# Default pod makefile distributed with pods version: 12.09.21

default_target: all

# Default to a less-verbose build.  If you want all the gory compiler output,
# run "make VERBOSE=1"
$(VERBOSE).SILENT:

# Figure out where to build the software.
#   Use BUILD_PREFIX if it was passed in.
#   If not, search up to four parent directories for a 'build' directory.
#   Otherwise, use ./build.
ifeq "$(BUILD_PREFIX)" ""
BUILD_PREFIX:=$(shell for pfx in ./ .. ../.. ../../.. ../../../..; do d=`pwd`/$$pfx/build;\
               if [ -d $$d ]; then echo $$d; exit 0; fi; done; echo `pwd`/build)
endif
# create the build directory if needed, and normalize its path name
BUILD_PREFIX:=$(shell mkdir -p $(BUILD_PREFIX) && cd $(BUILD_PREFIX) && echo `pwd`)

# Default to a release build.  If you want to enable debugging flags, run
# "make BUILD_TYPE=Debug"
ifeq "$(BUILD_TYPE)" ""
BUILD_TYPE="Release"
endif

all: pod-build/Makefile
	$(MAKE) -C pod-build all install

	mkdir -p $(BUILD_PREFIX)/bin
	sed s@LOCATION@$(BUILD_PREFIX)/bin/@ src/create-configure-pod.sh > $(BUILD_PREFIX)/bin/create-configure-pod.sh
	chmod a+x $(BUILD_PREFIX)/bin/create-configure-pod.sh
	cp src/Makefile.template $(BUILD_PREFIX)/bin/Makefile.template

	sed s@LOCATION@$(BUILD_PREFIX)@ src/build-pod > $(BUILD_PREFIX)/bin/build-pod
	chmod a+x $(BUILD_PREFIX)/bin/build-pod

	-if [ -e $(BUILD_PREFIX)/bin/pkg-config ]; then rm $(BUILD_PREFIX)/bin/pkg-config; fi
	ln -s `pwd`/src/my-sneaky-pkg-config.py $(BUILD_PREFIX)/bin/pkg-config
	chmod a+x $(BUILD_PREFIX)/bin/pkg-config

	mkdir -p pod-build/
	echo $(BUILD_PREFIX)/bin/create-configure-pod.sh >> pod-build/install_manifest.txt
	echo $(BUILD_PREFIX)/bin/Makefile.template >> pod-build/install_manifest.txt
	echo $(BUILD_PREFIX)/bin/build-pod >> pod-build/install_manifest.txt
	echo $(BUILD_PREFIX)/bin/pkg-config >> pod-build/install_manifest.txt


pod-build/Makefile:
	$(MAKE) configure

.PHONY: configure
configure:
	@echo "\nBUILD_PREFIX: $(BUILD_PREFIX)\n\n"

	# create the temporary build directory if needed
	@mkdir -p pod-build

	# run CMake to generate and configure the build scripts
	@cd pod-build && cmake -DCMAKE_INSTALL_PREFIX=$(BUILD_PREFIX) \
		   -DCMAKE_BUILD_TYPE=$(BUILD_TYPE) ..

clean:
	-if [ -e pod-build/install_manifest.txt ]; then rm -f `cat pod-build/install_manifest.txt`; fi
	-if [ -d pod-build ]; then $(MAKE) -C pod-build clean; rm -rf pod-build; fi

# other (custom) targets are passed through to the cmake-generated Makefile 
%::
	$(MAKE) -C pod-build $@
