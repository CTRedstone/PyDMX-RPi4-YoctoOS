import prgbarWin as pbw
import tkinter as tk
import socket
import time
import sys
import subprocess
from rgbMatrix import matrixDisplay
from customtkinter import *
from jsonWin import jsonWin, utils
from olaTerminal import PyDMX
from dmxServer import dmxServer, reloadHelpFile as dmxServerRHF
from dmxClient import dmxClient
from threading import Thread, Event as threadEvent
from pytools.variables import FE,cFN
from pytools.logger import clearLogFile, logfile
from pytools.configTools import load as loadcnf, save as savecnf
from pytools import exceptions
from copy import deepcopy as dc
from correctConfigWinElements import cc as _correctconfig

#cFN = lambda n=0: sys._getframe(n + 1).f_code.co_name #current function name

class vars():
	mdQuit = False
	simulateMD = True
	debug = False
	debugElements = False
	enableOLA = True
	enablePixelDisp = False
	enableLogFile = True
	started = False
	threadStop = threadEvent()
	errcnt = 0
	maxerr = 2 #means maximum of accepted errors, more errors will stop program from running
	load = True
	mdMsgStack = 0
	mdFont = "minecraftia.ttf"
	mdFontSize = 8
	class dmxcnf():
		fixt = []
		macro = []
		cuelst = []
		cuelst_thr = {}
		cuelst_stop = {}
	class win():
		class fxgen():
			choice = None

"""class exceptions():
	class ValueDefError(Exception): ...
	class ValueLoadError(Exception): ..."""

#Logfunction for everything inside the GUI (already prepeared path PyDMX/window)
def winlog(tpe:str,msg:str,source="commands",errtpe="normal"):
	if tpe in ("err","error","fatal"): vars.errcnt += 1
	color = FE["cyan"] if tpe in ("info","inf") else FE["blue"] if tpe == "debug" else FE["green"] if tpe in ("okay","ok","done","pass") else FE["yellow"] if tpe == "warn" or (tpe in ("err","error") and errtpe == "normal") else FE["red"] if tpe in ("fatal","err","error") else ''
	if vars.debug or tpe != "debug":
		print(color+f"[PyDMX/window/{source}] [{tpe.upper()}] {msg}"+FE["reset"])
		if vars.enableLogFile: logfile(f"PyDMX/window/commands.{source}",f"[{tpe.upper()}] {msg}")

#Sets a text on the screen. The text will disappear after a while
def mdSetMessage(text="",state=False):
	"""
	If state is False, the text will be green on a dark red background.
	If state is True, the text will be red on a dark green background.
	"""
	if not vars.mdQuit:
		vars.pixelDisp.clear()
		vars.mdMsgStack += 1
		if not state: vars.pixelDisp.generateText(text=text[:8],text_color=(30,255,0),bg_color=(30,0,0),font_size=vars.mdFontSize,directDraw=True,font=vars.mdFont)
		elif state: vars.pixelDisp.generateText(text=text[:8],text_color=(255,30,0),bg_color=(0,30,0),font_size=vars.mdFontSize,directDraw=True,font=vars.mdFont)
		vars.winManager.windowAfter("win1",vars.config["general"]["maxMatrixAlertView"],mdMessageClear)

#Clears the text from the display (for mdSetMessage()). Will only clear if there is no Message left on screen
def mdMessageClear():
	if not vars.mdQuit:
		vars.mdMsgStack -= 1
		if vars.mdMsgStack == 0:
			#vars.winManager.windowAfter("win1",vars.config["general"]["maxMatrixAlertView"],
			vars.pixelDisp.clearDisp()
			#vars.winManager.windowAfter("win1",vars.config["general"]["maxMatrixAlertView"]+10,
			pixelDispLoadDust()

class dmx():
	def runCuelist(_id:int,*args): #Executes cuelists from files
		#log(cFN(),"warn","Running cuelists is currently disabled, skipping")
		#return

		log(cFN(),"info",f"Loading cuelist with id {_id} and name '{vars.dmxcnf.cuelst['cuelist'+str(_id)]['name']}'")
		cuelist = vars.dmxcnf.cuelst[f"cuelist{_id}"]
		cues = cuelist["cues"]
		log(cFN(),"ok","Cuelist loaded")

		usedAddr = [] #List which stores the values of Addresses before modified the first time
		savedAddr = [] #List controlles if an addr is already stored in usedAddr
		if cuelist["loop"]: #Will only execute if the cuelist should loop
			ind = 0
			while not vars.threadStop.is_set(): #Checks if the program gets closed
				for elm in cues[ind]["events"]:
					if "level" in list(elm.keys()): #if event is a normal setaddr event
						if (elm["universe"],elm["address"]) not in savedAddr:
							resp = vars.dmxComm.sendCommand(f"channels getChannel universe='{elm['universe']}' addr='{elm['address']}'")
							savedAddr.append((elm["universe"],elm["address"]))
							usedAddr.append((elm["universe"],elm["address"],resp.split("_")[3:]))
						vars.dmxComm.sendCommand(f"channels setChannel universe='{elm['universe']}' addr='{elm['address']}' setto='{elm['level']}'",expectResponse=False)

					elif "newfx" in list(elm.keys()): #if event is a effect creation event
						type = elm["newfx"]
						id = elm["fxid"]
						start = elm["start"]
						end = elm["end"]
						speed = elm["speed"]
						if "stepsInHigh" in list(elm.keys()): stepsInHigh = elm["stepsInHigh"]
						else: stepsInHigh = 0
						if "stepsInLow" in list(elm.keys()): stepsInLow = elm["stepsInLow"]
						else: stepsInLow = 0

						resp = vars.dmxComm.sendCommand(f"channels getChannel universe'{elm['universe']}' addr='{elm['address']}'")
						if (elm["universe"],elm["address"]) not in savedAddr:
							savedAddr.append((elm["universe"],elm["address"]))
							usedAddr.append((elm["universe"],elm["address"],resp.split("_")[3:]))
						vars.dmxComm.sendCommand(f"effect new type='{type}' name='{id}' universe='{elm['universe']}' addr='{elm['address']}' start='{start}' end='{end}' speed='{speed}' stepsInHigh='{stepsInHigh}' stepsInLow='{stepsInLow}'")
						#			   effect new type='sin' universe='0' addr='1' start='0' end='255' name='Test1' stepsInHigh='10' stepsInLow='15' speed='75'

					elif "setfx" in list(elm.keys()):
						type = elm["setfx"]
						id = elm["fxid"]
						addr = elm["address"]
						universe = elm["universe"]
						value = elm["value"]

						resp = vars.dmxComm.sendCommand(f"channels getChannel universe='{universe}' addr='{addr}'")
						if (id,addr) not in savedAddr:
							savedAddr.append((universe,addr))
							usedAddr.append((universe,addr,resp.split("_")[3:]))
						resp = vars.dmxComm.sendCommand(f"effect getState type='{type}' universe='{universe}' addr='{addr}' name='{id}'")
						if len(resp.split(":")) > 1 and resp.split(":")[1] == bool(value): pass
						else:
							vars.dmxComm.sendCommand(f"effect trigger type='{type}' name='{id}' universe='{universe}' addr='{addr}'")
					else: pass

					if vars.threadStop.is_set() or vars.dmxcnf.cuelst_stop[f"cuelist{_id}"].is_set(): break
				if vars.threadStop.is_set() or vars.dmxcnf.cuelst_stop[f"cuelist{_id}"].is_set(): break
				ind += 1
				if ind == len(cues): ind = 0
				time.sleep(cues[ind]["wait"]/1000)
		else: #Will execute the cuelist one time, then reset the values of the DMX channels
			for i in range(len(cues)):
				for elm in cues[i]["events"]:
					try: uni = elm["universe"]
					except KeyError: elm["universe"] = "0"

					if "level" in list(elm.keys()):
						if (elm["universe"],elm["address"]) not in savedAddr:
							resp = vars.dmxComm.sendCommand(f"channels getChannel universe='{elm['universe']}' addr='{elm['address']}'")
							savedAddr.append((elm["universe"],elm["address"]))
							usedAddr.append((elm["universe"],elm["address"],resp.split("_")[3:]))
						vars.dmxComm.sendCommand(f"channels setChannel universe='{elm['universe']}' addr='{elm['address']}' setto='{elm['level']}'",expectResponse=False)

					elif "newfx" in list(elm.keys()): #if event is a effect creation event
						type = elm["newfx"]
						id = elm["fxid"]
						start = elm["start"]
						end = elm["end"]
						speed = elm["speed"]
						if "stepsInHigh" in list(elm.keys()): stepsInHigh = elm["stepsInHigh"]
						else: stepsInHigh = 0
						if "stepsInLow" in list(elm.keys()): stepsInLow = elm["stepsInLow"]
						else: stepsInLow = 0

						resp = vars.dmxComm.sendCommand(f"channels getChannel universe'{elm['universe']}' addr='{elm['address']}'")
						if (elm["universe"],elm["address"]) not in savedAddr:
							savedAddr.append((elm["universe"],elm["address"]))
							usedAddr.append((elm["universe"],elm["address"],resp.split("_")[3:]))
						vars.dmxComm.sendCommand(f"effect new type='{type}' name='{id}' universe='{elm['universe']}' addr='{elm['address']}' start='{start}' end='{end}' speed='{speed}' stepsInHigh='{stepsInHigh}' stepsInLow='{stepsInLow}'")

					elif "setfx" in list(elm.keys()):
						type = elm["setfx"]
						id = elm["fxid"]
						addr = elm["address"]
						universe = elm["universe"]
						value = elm["value"]

						resp = vars.dmxComm.sendCommand(f"channels getChannel universe='{universe}' addr='{addr}'")
						if (id,addr) not in savedAddr:
							savedAddr.append((universe,addr))
							usedAddr.append((universe,addr,resp.split("_")[3:]))
						resp = vars.dmxComm.sendCommand(f"effect getState type='{type}' universe='{universe}' addr='{addr}' name='{id}'")
						if len(resp.split(":")) > 1 and resp.split(":")[1] == bool(value): pass
						else:
							vars.dmxComm.sendCommand(f"effect trigger type='{type}' name='{id}' universe='{universe}' addr='{addr}'")
					else: pass

					if vars.threadStop.is_set() or vars.dmxcnf.cuelst_stop[f"cuelist{_id}"].is_set(): break
				if vars.threadStop.is_set() or vars.dmxcnf.cuelst_stop[f"cuelist{_id}"].is_set(): break
				time.sleep(cues[i]["wait"]/1000)

		log(cFN(),"info",f"Trying to reset changed values to source value...")
		for elm in usedAddr:
			log(cFN(),"debug",f"Trying to reset changed value of [U:{elm[0]} A:{elm[1]}] to 0")
			vars.dmxComm.sendCommand(f"channels setChannel universe='{elm[0]}' addr='{elm[1]}' setto='0'")
			#log(cFN(),"debug",f"Trying to reset changed value of [U:{elm[0]} A:{elm[1]}] to {elm[2][0]}")
			#vars.dmxComm.sendCommand(f"channels setChannel universe='{elm[0]}' addr='{elm[1]}' setto='{elm[2][0]}'")

class windowHandler(jsonWin):
	"""
	This class controls every Action etc. in the GUI. Every new method should be placed in the "commands" class
	to keep the overview.
	On the other hand this class uses the jsonWin class, so that the GUI can be loaded and controlled that way.
	See jsonWin.py for details.
	"""

	class commands():
		def test1():
			winlog("pass","Test one passed",cFN())

		def test2():
			winlog("pass","Test two passed","test2")

		class fxgen():
			def chooseFX(type:str):
				if type not in ("sin","cos","fade","shutter"):
					winlog("err",f"Type of FX has to be 'sin'/'cos'/'fade'/'shutter', not '{type}'",cFN())
					return

				winlog("debug",f"Storing choice of FX type for FX generation: '{type}'",cFN())
				vars.win.fxgen.choice = type

		class createFixt(): #Functions for fixture creation
			def loadPage(): #Displays the fixture creation page
				winlog("info","Loading page to create new fixture",cFN())
				vars.winManager.unassignElements("root")
				vars.winManager.assignElement("MenuFrm")
				vars.winManager.assignElement("CmdPromptFrm")
				vars.winManager.assignElement("CreateFixtureFrm")
				winlog("ok","Page loaded",cFN())

			def storeNewFixture(): #Stores the new fixture
				#winlog("warn","Storing new fixture is currently disabled. Skipping...",cFN())
				#return

				winlog("info","Loading values of new fixture...",cFN())
				name = vars.winManager.getState("CreateFixtNameEnt")
				address = vars.winManager.getState("CreateFixtStartaddrEnt")
				channelAmt = vars.winManager.getState("CreateFixtChannelsEnt")
				channels = vars.winManager.getState("CreateFixtChannelTypeEnt").split(";")
				stackAmt = int(vars.winManager.getState("CreateFixtStackSld"))
				winlog("ok",f"Values of new fixture with name '{name}' loaded",cFN())

				winlog("info","Generating more specific values for new fixture",cFN())
				type = ""
				for elm in channels.split(";"):
					if elm in ["dim","red","green","blue","yellow","cyan","magenta","white","pan","tilt"]:
						type = type + elm[0]
					else:
						winlog("err",f"Invailid channel type while configuring new fixture: '{elm}'",cFN())
						mdSetMessage(f"Chan:{elm}")
						return

				channelCnf = []
				for elm in channels.split(";"):
					channelCnf.append({"type": elm, "start": 0})
				winlog("ok","Important values generated successfully",cFN())

				winlog("info","Storing new fixture...",cFN())
				vars.dmxcnf.fixt.append({"address": address, "name": name, "type": type, "channelNum": len(channels.split(";")), "channels": channelCnf})
				winlog("ok","New fixture saved",cFN())

			def stackAmtChange(level:float):
				vars.winManager.configureElement("CreateFixtStackAmtLbl",text=str(int(level)))
				vars.winManager.windowUpdate("win1")

		class cuelist(): #Control for cuelists
			def trigger(id:int): #Triggers the state of a cuelist
				winlog("info",f"Request for triggering Cuelist '{id}' recieved from GUI",cFN())
				vars.dmxcnf.cuelst[f"cuelist{id}"]["active"] = not vars.dmxcnf.cuelst[f"cuelist{id}"]["active"]
				cl = vars.dmxcnf.cuelst[f"cuelist{id}"]
				isActive = cl["active"]
				if isActive:
					vars.winManager.configureElement(f"MainPageCues/{id}",border_color="#00FF00") #Changes the color of the corresponding button
					mdSetMessage(text=vars.shows[vars.config["general"]["activeShow"]]["cues"][f"cuelist{id}"]["name"],state=True)
					winlog("info",f"Starting cuelist with ID {id} in new thread",cFN())
					vars.dmxcnf.cuelst_stop[f"cuelist{id}"] = threadEvent()
					try:
						vars.dmxcnf.cuelst_thr[f"cuelist{id}"] = Thread(target=dmx.runCuelist,args=[int(id)])
						vars.dmxcnf.cuelst_thr[f"cuelist{id}"].start()
					except Exception as exc:
						winlog("fatal",f"Could not start cuelist {id} in new thread: {exc}",cFN())
						return
				else:
					vars.winManager.configureElement(f"MainPageCues/{id}",border_color="#FD8B00") #Changes the color of the corresponding button
					mdSetMessage(text=vars.shows[vars.config["general"]["activeShow"]]["cues"][f"cuelist{id}"]["name"],state=False)
					vars.dmxcnf.cuelst_stop[f"cuelist{id}"].set()
					winlog("info","Set stop value for cuelist",cFN())
				vars.winManager.windowUpdate("win1")

				winlog("ok","Cuelist triggered",cFN())

		def sendCmd(): #Sends the command from the command line when the user hits <Return> in the Entry field or clicks the "send" button
			#winlog("warn","Sending user entered commands is currently disabled. Skipping...",cFN())
			#return

			winlog("info","Trying to execute command user entered",cFN())
			#Puts the command at the top of the Command history Textbox
			_cmd = vars.winManager.getState("CmdPromptEnt")
			vars.winManager.configureElement("CmdHistoryTB",state="normal")
			vars.winManager.insertElement("CmdHistoryTB","0.0","> "+_cmd+"\n")
			vars.winManager.configureElement("CmdHistoryTB",state="disabled")
			vars.winManager.windowUpdate("CmdHistoryTB")
			vars.winManager.windowUpdate("win1")
			winlog("debug",f"Command: \"{_cmd}\"",cFN())
			if _cmd not in ("halt","stop","quit","shutdown","help","exit","clear","cls"):
				#Send command to the dmxServer
				resp = vars.dmxComm.sendCommand(_cmd,expectResponse=False if _cmd.split()[0] == "!noreply" else True)
				if _cmd.split()[0] != "!noreply": winlog("debug",f"Response from server: {resp}")
				resp = resp.split()
				if _cmd.split()[0] != "!noreply":
					#Writes the returned data from server into the command history box
					vars.winManager.configureElement("CmdHistoryTB",state="normal")
					vars.winManager.insertElement("CmdHistoryTB","1.0",f"[{resp[0]}] {resp[1]}\n")
					vars.winManager.configureElement("CmdHistoryTB",state="disabled")
					vars.winManager.windowUpdate("CmdHistoryTB")
					vars.winManager.windowUpdate("win1")
				vars.winManager.deleteTextFromEntry("CmdPromptEnt",0,tk.END) #Clear the Entry for commands
			elif _cmd in ("clear","cls"):
				vars.winManager.deleteTextFromEntry("CmdHistoryTB",0,tk.END) #Clear the output
			elif _cmd in ("help"):
				#Output a help to the Commands (read from dmxServer.help.txt)
				with open("dmxServer.help.txt","r") as fle: help = ''.join(fle.readlines())
				help = "HELP\n---------------\n"+help
				vars.winManager.configureElement("CmdHistoryTB",state="normal")
				vars.winManager.insertElement("CmdHistoryTB","1.0",help+"\n")
				vars.winManager.configureElement("CmdHistoryTB",state="disabled")
				vars.winManager.windowUpdate("CmdHistoryTB")
				vars.winManager.windowUpdate("win1")
				vars.winManager.deleteTextFromEntry("CmdPromptEnt",0,tk.END)
			else:
				#If the command is in "halt","stop","quit","shutdown","exit", the Program will be stopped
				vars.winManager.commands.quit()
			winlog("ok","Command executed",cFN())

		def loadPage(id:str): #Loads a page
			winlog("info",f"Loading page '{id}'...","loadPage")
			vars.winManager.unassignElements("root")
			vars.winManager.assignElement("MenuFrm")
			vars.winManager.assignElement("CmdPromptFrm")
			vars.winManager.assignElement(id+"Frm")
			winlog("okay",f"Loaded page '{id}'","loadPage")
			#winlog("debug","Replacing Window...","commands.loadPage")
			#vars.winManager.windowCenter("win1")

			vars.winManager.windowUpdate("win1")

		def fixtConfCall(id:int): #Function for Fixture configuration
			#winlog("warn",f"Loading GUI for Fixture ({id}) is currently disabled",cFN())
			#return

			winlog("info",f"Configuring and loading GUI for Fixture configuration of Fixture {id}...",cFN())
			vars.winManager.configureElement("fixtConfigNameLbl",text=vars.dmxcnf.fixt[id]["name"])
			enttxt = vars.dmxcnf.fixt[id]["address"]
			winlog("ok","Configured GUI for fixture configuration...",cFN())

			vars.winManager.configureElement("fixtConfigStartaddrEnt",placeholder_text=enttxt)
			vars.winManager.unassignElements("root")
			vars.winManager.assignElement("MenuFrm")
			vars.winManager.assignElement("CmdPromptFrm")
			vars.winManager.assignElement("fixtConfigFrm")
			winlog("ok",f"Loaded GUI for fixture configuration",cFN())

			winlog("debug","Storing information of currently editing fixture in vars class",cFN())
			vars.editFixt = id

		class fixtEdit():
			def saveChanges(): #Save the changes of Fixture Edit
				editFixt = vars.editFixt
				winlog("ok",f"Loaded id of currently edited fixture ({editFixt})",cFN())

				#winlog("warn","Saving fixtures is currently not enabled. Skipping...",cFN())
				#return

				winlog("info","Loading states of elements in window...",cFN())
				fixtAddr = vars.winManager.getState("fixtConfigStartaddrEnt")
				fixtAddr = fixtAddr if fixtAddr not in (None,"") else vars.winManager.cgetState("fixtConfigStartaddrEnt","placeholder_text")
				winlog("ok","States loaded",cFN())

				winlog("info","Saving fixture data...",cFN())
				vars.dmxcnf.fixt[editFixt]["address"] = fixtAddr
				winlog("ok","Saved fixture data",cFN())

		class settings():
			def cnfMdBrightLbl(level:int): #Write the current MatrixDisplay Brightness into the label
				vars.winManager.configureElement("SettingsMdBrightLbl",text=str(int(level)))
				vars.winManager.windowUpdate("win1")

			def saveChanges():
				winlog("info","Saving settings...",cFN())
				#setting for current show (load another show when program is launched again)
				try:
					cS = vars.winManager.getState("SettingsCurrentShowOMne")
					cS = cS if cS not in ("no shows available","") else vars.config["general"]["activeShow"]
					vars.config["general"]["activeShow"] = cS
				except Exception as exc:
					winlog("err",f"Could not save the show which should be started at next startup: {exc}",cFN())

				#setting for brightness of matrix display
				try:
					vars.config["general"]["mdBrightness"] = int(vars.winManager.getState("SettingsMdBrightSld"))
				except Exception as exc:
					winlog("err",f"Could not get Value for matrix display brightness due to the following exception: {exc}",cFN())

				#setting for alert timeout on matrix display
				try:
					try: mMAV = int(vars.winManager.getState("SettingsMdAlertTimeEnt"))
					except: mMAV = int(vars.winManager.cgetState("SettingsMdAlertTimeEnt","placeholder_text"))
					vars.config["general"]["maxMatrixAlertView"] = mMAV
				except Exception as exc:
					winlog("err",f"Could not get value of alert timeout for matrix display: {exc}",cFN())

				#setting for hiding progressbar window
				try:
					sPBW = bool(vars.winManager.getState("SettingsEnableProgressWinSwt"))
					vars.config["general"]["showProgressWin"] = sPBW
				except Exception as exc:
					winlog("err",f"Could not get value if progressbar window should be shown: {exc}",cFN())

				#setting for saving showfile
				try:
					activeShow = "shows/"+vars.winManager.getState("SettingsSaveShowEnt")+".json"
					activeShow = activeShow if activeShow not in (""," ","\n","\t","shows/.json") else vars.config["general"]["activeShow"] #Will allow changing the showfile if the text isn't weired
					if activeShow != vars.config["general"]["activeShow"] and activeShow not in vars.config["general"]["createdShows"]:
						vars.config["general"]["createdShows"].append(activeShow)
					if cS not in ("no shows available","") and activeShow not in (""," ","\n","\t","shows/.json"):
						baC = vars.config["general"]["activeShow"]
						vars.config["general"]["activeShow"] = activeShow
						vars.shows[activeShow] = dc(vars.shows[baC])
						with open(activeShow,"w+") as fle: fle.write("{}")
						saveShow()
						vars.config["general"]["activeShow"] = baC
					mdSetMessage(text="Sve Show...",state=True)
					saveShow()
					mdSetMessage(text="Show sve dne",state=True)
				except Exception as exc:
					winlog("err",f"Failed to save show settings in showfile: {exc}",cFN())

				try: saveConfig()
				except Exception as exc: winlog("err",f"Failed to save configuration file: {exc}",cFN())

				winlog("ok","Settings saved",cFN())

		"""def loadFaderPage():
			winlog("info","Loading Faderpage...","loadFaderPage")
			vars.winManager.unassignElements("root")
			vars.winManager.assignElement("MenuFrm")
			vars.winManager.assignElement("FaderPageFrm")
			winlog("okay","Loaded Faderpage","loadFaderPage")
			winlog("debug","Replacing Window...")
			#vars.winManager.windowCenter("win1")

			vars.winManager.windowUpdate("win1")"""

		def executeCuelist(id:int): #Starts a cuelist
			winlog("info",f"Request for executing Cuelist '{id}' recieved from GUI","commands.executeCuelist")

			aSN = vars.config["general"]["activeShow"] #Name of active Show
			vars.shows[aSN]["cues"][f"cuelist{id}"]["active"] = not vars.shows[aSN]["cues"][f"cuelist{id}"]["active"]
			if vars.shows[aSN]["cues"][f"cuelist{id}"]["active"]:
				vars.winManager.configureElement(f"MainPageCues/{id}",border_color='#00FF00')
				mdSetMessage(text=vars.shows[aSN]["cues"][f"cuelist{id}"]["name"],state=True)
			else:
				vars.winManager.configureElement(f"MainPageCues/{id}",border_color='#FD8B00')
				mdSetMessage(text=vars.shows[aSN]["cues"][f"cuelist{id}"]["name"],state=False)
			vars.winManager.windowUpdate("win1")

			winlog("ok",f"Started Cuelist '{id}'","executeCuelist")

		def executeMacro(id:int): #Executes a macro, currently only displayed but nothing gets really executed
			winlog("info",f"Request for executing Macro '{id}' recieved from GUI","executeMacro")

			aSN = vars.config["general"]["activeShow"] #Name of active Show
			vars.shows[aSN]["macros"][f"macro{id}"]["active"] = not vars.shows[aSN]["macros"][f"macro{id}"]["active"]
			if vars.shows[aSN]["macros"][f"macro{id}"]["active"]:
				vars.winManager.configureElement(f"MainPageMacros/{id}",border_color='#00FF00')
				mdSetMessage(text=vars.shows[aSN]["macros"][f"macro{id}"]["name"],state=True)
			else:
				vars.winManager.configureElement(f"MainPageMacros/{id}",border_color='#FD8B00')
				mdSetMessage(text=vars.shows[aSN]["macros"][f"macro{id}"]["name"],state=False)
			vars.winManager.windowUpdate("win1")

			winlog("ok",f"Toggled state of Macro '{id}'","executeMacro")

		def editFixture(id:int):
			winlog("info",f"Request for editing Fixture '{id}' recieved from GUI","editFixture")

			winlog("ok",f"Finished editing Fixture '{id}'","editFixture")

		def highlightDmxAddr(addr:int): #Sets the entered address to 255
			winlog("info",f"Request to toggle highlight of DMX address {addr+1}","highlightDmxAddr")
			resp = vars.dmxComm.sendCommand(f"channels getChannel universe='0' addr='{addr+1}'")
			if not resp:
				winlog("err","Response not given",cFN())
				return
			try:
				if resp[0]: pass
			except TypeError as exc:
				winlog("err","Response has invailid type: {exc}",cFN())
				return
			if resp[0] == "OK": state = resp[1].split("_")[3]
			elif resp[0] == "ERR":
				winlog("err",f"Could not get state of dmx address: Server responded with error: {resp[1]}",cFN())
				return
			else:
				winlog("err",f"Could not surely get state of dmx address: Server responded in unexpected format: {resp}",cFN())
				return
			resp = vars.dmxComm.sendCommand(f"channels setChannel universe='0' addr='{addr+1}' setto='{'255' if state == '0' else '0'}'")
			if resp[0] == "OK":
				winlog("ok","toggled highlight of dmx channel")
				return
			elif resp[0] == "ERR":
				winlog("err",f"Could not trigger highlight of dmx address: Server responded with error: {resp[1]}",cFN())
				return
			else:
				winlog("err",f"Could not trigger surely highlight of dmx address: Server responded in unexpected format: {resp}",cFN())

		def quit(): #Quits the application
			winlog("warn","Exiting program due to user request",cFN())
			vars.started = False
			if vars.enablePixelDisp: #Clears the matrix display if it was enabled, then writes "exiting" to inform the user
				vars.pixelDisp.clearDisp()
				vars.pixelDisp.generateText(text="exiting",font_size=vars.mdFontSize,text_color=(255,0,0),directDraw=True,font=vars.mdFont)
			saveShow() #Save the showfile
			vars.dmxComm.sendCommand("!noreply channels allOff",expectResponse=False) #Turns of every channel, without expecting a response (!noreply)
			time.sleep(0.5)
			vars.dmxComm.sendCommand("!noreply render stop",expectResponse=False) #Stops the dmxServer Render loop
			vars.winManager.windowDestroy("win1") #Destroys the window
			if vars.enablePixelDisp: vars.mdQuit = True
			if vars.enablePixelDisp: vars.pixelDisp.quit() #Really quits the matrix display
			#raise exceptions.ExitRequest("User requested to quit program")

def log(source:str,tpe:str,msg:str,errtpe="normal"):
	if tpe in ("err","error","fatal"): vars.errcnt += 1
	color = FE["cyan"] if tpe in ("info","inf") else FE["blue"] if tpe == "debug" else FE["green"] if tpe in ("okay","ok","done","pass") else FE["yellow"] if tpe == "warn" or (tpe in ("err","error") and errtpe == "normal") else FE["red"] if tpe in ("fatal","err","error") else ''
	if vars.debug == True:
		print(color+f"[PyDMX/{source}] [{tpe.upper()}] {msg}"+FE["reset"])
		if vars.enableLogFile: logfile(f"PyDMX/{source}",f"[{tpe.upper()}] {msg}")
	elif vars.debug == True and tpe != "debug":
		print(color+f"[PyDMX/{source}] [{tpe.upper()}] {msg}"+FE["reset"])
		if vars.enableLogFile: logfile(f"PyDMX/{source}",f"[{tpe.upper()}] {msg}")

	if vars.enablePixelDisp and not vars.started and not vars.mdQuit: #The Log messages will also be outputted on the matrix display if the GUI is not fully built
		pclr = (0,30,30) if tpe in ("info","inf") else (0,0,30) if tpe == "debug" else (5,30,0) if tpe in ("okay","ok","done","pass") else (30,30,0) if tpe == "warn" or (tpe in ("err","error") and errtpe == "normal") else (30,5,0) if tpe in ("fatal","err","error") else "IMP"
		try: vars.pixelDisp.generateMultiLineText(text='\n'.join(msg.split()),font=vars.mdFont,font_size=vars.mdFontSize,no_log=True,text_color=(0,0,0) if pclr != "IMP" else (255,255,255),bg_color=pclr if pclr != "IMP" else (0,0,0))
		except AttributeError: pass

def errStopCtrl(): #Stopps the Application if to many errors occured
	while not vars.threadStop.is_set():
		if vars.errcnt == vars.maxerr+1: raise exceptions.criticalException(f"More than {vars.maxerr} errors raised in PyDMX")

def getScreenSize(): #Gets the screensize
	log(cFN(),"info","Loading screensize...")
	try:
		log(cFN(),"debug","Creating example window to load windowsize with")
		test = CTk()
		test.title("Starting...")
		log(cFN(),"debug","Loaded example window")
		_return = {}
		try:
			log(cFN(),"debug","Trying to load screensize...")
			_return["height"] = test.winfo_screenheight()
			_return["width"] = test.winfo_screenwidth()
			log(cFN(),"debug","Done")
		except Exception as exc:
			log(cFN(),"err",f"Error while loading screensize (could mean destroyed windowmanager): {exc} - returning screensize of 1000x1000")
			_return["height"] = 1000
			_return["width"] = 1000
		log(cFN(),"debug","Destroying example window")
		test.destroy()
		print("",end="")
		print("",end="")
		log(cFN(),"ok","Loaded screensize")
		return _return
	except:
		#log(cFN(),"warn","getScreenSize only works for CTk Framework, not Qt (You can ignore this message)")
		log(cFN(),"debug","Loading screensize with Qt")
		output = subprocess.check_output('xrandr | grep "*" | cut -d" " -f4', shell=True)
		resolution = output.decode().strip().split('x')
		width, height = int(resolution[0]), int(resolution[1])
		_return = {"width":width,"height":height}
		log(cFN(),"ok","Loaded screensize")
		return _return

def start():
	log(cFN(),"info","Loading and initializing PyDMX...")

	log(cFN(),"debug","Starting errStopCtrl() in additional Thread")
	eSC_thr = Thread(target=errStopCtrl) #Starts the error stop control
	eSC_thr.deamon = True #Thread will stop after program halt
	eSC_thr.start()

	log(cFN(),"info","Loading config from file 'config.json'...")
	vars.debug = loadcnf("config.json")["general"]["debug"] #Loads the configured debug value
	vars.config = loadcnf("config.json") #Loads the hole config file
	log(cFN(),"ok","Loaded config")

	try: vars.enablePixelDisp = vars.config["general"]["enableMd"] #Checks if the matrix display is enabled
	except KeyError:
		log(cFN(),"debug","Outdated config.json: Could not find general setting enableMd. Correcting mistake for runtime (Program needs to be correctly closed from GUI to fix problem in config.json)")
		vars.config["general"]["enableMd"] = True
		vars.enablePixelDisp = True

	if vars.enablePixelDisp:
		try:
			log(cFN(),"info","Loading driver for 64x32 RGB matrix display...")
			#Initialize matrix Display
			vars.pixelDisp = matrixDisplay(debug=vars.debug,masterMod="PyDMX",forceReplace=vars.config["general"]["simulateMatrix"],brightness=vars.config["general"]["mdBrightness"])
			log(cFN(),"ok","Loaded driver for 64x32 RGB matrix display")
		except Exception as exc:
			log(cFN(),"err",f"Failed to load driver for matrixDisplay: {exc}")
			log(cFN(),"warn","Changing vars.enablePixelDisp to False")
			vars.enablePixelDisp = False #If there was an error initializing the MD, it will simply be disabled
	else: log(cFN(),"warn","Pixel Display is not enabled, warning will not show again")

	if vars.enablePixelDisp:
		try:
			log(cFN(),"debug","Trying to show text 'loading' on pixel display")
			vars.pixelDisp.generateText(text="loading",font_size=vars.mdFontSize,text_color=(255,0,0),directDraw=True,font=vars.mdFont)
		except Exception as exc:
			log(cFN(),"err",f"Failed to Display text on matrixDisplay: {exc}")
			log(cFN(),"warn","Changing vars.enablePixelDisp to False")
			vars.enablePixelDisp = False

	log(cFN(),"debug","Trying to get screen size...")
	try: vars.screenSize = getScreenSize()
	except Exception as exc:
		log(cFN(),"fatal",f"Error while loading screensize, meaning broken / unaccessible library customtkinter")
		raise exceptions.criticalException(str(exc))

	log(cFN(),"info","Loading shows...")
	vars.shows = {}
	for elm in vars.config["general"]["createdShows"]: #Loads the configuration of every showfile
		vars.shows[elm] = loadcnf(elm)
	log(cFN(),"done","Loaded shows")

	#Initialize GUI
	log(cFN(),"info","Loading window...")
	activeShowData = vars.shows[vars.config["general"]["activeShow"]]
	vars.dmxcnf.fixt = activeShowData["patch"]["fixtures"]
	vars.dmxcnf.macro = activeShowData["macros"]
	vars.dmxcnf.cuelst = activeShowData["cues"]
	try:
		#Start the window manager
		try: vars.winManager = windowHandler(stack={"cues":{"times":min(len(activeShowData["cues"]),20),"maxColumnCopy":5},"macros":{"times":min(len(activeShowData["macros"]),10),"maxColumnCopy":20},"fixtureConfig":{"times":len(vars.dmxcnf.fixt),"maxColumnCopy":int((vars.screenSize["width"]-50)/66)}})
		except Exception as exc:
			log(cFN(),"err",f"Failed to load window manager in first execution: {exc}")
			raise exceptions.ValueDefError(f"Failed to load window manager: {exc}") from exc
		log(cFN(),"debug","Loading main elements...")
		#Gives the list of elements to the winManager (read from config.json)
		vars.winManager.loadElmDict(vars.config["window"]["elements"])
		log(cFN(),"debug","Loading generator Frames and widgets from generatorFrames.json")
		#Also adds the widgets from generatorFrames.json
		vars.winManager.addFile("generatorFrames.json")
		#Verifies GUI widgets
		vars.winManager.verifyElements()
	except Exception as exc:
		log(cFN(),"fatal",f"Failed to load window manager in general: {exc}")
		raise exceptions.ValueDefError(f"Failed to load window manager: {exc}")
	log(cFN(),"ok","Loaded window manager")

	#Binds the sendCommand function to the command prompt entry so that the user can simply press <Return> to send the command
	log(cFN(),"debug","Binding key <Return> on element 'CmdPromptEnt' to ensure command sending after pressing <Return>")
	vars.winManager.getElementClass("CmdPromptEnt").bind("<Return>", lambda event: vars.winManager.commands.sendCmd())
	log(cFN(),"debug","Bound key successfully to element")

	"""
	log(cFN(),"info","Loading generator window frames")
	try:
		try: vars.genWinManager = generatorWindowHandler()
		except Exception as exc:
			log(cFN(),"err",f"Failed to load additional window manager for generator frames in first execution: {exc}")
			raise exceptions.ValueDefError(f"Failed to load additional window manager (generator frames): {exc}") from exc
		vars.genWinManager.loadFile("generatorFrames.json")
		vars.genWinManager.addElement(vars.winManager.extractElementData("win1"))
		vars.genWinManager.verifyElements()
		vars.winManager.addElementDataList(vars.winManager.getElementDataList())
	except Exception as exc:
		log(cFN(),"fatal",f"Failed to load additional window manager for generator frames in mainwindow: {exc}")
		raise exceptions.ValueDefError(f"Failed to load additional window manager (generator frames): {exc}")
	log(cFN(),"ok","Loaded generator window frames...")

	log(cFN(),"info","Extending main window manager with generator frames...")
	try:
		vars.winManager.addElementDataList(vars.winManager.getElementDataList())
	except Exception as exc:
		log(cFN(),"fatal",f"Failed to extend main window manager with generator frames: {exc}")
		raise exceptions.ValueDefError(f"Failed to extend main window manager with generator frames: {exc}")
	log(cFN(),"ok","Extended main window manager with generator frames")"""

	#if OLA is enabled, initialize the PyDMX controller
	if vars.enableOLA == True:
		log(cFN(),"info","Loading ola DMX controller...")
		vars.dp = PyDMX(universes=vars.config["olaTerminal"]["universes"],debug=vars.debug,mainApp="PyDMX")
		log(cFN(),"done","Loaded ola DMX controller")
	else: log(cFN(),"warn","ola DMX controller will not be started due to massive test on other software, so it is not usable")

	#Start the dmx server in a thread
	if vars.config["communication"]["server"]:
		log(cFN(),"info","Starting main DMX server in new thread...")
		vars.dmxServ = dmxServer(vars.dp,ip=vars.config["communication"]["ip"],port=vars.config["communication"]["port"])
		vars.dmxServThread = Thread(target=vars.dmxServ.startServer)
		vars.dmxServThread.deamon = True
		vars.dmxServThread.start()
		log(cFN(),"ok","Main DMX server started...")
	else: log(cFN(),"ok","Passing DMX server configuration because server is not enabled by settings")

	#Initialize the connection with the dmx server
	log(cFN(),"info","Initializing communication client for DMX commands...")
	vars.dmxComm = dmxClient(master="PyDMX",ip=vars.config["communication"]["ip"],port=vars.config["communication"]["port"])
	log(cFN(),"ok","Communication client for DMX commands initialized")
	log(cFN(),"info","Connecting to dmx communication server...")
	try:
		#connect to the dmx server
		vars.dmxComm.connect()
		log(cFN(),"ok","Connected")
	except Exception as exc:
		log(cFN(),"err",f"Failed to connect to DMX communication server: {exc}")

	log(cFN(),"info","Reloading dmxServer help file for commands...")
	try:
		#Reload the command help list of the dmxServer
		dmxServerRHF()
		log(cFN(),"ok","dmxServer help file reloaded")
	except Exception as exc:
		log(cFN(),"err",f"Failed to reload help file for dmxServer: {exc}")

	log(cFN(),"done","Loaded and initialized PyDMX successfully...")

	main()

def pixelDispLoadDust(): #Load the default image for the MD
	if vars.enablePixelDisp:
		vars.pixelDisp.generateImage(filepath="resources/matrixDisplay-icon.jpg",size=(32,32),startAt=(16,0),directDraw=True)

def main():
	configureElements()

	vars.started = True #Disables the Loglines on the MD
	if vars.enablePixelDisp:
		log(cFN(),"debug","Clearing RGB matrix display and displaying main image...")
		vars.pixelDisp.clearDisp()
		pixelDispLoadDust()
		log(cFN(),"debug","Prepeared RGB matrix display")
	vars.load = False

	#Shows the main page
	log(cFN(),"info","Rendering mainframe in window...")
	vars.winManager.assignAll()
	vars.winManager.unassignElements("root")
	vars.winManager.assignElement("MenuFrm")
	vars.winManager.assignElement("CmdPromptFrm")
	vars.winManager.assignElement("MainPageFrm")
	log(cFN(),"ok","Successfully rendered mainframe in window...")

	#log(cFN(),"debug",f"jsonWin found elements: {vars.winManager.elements}")
	if vars.debug and vars.debugElements: #Will write every widget config into the logfile, if vars.debugElements is set
		print("--------")
		with open(".log","a") as fle: fle.write("--------\n")
		log(cFN(),"debug","jsonWin founded/verified elements:")
		with open(".log","a") as fle: fle.write('\n'.join(vars.winManager.getElements())+"\n")
		with open(".log","a") as fle: fle.write("--------\n")
		print("--------")

	#Start the dmx render loop
	log(cFN(),"info","Starting dmx render mainloop...")
	vars.dmxComm.sendCommand("render startLoop")
	log(cFN(),"ok","DMX renderloop started")

	#Start the mainloop of the window
	log(cFN(),"info","Starting window mainloop...")
	vars.winManager.getElementClass("win1").title(f"PyDMX Controller ({vars.config['general']['activeShow']})")
	vars.winManager.windowMainloop("win1")
	log(cFN(),"info","window mainloop ended, storing show and exiting...")
	saveShow()
	saveConfig()
	log(cFN(),"info","Exiting PyDMX...")

def saveShow(): #Save the current show data into the show file
	log(cFN(),"info",f"Saving active show '{vars.config['general']['activeShow']}'...")
	try:
		savecnf(vars.config["general"]["activeShow"],vars.shows[vars.config["general"]["activeShow"]])
		log(cFN(),"ok","Saved show")
	except Exception as exc:
		log(cFN(),"err",f"Could not save show: {exc}","errHandlingNonNormal")

def saveConfig(): #Save the current config data into the show file
	log(cFN(),"info","Saving configuration...")
	try:
		savecnf("config.json",vars.config)
		log(cFN(),"ok","Saved config")
	except Exception as exc:
		log(cFN(),"err",f"Could not save config: {exc}","errHandlingNonNormal")
	log(cFN(),"info","Correcting config.json window elements")
	try: _correctconfig()
	except Exception as exc:
		log(cFN(),"warn",f"Could not correct config.json window elements: {exc}")
		return
	log(cFN(),"ok","config.json window elements corrected")

def configureElements(): #Configure the settings of widgets, which can not be set in the JSON configuration
	log(cFN(),"info","Configuring element specific settings...")

	vars.winManager.configureElement("CmdPromptFrm",width=vars.winManager.getScreenSize("win1")["width"]-200,height=190)
	vars.winManager.configureElement("CmdHistoryTB",width=vars.winManager.getScreenSize("win1")["width"]-200,height=110)
	vars.winManager.configureElement("fxEditFrm",width=vars.winManager.getScreenSize("win1")["width"]-200,height=400)
	vars.winManager.configureElement("fxOptionsEditorSFrm",width=vars.winManager.getScreenSize("win1")["width"]-220)
	vars.winManager.configureElement("MainPageMacroFrm",width=vars.winManager.getScreenSize("win1")["width"]-200)
	vars.winManager.configureElement("MainPageCuelistFrm",width=vars.winManager.getScreenSize("win1")["width"]-200)
	vars.winManager.configureElement("MainPageFixtureFrm",width=vars.winManager.getScreenSize("win1")["width"]-200,height=vars.winManager.getScreenSize("win1")["height"]-700)
	vars.winManager.configureElement("FixturesFrm",width=vars.winManager.getScreenSize("win1")["width"]-60,height=vars.winManager.getScreenSize("win1")["width"]-300)
	vars.winManager.configureElement("SettingsStgFrm",width=vars.winManager.getScreenSize("win1")["width"]-200,height=vars.winManager.getScreenSize("win1")["height"]-400)
	vars.winManager.configureElement("SettingsCurrentShowOMne",values=vars.config["general"]["createdShows"])
	vars.winManager.configureElement("SettingsMdBrightLbl",text=str(vars.config["general"]["mdBrightness"]))
	vars.winManager.getElementClass("SettingsMdBrightSld").set(vars.config["general"]["mdBrightness"])
	vars.winManager.configureElement("SettingsMdAlertTimeEnt",placeholder_text=str(vars.config["general"]["maxMatrixAlertView"]))
	if "showProgressWin" in list(vars.config["general"].keys()):
		if vars.config["general"]["showProgressWin"] == True: vars.winManager.getElementClass("SettingsEnableProgressWinSwt").select()
		else: vars.winManager.getElementClass("SettingsEnableProgressWinSwt").deselect()
	else:
		vars.winManager.getElementClass("SettingsEnableProgressWinSwt").select()

	log(cFN(),"okay","Element specific settings configured")

	log(cFN(),"info","Setting states of togglebuttons...")

	#Configure the color of toggle buttons in GUI
	activeShow = vars.config["general"]["activeShow"]
	for i in range(len(vars.dmxcnf.cuelst)):
		try:
			prcCue = vars.shows[activeShow]["cues"][f"cuelist{i}"]
			vars.winManager.configureElement(f"MainPageCues/{i}",text=prcCue["name"],border_color='#FD8B00' if prcCue["active"] == False else '#00FF00')
		except Exception as exc: log(cFN(),"err",f"Could not find 'MainPageCues/{i}': {exc}")
	for i in range(len(vars.dmxcnf.macro)):
		try:
			prcMac = vars.shows[activeShow]["macros"][f"macro{i}"]
			vars.winManager.configureElement(f"MainPageMacros/{i}",text=prcMac["name"],border_color='#FD8B00' if prcMac["active"] == False else '#00FF00')
		except Exception as exc: log(cFN(),"err",f"Could not find 'MainPageMacros/{i}': {exc}")
	for i in range(len(vars.dmxcnf.fixt)):
		try:
			prcFixt = vars.dmxcnf.fixt[i]
			vars.winManager.configureElement(f"FixtureCnf/{i}",text=prcFixt["name"])
			vars.winManager.configureElement(f"MainPageFixtureCnfBtn/{i}",text=prcFixt["name"])
		except Exception as exc: log(cFN(),"err",f"Could not find 'FixtureCnf/{i}' or 'MainPageFixtureCnfBtn/{i}'")
	log(cFN(),"okay","States of togglebuttons set correctly from active showfile")
