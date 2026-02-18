DESCRIPTION = "Open Lighting Architecture (OLA)"
HOMEPAGE = "https://www.openlighting.org/ola/"
LICENSE = "GPL-2.0-or-later"
LIC_FILES_CHKSUM = "file://COPYING;md5=751419260aa954499f7abaabaa882bbe"
SRCREV = "c8f3f4c9f2f4f0d8e8e8e2c6c1f1a8b9c6b0f3d"

SRC_URI = "git://github.com/OpenLightingProject/ola.git;branch=master;protocol=https"
S = "${WORKDIR}/git"

inherit cmake pkgconfig

DEPENDS = "protobuf protobuf-native libmicrohttpd"

# Falls nötig, je nach OLA-Version:
# EXTRA_OECMAKE += "-DWITH_HTTP=yes -DWITH_PYTHON=no"

# Standard-CMake-Flow: do_configure/do_compile/do_install kommen von 'cmake'
