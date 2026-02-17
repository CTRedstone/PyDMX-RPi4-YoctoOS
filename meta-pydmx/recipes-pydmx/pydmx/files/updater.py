import time
import client as cl
from tkinter import *
import prgbarWin as pbw
from json import load as jsload, dump as jsdump

class vars():
	install = False
	fullInstall = False

def install():
	print("updater: Loading file contents of update files...") #After user agreement, file contents will be requested from server
	if vars.fullInstall: _resp = cl.callPath("/pydmx/updater/getFullUpdate")["value"]
	else: _resp = cl.callPath("/pydmx/updater/getUpdate")["value"]
	if type(_resp) != dict: #If the data type returned is not dict ({filename:content}), the Installation will be aborted.
		print("updater: Invailid return type for update data")
		vars.infLbl.config(text="Install failed")
		vars.win.update()
		vars.win.after(1000,vars.win.destroy)

	print("updater: Installing changes...")
	cnt = 0
	installed = 0
	fls = len(vars.updFiles)
	"""pgbw = pbw.initwin()
	pgbw = pbw.setinf(pgbw,inftxt="[PyDMX] Installing update")
	pgbw = pbw.setprg(pgbw)"""
	for elm in vars.updFiles:
		cnt += 1
		#pgbw = pbw.setprg(pgbw,prgfloat=cnt/len(vars.updFiles))
		print(f"updater: Installing changes on file '{elm}' [{cnt}/{fls}]")
		vars.infLbl.config(text=f"[{cnt}/{fls}] Installing file '{elm}'...")
		vars.win.update()
		if elm not in ("config.json","config.new.json"):
			"""
			If the filename is not config.json, the file will just be overwritten with the new contents.
			If there are errors while installing, the installation will continue.
			"""
			try:
				with open(elm,"w+") as fle: fle.write(''.join(_resp[elm]))
				print(f"updater: Installed changes on file '{elm}' [{cnt}/{fls}]")
				vars.infLbl.config(text=f"[{cnt}/{fls}] Installed update on file '{elm}'")
				vars.win.update()
				installed += 1
			except Exception as exc:
				print(f"updater: Install of file '{elm}' [{cnt}/{fls}] failed: {exc}")
				vars.infLbl.config(text=f"[{cnt}/{fls}] Install of file '{elm}' failed")
		else:
			print(f"updater: Install of file '{elm}' [{cnt}/{fls}] failed: File is configuration file")
			"""
			If there are updates on config.json, only the "window" segment will be overwritten,
			because the rest are userspecific settings.
			
			with open(elm,"r") as fle: filecnt = jsload(fle)
			filecnt["window"] = _resp[elm]
			with open(elm,"w+") as fle: jsdump(filecnt,fle)
			installed += 1"""
		time.sleep(0.1)
	#pbw.endwin(pgbw)
	if installed == cnt:
		"""
		If all files were installed correctly, the version number in config.json gets updated and the
		user gets prompted via GUI and terminal to restart PyDMX.
		"""
		vars.install = True

		with open("config.new.json","r") as fle: filecnt = jsload(fle)
		filecnt["system"]["version"] = vars.serverVer
		with open("config.new.json","w+") as fle: jsdump(filecnt,fle)

		print("updater: Install completed")
		vars.infLbl.config(text="Installed")
		vars.win.update()
		def hint():
			vars.infLbl.config(text="Please restart PyDMX now",fg="red")
			vars.win.update()
			vars.win.after(2500,vars.win.destroy)
		vars.win.after(1000,hint)
	else:
		"""
		If the number of successfully installed files does not match the goal, the local version number will not be
		updated. Instead, the user will only be messaged about the error.
		"""
		print(f"updater: Install failed due to installation errors - changes only applied on {installed} of {fls} files")
		vars.infLbl.config(text="Install failed (install errors)")
		vars.win.update()
		vars.install = False
		vars.win.after(2000,vars.win.destroy)

def skip():
	vars.infLbl.config(text="Skipping install...")
	vars.win.update()
	vars.win.after(1000,vars.win.destroy)

def updater(ver):
	try:
		print("updater: Connecting to server and testing connection...")
		try: cl.initConnection("ctredstone.pythonanywhere.com") #initializing server connection
		except Exception as exc:
			print(f"updater: Some exception occured while trying to connect to server ({exc})")
			print("updater: Skipping")
			return
		print("updater: Connected to server...")
		print(f"updater: Connection data stored for communication: svrAddr='{cl.vars.svrAddr}' svrPortCall={cl.vars.svrPortCall} svrPort={cl.vars.svrPort} svrAuth='{cl.vars.svrAuth}'")
		_resp = cl.sendData({"value":"Test proceed"},"/getConnectionData") #Checks if the serverconnection is okay
		if "recvdata" not in list(_resp.keys()) or _resp["recvdata"] != {"value":"Test proceed"}:
			print("updater: Failed to update because connection to server is faulty")
			raise Exception("Broken connection to server")
		print("updater: Connection test proceed")

		print("updater: Requesting current version...") #Requests the version and the description of the current update
		vars.serverVer = cl.callPath("/pydmx/updater/getCurrentVersion")["value"]
		vars.versionDescrib = cl.callPath("/pydmx/updater/getCurrentVersion")["description"]

		vars.versionType = cl.callPath("/pydmx/updater/getCurrentVersion")["type"] #Requests the type of the update
		if vars.versionType == "codeupload": #type codeupload is just for admins, so updater will exit
			print(f"updater: Newest version on the server is a codeupload (not to download). Exiting")
			raise Exception(f"Newest version not to download")
		print(f"updater: Newest version on the server is from type {vars.versionType}")

		if ver == vars.serverVer or ver == f"v{vars.serverVer[0]}.{vars.serverVer[1]}": #If the current version matches the server's version, updater will exit
			print(f"updater: Current version '{ver}' is up to date")
			raise Exception("Current version up to date")
		print(f"updater: Version of code '{ver}' does not match to the current version 'v{vars.serverVer[0]}.{vars.serverVer[1]}'")
		if type(ver) == str:
			pos1 = int(ver.split(".")[0][1:])
			pos2 = int(ver.split(".")[1])
		elif type(ver) == list:
			pos1 = ver[0]
			pos2 = ver[1]
		if (pos1 > vars.serverVer[0]) or (pos2 > vars.serverVer[1] and pos1 == vars.serverVer[0]): #updater will be ended if the local code version id is higher than the server's ID
			print(f"updater: Version of code '{ver}' is higher than the version of the current code uploaded. If you are the developer, please update the server's data")
			raise Exception("Version to new")
		elif (vars.serverVer[0]-pos1 > 1) or (vars.serverVer[1]-pos2 > 1): #If the local version has a larger distance than one version to the current version, every updateable file from the server will be updated
			print(f"updater: Full update required because server version has a distance of more than one version from current")
			vars.fullInstall = True

		print("updater: new version found on server")
		print("updater: loading version details...") #Request for list of (new) files, to show them in the GUI
		if vars.fullInstall: vars.updFiles = cl.callPath("/pydmx/updater/getFullUpdateFiles")["value"]
		else: vars.updFiles = cl.callPath("/pydmx/updater/getUpdateFiles")["value"]
		if type(vars.updFiles) != list:
			print(f"updater: Server-sided error while loading update files: {vars.updFiles}")
			raise Exception(f"Server-sided error while loading update files: {vars.updFiles}")

		print(f"updater: Files to update: {' ; '.join(vars.updFiles)}")

		print("updater: Building update GUI") #GUI for user if an update can be done
		vars.win = Tk()
		vars.win.title(f"Update PyDMX to v{vars.serverVer[0]}.{vars.serverVer[1]}?")
		vars.frm = Frame(vars.win)
		vars.infLbl = Label(vars.frm,text="Restart PyDMX after update installation")
		vars.updTxt = Text(vars.frm,width=200,height=15) #len(vars.updFiles)+4)
		vars.updTxt.insert(0.0,f"Files which can be updated:\n- "+'\n- '.join(vars.updFiles)+f"\nUpdatetype: {vars.versionType}\nCurrent version: v{pos1}.{pos2}\nVersion comment: {vars.versionDescrib}\nHint: For commands, etc. use command 'help' in GUI")
		vars.instBtn = Button(vars.frm,text="Install updates",command=install)
		vars.skipBtn = Button(vars.frm,text="Skip updates",command=skip)
		vars.infLbl.pack()
		vars.updTxt.pack()
		vars.instBtn.pack()
		vars.skipBtn.pack()
		vars.frm.pack()

		print("updater: Starting mainloop of update GUI")
		vars.win.mainloop()
	except Exception as exc:
		print(f"Failed to update: {exc}")
	finally:
		print("updater: Closing connection to server...")
		try: cl.closeConnection()
		except: pass
		print("updater: Connection to server closed")
		return vars.install
