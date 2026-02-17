DESCRIPTION = "PyDMX Controller Application"
LICENSE = "CLOSED"

SRC_URI = "file://__main__.py \
           file://startx.sh \
           file://pydmx.service \
           file://gui.py \
           file://NewPyDMX.py \
           file://dmxClient.py \
           file://dmxServer.py \
           file://client.py \
           file://config.new.json \
           file://guicommands.txt \
           file://imports.txt \
           file://jsonToClass.py \
           file://jsonWin.py \
           file://largeFont.json \
           file://largefont.py \
           file://log.py \
           file://minecraftia.ttf \
           file://olaTerminal.py \
           file://prgbarWin.py \
           file://six.py \
           file://updater.py \
           file://certifi \
           file://chardet \
           file://darkdetect \
           file://idna \
           file://packaging \
           file://Pillow-8.1.2.egg-info \
           file://PyQt5 \
           file://pytools \
           file://requests \
           file://resources \
           file://rgbmatrix \
           file://rgbMatrix \
           file://shows \
           file://urllib3 \
           file://customtkinter \
           file://olad.service"

S = "${WORKDIR}"

inherit systemd

SYSTEMD_SERVICE:${PN} = "pydmx.service"

RDEPENDS:${PN} = "python3-core python3-tkinter python3-requests python3-random python3-math xserver-xorg xinit openbox ola"

do_install() {
	install -d ${D}/opt/pydmx
	cp -r ${WORKDIR}/*.py ${D}/opt/pydmx/
	cp -r ${WORKDIR}/certify ${D}/opt/pydmx/
	cp -r ${WORKDIR}/chardet ${D}/opt/pydmx/
	cp -r ${WORKDIR}/customtkinter ${D}/opt/pydmx/
	cp -r ${WORKDIR}/darkdetect ${D}/opt/pydmx/
	cp -r ${WORKDIR}/idna ${D}/opt/pydmx/
	cp -r ${WORKDIR}/packaging ${D}/opt/pydmx/
	cp -r ${WORKDIR}/Pillow-8.1.2.egg-info ${D}/opt/pydmx/
	cp -r ${WORKDIR}/PyQt5 ${D}/opt/pydmx/
	cp -r ${WORKDIR}/pytools ${D}/opt/pydmx/
	cp -r ${WORKDIR}/requests ${D}/opt/pydmx/
	cp -r ${WORKDIR}/resources ${D}/opt/pydmx/
	cp -r ${WORKDIR}/rgbmatrix ${D}/opt/pydmx/
	cp -r ${WORKDIR}/rgbMatrix ${D}/opt/pydmx/
	cp -r ${WORKDIR}/shows ${D}/opt/pydmx/
	cp -r ${WORKDIR}/urllib3 ${D}/opt/pydmx/
	cp -r ${WORKDIR}/config.new.json ${D}/opt/pydmx/
	cp -r ${WORKDIR}/guicommands.txt ${D}/opt/pydmx/
	cp -r ${WORKDIR}/imports.txt ${D}/opt/pydmx/
	cp -r ${WORKDIR}/largeFont.json ${D}/opt/pydmx/
	cp -r ${WORKDIR}/minecraftia.ttf ${D}/opt/pydmx/
	cp -r ${WORKDIR}/startx.sh ${D}/opt/pydmx/
	cp -r ${WORKDIR}/pydmx.service ${D}/opt/pydmx/
	cp -r ${WORKDIR}/olad.service ${D}/opt/pydmx

	install -m 0755 ${WORKDIR}/__main__.py ${D}/opt/pydmx/
	install -m 0755 ${WORKDIR}/startx.sh ${D}/opt/pydmx/

	install -d ${D}${systemd_system_unitdir}
	install -m 0644 ${WORKDIR}/pydmx.service ${D}§{systemd_system_unitdir}/pydmx.service
}

SYSTEMD_SERVICE:${PN} = "pydmx.service"
SYSTEMD_SERVICE:${PN} += " olad.service"
#inherit systemd
