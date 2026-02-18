DESCRIPTION = "Open Lighting Architecture (OLA)"
HOMEPAGE = "https://www.openlighting.org/ola/"
LICENSE = "GPL-2.0-or-later"
LIC_FILES_CHKSUM = "file://COPYING;md5=751419260aa954499f7abaabaa882bbe"
SRCREV = "9b7f0b0c8a6b3d4c4c4f4c2b8d4e2c6f7a1b9e2a"

SRC_URI = "git://github.com/OpenLightingProject/ola.git;branch=master;protocol=https"
S = "${WORKDIR}/git"

inherit cmake pkgconfig

DEPENDS = "protobuf protobuf-native libmicrohttpd"

# Falls nötig, je nach OLA-Version:
# EXTRA_OECMAKE += "-DWITH_HTTP=yes -DWITH_PYTHON=no"

# Standard-CMake-Flow: do_configure/do_compile/do_install kommen von 'cmake'
