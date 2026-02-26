require protobuf_3.19.6.bb
inherit native
SRC_URI += "file://0001-patch-libprotoc-native-installation.patch"
EXTRA_OECONF += "--enable-static --disable-shared"
