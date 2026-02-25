require protobuf_3.19.6.bb
inherit native
EXTRA_OECONF += "--enable-static --disable-shared"
