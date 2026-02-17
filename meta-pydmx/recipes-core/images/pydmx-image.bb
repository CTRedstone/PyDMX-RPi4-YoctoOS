DESCRIPTION = "Minimal PyDMX Controller Image"
LICENSE = "CLOSED"

IMAGE_INSTALL = "\
    pydmx \
    ola \
    python3-core \
    python3-tkinter \
    python3-requests \
    python3-random \
    python3-math \
    xserver-xorg \
    xinit \
    openbox"

IMAGE_FEATURES += " splash"

inherit cure-image
