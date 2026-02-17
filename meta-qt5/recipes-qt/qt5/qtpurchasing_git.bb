require qt5.inc
require qt5-lts.inc

HOMEPAGE = "http://www.qt.io"
LICENSE = "Apache-2.0 & BSD-3-Clause & ( LGPL-3.0-only | GPL-3.0-only | The-Qt-Company-Commercial )"
LIC_FILES_CHKSUM = " \
    file://LICENSE.LGPLv3;md5=b8c75190712063cde04e1f41b6fdad98 \
    file://LICENSE.GPLv3;md5=40f9bf30e783ddc201497165dfb32afb \
"

DEPENDS += "qtbase qtdeclarative"

SRCREV = "6e55bbb7fc14909f8ed0fadae1f9d486b79cf39f"
