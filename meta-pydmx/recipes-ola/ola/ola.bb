DESCRIPTION = "Open Lighting Architecture (OLA)"
LICENSE = "GPL-2.0-or-later"
LIC_FILES_CHKSUM = "file://COPYING;md5=751419260aa954499f7abaabaa882bbe"

SRC_URI = "git://github.com/OpenLightingProject/ola.git;branch=master;protocol=https;destsuffix=git"
SRCREV = "${AUTOREV}"

PV = "1.0+git${SRCPV}"
S = "${WORKDIR}/git"

inherit autotools pkgconfig

DEPENDS = "protobuf protobuf-native libmicrohttpd bison-native flex-native python3-native"

# Options aren't recognized by OLA
#EXTRA_OECONF += " --disable-cpp-lint --disable-python-lint --disable-gcov --disable-gcovr"
EXTRA_OEMAKE += "OLA_DISABLE_PYTHON_LINT=1"
EXTRA_OEMAKE += "OLA_DISABLE_CPP_LINT=1"
EXTRA_OEMAKE += "OLA_DISABLE_COVERAGE=1"

# UNBUILDABLE DUE TO SRCREV
#DESCRIPTION = "Open Lighting Architecture (OLA)"
#HOMEPAGE = "https://www.openlighting.org/ola/"
#LICENSE = "GPL-2.0-or-later"
#LIC_FILES_CHKSUM = "file://COPYING;md5=751419260aa954499f7abaabaa882bbe"
#SRCREV = "9b7f0b0c8a6b3d4c4c4f4c2b8d4e2c6f7a1b9e2a"

#SRC_URI = "git://github.com/OpenLightingProject/ola.git;branch=master;protocol=https"
#S = "${WORKDIR}/git"

#inherit cmake pkgconfig

#DEPENDS = "protobuf protobuf-native libmicrohttpd"

# Falls nötig, je nach OLA-Version:
# EXTRA_OECMAKE += "-DWITH_HTTP=yes -DWITH_PYTHON=no"

# Standard-CMake-Flow: do_configure/do_compile/do_install kommen von 'cmake'
