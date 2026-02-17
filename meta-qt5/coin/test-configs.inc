# https://github.com/shr-project/jenkins-jobs/blob/master/jenkins-job.sh
# need space for dunfell build
INHERIT += "rm_work"
# We want musl and glibc to share the same tmpfs, so instead of appending default "-${TCLIBC}" we append "fs"
TCLIBCAPPEND = "fs"
PREFERRED_PROVIDER_virtual/fftw = "fftw"
# use gold
#DISTRO_FEATURES:append = " ld-is-gold"
# use ptest
DISTRO_FEATURES:append = " ptest"
# use systemd
INIT_MANAGER:forcevariable = "systemd"
# use opengl
DISTRO_FEATURES:append = " opengl"
# use wayland to fix building weston and qtwayland
DISTRO_FEATURES:append = " wayland"
PREFERRED_PROVIDER_jpeg = "libjpeg-turbo"
PREFERRED_PROVIDER_jpeg-native = "libjpeg-turbo-native"
PREFERRED_PROVIDER_gpsd = "gpsd"
PREFERRED_PROVIDER_e-wm-sysactions = "e-wm"
ESYSACTIONS = "e-wm-sysactions"
# don't pull libhybris unless explicitly asked for
PREFERRED_PROVIDER_virtual/libgl ?= "mesa"
PREFERRED_PROVIDER_virtual/libgles1 ?= "mesa"
PREFERRED_PROVIDER_virtual/libgles2 ?= "mesa"
PREFERRED_PROVIDER_virtual/egl ?= "mesa"
# to fix fsoaudiod, alsa-state conflict in shr-image-all
VIRTUAL-RUNTIME_alsa-state = ""
# to prevent alsa-state being pulled into -dev or -dbg images
RDEPENDS:${PN}-dev:pn-alsa-state = ""
RDEPENDS:${PN}-dbg:pn-alsa-state = ""
# to fix dependency on conflicting x11-common from packagegroup-core-x11
VIRTUAL-RUNTIME_xserver_common ?= "xserver-common"
RDEPENDS:${PN}-dev:pn-x11-common = ""
RDEPENDS:${PN}-dbg:pn-x11-common = ""
# to fix apm, fso-apm conflict in shr-image-all
VIRTUAL-RUNTIME_apm = "fso-apm"
# require conf/distro/include/qt5-versions.inc
# QT5_VERSION = "5.4.0+git%"
# for qtwebkit etc
# see https://bugzilla.yoctoproject.org/show_bug.cgi?id=5013
# DEPENDS:append:pn-qtbase = " mesa"
PACKAGECONFIG:append:pn-qtbase = " icu gl accessibility freetype fontconfig"
# qtwayland doesn't like egl and xcomposite-glx enabled at the same time
# http://lists.openembedded.org/pipermail/openembedded-devel/2016-December/110444.html
PACKAGECONFIG:remove:pn-qtwayland = "xcomposite-egl xcomposite-glx"
# for webkit-efl
PACKAGECONFIG:append:pn-harfbuzz = " icu"
# enable reporting
# needs http://patchwork.openembedded.org/patch/68735/
#ERR_REPORT_SERVER = "errors.yoctoproject.org"
#ERR_REPORT_PORT = "80"
#ERR_REPORT_USERNAME = "Martin Jansa"
#ERR_REPORT_EMAIL = "Martin.Jansa@gmail.com"
#ERR_REPORT_UPLOAD_FAILURES = "1"
#INHERIT += "report-error"
# needs patch with buildstats-summary.bbclass
INHERIT += "buildstats buildstats-summary"
# be more strict with QA warnings, turn them all to errors:
ERROR_QA:append = " ldflags useless-rpaths rpaths staticdev libdir xorg-driver-abi             textrel already-stripped incompatible-license files-invalid             installed-vs-shipped compile-host-path install-host-path             pn-overrides infodir build-deps             unknown-configure-option symlink-to-sysroot multilib             invalid-packageconfig host-user-contaminated uppercase-pn"
WARN_QA:remove = " ldflags useless-rpaths rpaths staticdev libdir xorg-driver-abi             textrel already-stripped incompatible-license files-invalid             installed-vs-shipped compile-host-path install-host-path             pn-overrides infodir build-deps             unknown-configure-option symlink-to-sysroot multilib             invalid-packageconfig host-user-contaminated uppercase-pn"
# workaround for qemu
# nativesdk-qemu-user-mips rdepends on nativesdk-bash, but it isn't a build dependency
INSANE_SKIP:nativesdk-qemu-user-mips = "build-deps"
# enable thumb for broader test coverage (oe-core autobuilder doesn't have thumb enabled)
PREFERRED_ARM_INSTRUCTION_SET              ?= "thumb"
ARM_INSTRUCTION_SET = "${PREFERRED_ARM_INSTRUCTION_SET}"
# use musl for qemux86 and qemux86copy
TCLIBC:qemux86 = "musl"
TCLIBC:qemux86copy = "musl"
# limit parallel make to avoid OOM
PARALLEL_MAKE:pn-qtwebkit = "-j 8"
# For decrease memory usage.
SDK_XZ_COMPRESSION_LEVEL = "-1"
