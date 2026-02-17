DESCRIPTION = "Custom PyDMX Splash Image"
LICENSE = "CLOSED"

SRC_URI = "file://psplash-pydmx.png"

S = "${WORKDIR}"

inherit psplash

PSPLASH_IMAGES = "file://psplash-pydmx.png;outsuffix=default"

IMAGE_INSTALL:append = " psplash-pydmx"
