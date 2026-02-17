DESCRIPTION = "Custom PyDMX Splash Image"
LICENSE = "CLOSED"

SRC_URI = "file://psplash-pydmx.png"

#S = "${WORKDIR}"

#inherit psplash

PSPLASH_IMAGES = "file://psplash-pydmx.png;outsuffix=default"

#IMAGE_INSTALL:append = " psplash-pydmx"

S = "${WORKDIR}"

do_install() {
    install -d ${D}${datadir}/psplash
    install -m 0644 ${WORKDIR}/psplash-pydmx.png ${D}${datadir}/psplash/psplash.png
}
