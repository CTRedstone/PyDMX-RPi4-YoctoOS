import sys
import time
from log import *
import tkinter as tk
import customtkinter as ctk
from tkinter import simpledialog as tkSD
from tkinter import messagebox as tkMB
from PIL import Image
from random import randint
from pytools.variables import cFN
from copy import deepcopy as dc
import pytools.ctktools as tktools
import NewPyDMX
from json import load as jsload, dump as jsdump
from threading import Thread
from PyQt5.QtWidgets import (
	QApplication, QMainWindow, QWidget, QPushButton, QLabel, QTextEdit,
	QLineEdit, QFrame, QGridLayout, QVBoxLayout, QHBoxLayout,
	QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QTextCursor
from threading import Thread
import sys, time
from random import randint
from PIL import Image
from pathlib import Path as plpath
from subprocess import call as shcall

class errs():
	class DataError(Exception): ...
	class ExecutionError(Exception): ...

class guivars():
	class general():
		swidth = None
		sheight = None
		show = None
		macrothr = []
		mthr_active = []
		usrvars = {}
	class loadwin(): ...
	class windows():
		class toplevels(): ...
		class screen2(): ...
	class frames():
		class main(): ...
		class screen2():
			class settings(): ...
			class programmer(): ...
			class fixturepool(): ...
			class macropool(): ...
			class editmacro(): ...
	class elements():
		class main(): ...
		class screen2():
			class settings(): ...
			class programmer(): ...
			class fixturepool(): ...
			class macropool(): ...
			class editmacro(): ...

def set_screen_size(size:dict):
	log("GUI/"+cFN(),"info","Loading screensize from dict")
	try:
		guivars.general.swidth = size["width"]
		guivars.general.sheight = size["height"]
	except Exception as exc:
		log("GUI/"+cFN(),"error",f"Failed to load screen size ({exc})")
		raise errs.DataError(f"Failed to load screen size ({exc})")
	log("GUI/"+cFN(),"okay","Screen size loaded")

def set_dmx_client(clientobject:type):
	log("GUI/"+cFN(),"info","Loading DMX client object")
	guivars.general.dmxComm = clientobject
	log("GUI/"+cFN(),"okay","DMX client object loaded")

def set_show(showobject):
	log("GUI/"+cFN(),"info","Loading show")
	guivars.general.show = showobject
	log("GUI/"+cFN(),"okay","Show loaded")

def set_config(configobject):
	log("GUI/"+cFN(),"info","Loading config")
	guivars.general.config = configobject
	log("GUI/"+cFN(),"okay","Config loaded")

def get_screen_index_for(screen,nolog=False):
	#log("GUI/"+cFN(),"info",f"Loading screen index for screen {repr(screen)}")
	_ret = guivars.general.show["config"]["screens"][screen]
	if not nolog: log("GUI/"+cFN(),"debug",f"Screen index for screen {repr(screen)} is {_ret}")
	return _ret

def get_screen_name_for(screen,nolog=False):
	#log("GUI/"+cFN(),"debug",f"Loading screen name for screen {repr(screen)}")
	screens = tktools.getMonitors(_return="list")
	if not nolog: log("GUI/"+cFN(),"debug",f"Currently recognized screens are: {screens}")
	_ret = tktools.getMonitors(_return="list")[get_screen_index_for(screen,nolog=nolog)]["name"]
	if not nolog: log("GUI/"+cFN(),"debug",f"Name of monitor for screen {repr(screen)} is {repr(_ret)}")
	return _ret

def save_config():	
		log("GUI/"+cFN(),"info","Saving config")
		try:
			with open("config.new.json","w+") as fle: jsdump(guivars.general.config,fle)
			log("GUI/"+cFN(),"okay","config saved")
		except Exception as exc:
			log("GUI/"+cFN(),"fatal",f"Could not save config ({exc})")
			NewPyDMX.tools.dialogs.error("config save failed","Failed to save config. Please check the logs and message the developers to correct this issue.")

class _tkinter():
	class guicmds():
		def quit(CONFIG,shutdown=False,saveshow=True):
			log("GUI/_tkinter.guicmds."+cFN(),"info","Quitting PyDMX due to User request\n\n\n\n\n"+"="*50+"\nAFTER MAINLOOP/PROGRAM EVENTS\n\n")
			#log("GUI/_tkinter.guicmds."+cFN(),"info","Quitting PyDMX due to User request")
			guivars.general.dmxComm.sendCommand("!noreply channels allOff",expectResponse=False)
			time.sleep(1)
			guivars.general.dmxComm.sendCommand("!noreply render stop",expectResponse=False)
			time.sleep(1)
			guivars.general.dmxComm.sendCommand("!noreply channels allOff",expectResponse=False)
			guivars.general.mthr_active = []
			if saveshow == True: save_config()
			if not shutdown:
				log("GUI/_tkinter.guicmds."+cFN(),"okay","Destroying windows, executing 'sys.exit()'")
				_tkinter.main.destroy(CONFIG)
				sys.exit()
			else:
				log("GUI/_tkinter.guicmds."+cFN(),"warn","Executing halt commands ('halt || shutdown -s -t 0 -c \"Shutdown of console requested\"')")
				try: shcall(["halt","||","shutdown","-s","-t","10","-c","'Shutdown","of","console","requested'"])
				except Exception as exc:
					log("GUI/_tkinter.guicmds."+cFN(),"error",f"Shutdown failed, destroying GUI and executing 'sys.exit()' ({exc})")
					_tkinter.main.destroy(CONFIG)
					sys.exit()
		
		def execcmd(CONFIG,cmdtext,expectResponse=True,applyDimmer=100):
			#Replace variables
			log("GUI/_tkinter.guicmds."+cFN(),"info","Replacing variables in cmd string")
			splt = cmdtext.split("$")
			for i in range(len(splt)-1):
				name = splt[i+1].split()[0]
				log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Trying to load value of '{name}'")
				try: val = guivars.general.usrvars[name]
				except KeyError: return "ERR VarNotFound"
				log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Variable '{name}' has a value of {repr(val)}")
				splt2 = splt[i+1].split()[1:]
				splt[i+1] = f"{repr(val)} {' '.join(splt2)}"
			cmdtext = ''.join(splt)
			log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Resulting command string: {repr(cmdtext)}")
			log("GUI/_tkinter.guicmds."+cFN(),"okay","Variables in cmd string replaced")
			
			#Replace dimmer values
			log("GUI/_tkinter.guicmds."+cFN(),"info","Applying dimmer onto command")
			cnv = True
			if len(cmdtext.split("value=")) < 2:
				cnv = False
				log("GUI/_tkinter.guicmds."+cFN(),"warn","No 'value' parameter supplied")
			if cnv == True:
				beforeval = cmdtext.split("value=")[0]
				valtxt = cmdtext.split("value=")[1].split(" ")[0]
				try: afterval = cmdtext.split("value=")[1].split(" ")[1]
				except IndexError: afterval = ""
				log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Value defined in command is: {repr(valtxt)}")
			if cnv == True and (valtxt[0],valtxt[-1]) not in (("'","'"),('"','"')):
				cnv = False
				log("GUI/_tkinter.guicmds."+cFN(),"warn",f"Could not apply dimmer (String not completed)")
			if cnv == True:
				for char in valtxt:
					if char not in "1234567890'" and char not in ('"'):
						log("GUI/_tkinter.guicmds."+cFN(),"warn",f"Could not apply dimmer (Invailid character {repr(char)})")
						cnv = False
			if cnv == True:
				val = int(eval(valtxt))
				final = int((val/100)*applyDimmer)
				log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Dimmer applied to value ({val} -> {final})")
				cmdtext = f"{beforeval}value='{final}' {afterval}"
				log("GUI/_tkinter.guicmds."+cFN(),"okay",f"Command changed")
			
			#Replace fixtures
			log("GUI/_tkinter.guicmds."+cFN(),"info","Replacing fixtures in cmd string")
			splt = cmdtext.split("fixt=")
			for i in range(len(splt)-1):
				name = splt[i+1].split()[0]
				val = ""
				try: fixt = guivars.general.show["fixtures"][name.split(".")[0]]
				except KeyError:
					log("GUI/_tkinter.guicmds."+cFN(),"error",f"Fixture {repr(name.split('.')[0])} not found")
					return "ERR FixtNotFound"
				universe = fixt["universe"]
				try: addr = fixt["addr"] + fixt["channels"].index(name.split(".")[1])
				except IndexError:
					log("GUI/_tkinter.guicmds."+cFN(),"error",f"No channel information supplied for fixture")
					return "ERR NoChannelInfoSupplied"
				except ValueError:
					log("GUI/_tkinter.guicmds."+cFN(),"error",f"Channel {repr(name.split('.')[1])} is not existant for fixture {repr(name.split('.')[0])}")
					return f"ERR ChannelNotFound {repr(name.split('.')[1])}"
				val = f"universe='{universe}' addr='{addr}'"
				splt2 = splt[i+1].split()[1:]
				splt[i+1] = f"{val} {' '.join(splt2)}"
			cmdtext = ''.join(splt)
			log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Resulting command string: {repr(cmdtext)}")
			
			splt = cmdtext.split("§")
			for i in range(len(splt)-1):
				name = splt[i+1].split()[0]
				val = ""
				try: fixt = guivars.general.show["fixtures"][name.split(".")[0]]
				except KeyError:
					log("GUI/_tkinter.guicmds."+cFN(),"error",f"Fixture {repr(name.split('.')[0])} not found")
					return "ERR FixtNotFound"
				universe = fixt["universe"]
				try: addr = fixt["addr"] + fixt["channels"].index(str(name.split(".")[1]).split(",")[0])
				except IndexError:
					log("GUI/_tkinter.guicmds."+cFN(),"error",f"No channel information supplied for fixture")
					return "ERR NoChannelInfoSupplied"
				except ValueError:
					log("GUI/_tkinter.guicmds."+cFN(),"error",f"Channel {repr(name.split('.')[1])} is not existant for fixture {repr(name.split('.')[0])}")
					return f"ERR ChannelNotFound {repr(name.split('.')[1])}"
				val = f"({universe},{addr}),"
				splt2 = splt[i+1].split(",")[1:]
				splt[i+1] = f"{val}{' '.join(splt2)}"
			cmdtext = ''.join(splt)
			log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Resulting command string: {repr(cmdtext)}")
			
			log("GUI/_tkinter.guicmds."+cFN(),"okay","Fixtures in cmd string replaced")
			
			#Execute command
			if cmdtext.split()[0] == "!IF":
				log("GUI/_tkinter.guicmds."+cFN(),"info","Found IF condition in command")
				var = cmdtext.split()[1]
				op = cmdtext.split()[2]
				val = cmdtext.split()[3]
				if len(cmdtext.split()) > 4: act = cmdtext.split()[4]
				else: act = "!RETURN"
				if var not in list(guivars.general.usrvars.keys()):
					log("GUI/_tkinter.guicmds."+cFN(),"error","Requested variable not existant")
					return "ERR VarNotFound"
				if op not in ("==",">",">=","<","<=","!=","not"):
					log("GUI/_tkinter.guicmds."+cFN(),"error",f"Invailid operation in conditional command: {op}")
					return "ERR InvailidOperation"
				vartxt = f"guivars.general.usrvars['{var}']"
				if not eval(f"{vartxt} {op} {val}"):
					log("GUI/_tkinter.guicmds."+cFN(),"warn","Condition not True, returning")
					return "OK ConditionChecked False"
				if act == "!RETURN":
					log("GUI/_tkinter.guicmds."+cFN(),"debug","No command execution requested, returning")
					return "OK ConditionChecked True"
				elif act != "!RUN":
					log("GUI/_tkinter.guicmds."+cFN(),"error","Invailid action specification at end of condition in command - Returning")
					return "ERR InvailidConditionAction"
				bfr = cmdtext.split()
				for i in range(5): del bfr[0]
				cmdtext = ' '.join(bfr)
				log("GUI/_tkinter.guicmds."+cFN(),"okay","Proceeding with command execution")
			
			if cmdtext.split()[0] not in ("exit","halt","shutdown","cuelist","quit","help","clear","","var","new","edit","copy","delete","wait"):
				log("GUI/_tkinter.guicmds."+cFN(),"info","Sending command to DMX Server")
				#resp = vars.dmxComm.sendCommand(_cmd,expectResponse=False if _cmd.split()[0] == "!noreply" else True)
				resp = guivars.general.dmxComm.sendCommand(cmdtext,expectResponse=True)
				if expectResponse: log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Response from Server: {resp}")
				return resp
			
			elif cmdtext.split()[0] in ("help"):
				with open("dmxServer.help.txt","r") as fle: help = ''.join(fle.readlines())
				with open("guicommands.txt","r") as fle: help = help + "\n" + ''.join(fle.readlines())
				help = "HELP\n---------------\n"+help
				guivars.elements.main.cmdhistory_txt.configure(state="normal")
				guivars.elements.main.cmdhistory_txt.insert("0.0",f"{help}\n")
				guivars.elements.main.cmdhistory_txt.configure(state="disabled")
			
			elif cmdtext.split()[0] in ("halt","shutdown","quit"):
				log("GUI/_tkinter.guicmds."+cFN(),"info","Shutdown was requested")
				ret = tkMB.askyesnocancel("Shutdown requested","Do you really want to shutdown the controller without saving the show?\n- 'Yes' will just shutdown the controller\n- 'No' will first save the show",parent=guivars.windows.main)
				if ret == None:
					log("GUI/_tkinter.guicmds."+cFN(),"warn","User aborted shutdown")
					return "ERR Aborted"
				if ret == True: log("GUI/_tkinter.guicmds."+cFN(),"info","User wants to shutdown without saving the showfile")
				log("GUI/_tkinter.guicmds."+cFN(),"warn","Shutting down console")
				_tkinter.guicmds.quit(CONFIG,shutdown=True,saveshow=True if ret == True else False)
			
			elif cmdtext.split()[0] in ("exit"):
				log("GUI/_tkinter.guicmds."+cFN(),"info","Program exit was requested")
				ret = tkMB.askyesnocancel("Shutdown requested","Do you really want to exit the program without saving the show?\n- 'Yes' will just quit the program\n- 'No' will first save the show",parent=guivars.windows.main)
				if ret == None:
					log("GUI/_tkinter.guicmds."+cFN(),"warn","User aborted exit")
					return "ERR Aborted"
				if ret == True: log("GUI/_tkinter.guicmds."+cFN(),"info","User wants to exit program without saving the showfile")
				log("GUI/_tkinter.guicmds."+cFN(),"warn","Quitting program")
				_tkinter.guicmds.quit(CONFIG,shutdown=False,saveshow=True if ret == True else False)
			
			elif cmdtext.split()[0] in ("wait"):
				log("GUI/_tkinter.guicmds."+cFN(),"info",f"Waiting for {cmdtext.split()[1]} seconds")
				try: time.sleep(float(cmdtext.split()[1]))
				except Exception as exc:
					log("GUI/_tkinter.guicmds."+cFN(),"error",f"Could not interrupt code execution with command wait ({exc})")
					return "ERR Failed"
				return "OK Waited"
			
			elif cmdtext.split()[0] == "edit":
				if cmdtext.split()[1] == "preference":
					if cmdtext.split()[2] == "gui/framework":
						log("GUI/_tkinter.guicmds."+cFN(),"info","User requested to change GUI Framework preference, building up dialog")
						try:
							_set = cmdtext.split()[3]
							if _set not in ("qt","tk"): raise Exception("")
						except: _set = None
						if _set == None:
							ret = NewPyDMX.tools.dialogs.yesno("Edit Preference",f"Do you want the GUI to be build up with tkinter ('yes') or PyQT ('no')?\nHint: tkinter is more failure-proof in general and will recieve any updates at first",parent=guivars.windows.main)
							guivars.general.config["gui"]["framework"] = "tk" if ret else "qt"
						else: guivars.general.config["gui"]["framework"] = dc(_set)
						log("GUI/_tkinter.guicmds."+cFN(),"debug",f"User chose framework '{'tk' if ret else 'qt'}' for GUI")
						log("GUI/_tkinter.guicmds."+cFN(),"okay","Preference of GUI framework changed")
						return "OK ChangedPreference (Please restart program)"
					elif cmdtext.split()[2] == "dmx/server/addr":
						log("GUI/_tkinter.guicmds."+cFN(),"info","User requested to change DMX Server address, prompting for new")
						root = tk.Tk()
						root.withdraw()
						ret = tkSD.askstring("Set Server Addr.","Please enter new address of DMX Server (You'll need to restart program to let changes be applied)",parent=guivars.windows.main)
						root.destroy()
						if len(ret.split(".")) != 4:
							log("GUI/_tkinter.guicmds."+cFN(),"error",f"User entered invailid IP: {repr(ret)}")
							tkMB.showerror("Set Server Addr. failed",f"Failed to change IP address: The entered IP ({repr(ret)} is invailid",parent=guivars.windows.main)
							return "ERR InvailidAddr"
						guivars.general.config["preferences"]["dmxcontrol"]["ip"] = ret
						log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Set server address to {repr(ret)}")
						log("GUI/_tkinter.guicmds."+cFN(),"okay","Server address changed")
						return "OK AddrChanged"
					elif cmdtext.split()[2] == "dmx/server/port":
						log("GUI/_tkinter.guicmds."+cFN(),"info","User requested to change DMX Server port, prompting for new")
						root = tk.Tk()
						root.withdraw()
						ret = tkSD.askinteger("Set Server Port","Please enter new port of DMX Server (You'll need to restart program to let changes be applied)",parent=guivars.windows.main)
						root.destroy()
						if ret > 35676:
							log("GUI/_tkinter.guicmds."+cFN(),"error",f"User entered invailid Port: {repr(ret)}")
							tkMB.showerror("Set Server Port failed",f"Failed to change Port: The entered port ({repr(ret)} is invailid",parent=guivars.windows.main)
							return "ERR InvailidPort"
						guivars.general.config["preferences"]["dmxcontrol"]["port"] = ret
						log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Set server port to {ret}")
						log("GUI/_tkinter.guicmds."+cFN(),"okay","Server port changed")
						return "OK PortChanged"
					elif cmdtext.split()[2] == "show/name":
						log("GUI/_tkinter.guicmds."+cFN(),"info","User requested to change show name, prompting for new")
						root = tk.Tk()
						root.withdraw()
						ret = tkSD.askstring("Change show name","Please enter new name of show",parent=guivars.windows.main)
						root.destroy()
						if ret == None or ret == "":
							log("GUI/_tkinter.guicmds."+cFN(),"error",f"Invailid show name ({repr(ret)})")
							return f"ERR InvailidShowName {repr(ret)}"
						guivars.general.show["name"] = ret
						newpath = '/'.join(CONFIG.preferences.general.currentshow.split("/")[:-1]) + "/" + ret + ".json"
						log("GUI/_tkinter.guicmds."+cFN(),"info",f"Moving current showfile from {repr(CONFIG.preferences.general.currentshow)} to {repr(newpath)}")
						try:
							plpath(CONFIG.preferences.general.currentshow).rename(newpath)
							CONFIG.preferences.general.currentshow = dc(newpath)
							guivars.general.config["preferences"]["general"]["currentshow"] = dc(newpath)
						except Exception as exc:
							log("GUI/_tkinter.guicmds."+cFN(),"error",f"Failed to move showfile ({exc})")
						log("GUI/_tkinter.guicmds."+cFN(),"debug",f"New show name is: {repr(ret)}")
						log("GUI/_tkinter.guicmds."+cFN(),"okay","Show name changed")
						return "OK ShowNameChanged"
				elif cmdtext.split()[1] == "macro":
					loc = cmdtext.split()[2]
					#em_win = _tkinter.editmacro_toplvl(CONFIG,loc=loc)
					#em_win.mainloop()
					guivars.windows.screen2.mainclass.showwin("editmacro",passkwargs={"loc":loc})
					return "OK MacroEdited"
				elif cmdtext.split()[1] == "fixture":
					edit = True
					log("GUI/_tkinter.guicmds."+cFN(),"info","Prepearing for fixture editing")
					try: name = cmdtext.split()[2]
					except IndexError:
						log("GUI/_tkinter.guicmds."+cFN(),"error",f"Fixture name has to be supplied")
						return "ERR NoNameSupplied"
					try: fixt = guivars.general.show["fixtures"][name]
					except KeyError:
						log("GUI/_tkinter.guicmds."+cFN(),"error",f"Fixture {repr(name)} not found")
						return f"ERR FixtNotFound {repr(name)}"
					
					while edit == True:
						log("GUI/_tkinter.guicmds."+cFN(),"info","Starting edit possibility for user")
						r = tk.Tk()
						r.withdraw()
						nname = tkSD.askstring(f"Edit fixture {repr(name)}","Enter name of fixture",initialvalue=name,parent=guivars.windows.main)
						channelsstr = tkSD.askstring(f"Edit fixture {repr(name)}","Please enter the channels of the fixture:",initialvalue=';'.join(fixt["channels"]),parent=guivars.windows.main)
						universe = tkSD.askinteger(f"Edit fixture {repr(name)}","Please enter the universe of the fixture. Keep in mind that the first Universe is universe 0, and so on.",initialvalue=fixt["universe"],parent=guivars.windows.main)
						addr = tkSD.askinteger(f"Edit fixture {repr(name)}","Please enter the address of the fixture. It can be any integer from 1 to 512",initialvalue=fixt["addr"],minvalue=1,maxvalue=512,parent=guivars.windows.main)
						
						if None not in (nname,channelsstr,universe,addr):
							ret = tkMB.askyesno(f"Edit fixture {repr(name)}",f"Is this data correct?\nname={repr(nname)}\nuniverse={repr(universe)}\naddr={repr(addr)}\nchannels={repr(channelsstr)}",parent=guivars.windows.main)
							if ret == True:
								log("GUI/_tkinter.guicmds."+cFN(),"okay","User confirmed edited data for fixture, validating entered data")
								edit = False
							else:
								log("GUI/_tkinter.guicmds."+cFN(),"okay","User denied that edited data for fixture is correct, asking for retry")
								ret = tkMB.askretrycancel(f"Edit fixture {repr(name)}",f"Do you want to retry editing the fixture?",parent=guivars.windows.main)
								if ret == False:
									log("GUI/_tkinter.guicmds."+cFN(),"okay","Aborting fixture editing process due to user selection")
									r.destroy()
									return "OK Aborted"
								else: log("GUI/_tkinter.guicmds."+cFN(),"okay","User requested retry of fixture editing process")
						
						if None in (nname,channelsstr,universe,addr):
							log("GUI/_tkinter.guicmds."+cFN(),"warn","Some setting the user made is empty.")
							ret = tkMB.askretrycancel(f"Edit fixture {repr(name)}",f"Some of the data you could change is empty. Do you want to retry?",parent=guivars.windows.main)
							if ret == False:
								log("GUI/_tkinter.guicmds."+cFN(),"okay","User chose to abort fixture editing process")
								r.destroy()
								return "OK Aborted"
					
					log("GUI/_tkinter.guicmds."+cFN(),"info","Validating entered changes")
					
					channels = channelsstr.split(";")
					editname = True
					editaddr = True
					editaddrcmt = []
					
					log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Validating fixture name {repr(nname)}")
					for char in (" ","\\","'",'"',".","/","{","}","[","]","=","$"):
						if char in nname:
							log("GUI/_tkinter.guicmds."+cFN(),"error",f"Character {repr(char)} isn't allowed to be used in a fixture's name")
							editname = False
					
					for fixtname in list(guivars.general.show["fixtures"].keys()):
						fixt = guivars.general.show["fixtures"][fixtname]
						if fixtname != name:
							if nname == fixtname: editname = False
							if ((fixt["addr"],fixt["universe"]) == (addr,universe)) or (fixt["universe"] == universe and addr+(len(channels)-1) == fixt["addr"]) or (fixt["universe"] == universe and (fixt["addr"] <= addr and (fixt["addr"] + len(fixt["channels"]) > addr))):
								log("GUI/_tkinter.guicmds."+cFN(),"error",f"Address of new fixture would overlap with other fixture")
								editaddr = False
								editaddrcmt.append(fixtname)
					
					save = True
					if False in (editname,editaddr):
						ret = tkMB.askyesno(f"Edit fixture {repr(name)}",f"{'Name can not get changed either because new is used or invailid' if not editname else ''}{'Channels, Address and Universe can not be changed because they would then overlap with other fixtures: '+';'.join(editaddrcmt) if not editaddr else ''}\nDo you want to save the vailid settings?",parent=guivars.windows.main)
						if ret == False:
							save = False
							log("GUI/_tkinter.guicmds."+cFN(),"okay","User chose to not only save the valid settings")
					
					if save:
						fixtdta = guivars.general.show["fixtures"][name]
						del guivars.general.show["fixtures"][name]
						if editaddr == True:
							fixtdta["channels"] = channels
							fixtdta["addr"] = addr
							fixtdta["universe"] = universe
						guivars.general.show["fixtures"][nname if editname else name] = dc(fixtdta)
						log("GUI/_tkinter.guicmds."+cFN(),"okay","Data saved")
						tkMB.showinfo(f"Edit fixture {repr(name)}","Changes saved",parent=guivars.windows.main)
						r.destroy()
						return "OK Saved"
					
					r.destroy()
					return "OK Aborted"
			
			elif cmdtext.split()[0] == "delete":
				if cmdtext.split()[1] == "macro":
					pos = cmdtext.split()[2]
					if len(pos.split("x")) != 2:
						return "ERR InvailidPos"
					if pos not in list(guivars.general.show["macros"].keys()):
						log("GUI/_tkinter.guicmds."+cFN(),"error",f"No macro found on position {repr(pos)}")
						return "ERR NotFound"
					log("GUI/_tkinter.guicmds."+cFN(),"info",f"Trying to delete macro at {repr(pos)}")
					
					log("GUI/_tkinter.guicmds."+cFN(),"info",f"Disabling macro thread of macro at {repr(pos)} if running")
					try:
						del guivars.general.mthr_active[guivars.general.mthr_active.index(pos)]
						log("GUI/_tkinter.guicmds."+cFN(),"okay","Macro thread disabled")
					except Exception as exc: log("GUI/_tkinter.guicmds."+cFN(),"okay","Macro thread for macro wasn't active")
					
					del guivars.general.show["macros"][pos]
					
					x,y = map(int,pos.split("x"))
					guivars.elements.main.macros_btn_lst[y][x].configure(text="",fg_color="#161616",hover_color="#161616",text_color=CONFIG.gui.style.general.buttontxt,border_width=CONFIG.gui.style.general.buttonborderwidth,border_color="#f00",command=eval(f'lambda:log("GUI/window/macro{x}x{y}_btn","okay","Click event detected")'))
					
					log("GUI/_tkinter.guicmds."+cFN(),"okay",f"Macro at {repr(pos)} deleted")
					return "OK MacroDeleted"
			
			elif cmdtext.split()[0] == "new":
				if cmdtext.split()[1] == "macro":
					r = tk.Tk()
					r.withdraw()
					pos = cmdtext.split()[2]
					if len(pos.split("x")) != 2:
						tkMB.showerror(f"Error",f"Failed to create Macro: Invailid position",parent=guivars.windows.main)
						r.destroy()
						return "ERR InvailidPos"
					name = tkSD.askstring(f"Create Macro","Please enter the name of the new macro",parent=guivars.windows.main)
					rstOE = tkMB.askyesno(f"Create Macro {repr(name)}",f"Reset changed DMX Values on end?",parent=guivars.windows.main)
					repOE = tkMB.askyesno(f"Create Macro {repr(name)}",f"Repeat macro code until it is stopped?",parent=guivars.windows.main)
					clr = tkSD.askstring(f"Create Macro {repr(name)}",f"Enter color of macro in grid (Can be: red/orange/yellow/green/cyan/blue/purple/white)",parent=guivars.windows.main)
					if clr not in ("red","orange","yellow","green","cyan","blue","purple","white"):
						tkMB.showerror(f"Error",f"Failed to create Macro: Invailid color",parent=guivars.windows.main)
						r.destroy()
						return "ERR InvailidColor"
					
					if clr == None or name == None:
						log("GUI/_tkinter.guicmds."+cFN(),"error","Either 'color' or 'name' dialog returned a valid value")
						return "ERR InvailidColorOrName"
					
					guivars.general.show["macros"][pos] = {"name":name,"resetOnEnd":rstOE,"repeatOnEnd":repOE,"code":[],"color":clr}
					
					x,y = map(int,pos.split("x"))
					try:
						title = guivars.general.show["macros"][f"{x}x{y}"]["name"] if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else ""
						clr = guivars.general.show["macros"][f"{x}x{y}"]["color"] if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else "#f00"
						guivars.elements.main.macros_btn_lst[y][x].configure(text=title,fg_color="#161616",hover_color="#161616",text_color=CONFIG.gui.style.general.buttontxt,border_width=CONFIG.gui.style.general.buttonborderwidth,border_color=clr,command=eval(f'lambda:_tkinter.guicmds.main.run.macro(guivars.general.config,"{x}x{y}")') if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else eval(f'lambda:log("GUI/window/macro{x}x{y}_btn","okay","Click event detected")'))
					except Exception as exc: log("GUI/_tkinter.guicmds."+cFN(),"error",f"Failed to configure macro button for new macro at {x}x{y} ({exc})")
					
					r.destroy()
					return "OK Created"
				elif cmdtext.split()[1] == "fixture":
					showgui = False
					root = tk.Tk()
					root.withdraw()
					if len(cmdtext.split()) < 4:
						showgui = True
						proceed = False
						name = None
						channels = None
						universe = None
						addr = None
						while proceed == False:
							if name == None: name = tkSD.askstring("Create fixture","Please enter the name of the new fixture",parent=guivars.windows.main)
							if channels == None: channels = tkSD.askstring(f"Create fixture {repr(name)}","Please enter the channels of the new fixture.\nPlease split with ';'. For example, use the following channel names:\ndimm / red / yellow / green / cyan / blue / magenta / white / pan / tilt / span / stilt / zoom / shutter",parent=guivars.windows.main)
							if universe == None: universe = tkSD.askinteger(f"Create fixture {repr(name)}","Please enter the universe of the Fixture. Keep in mind that the first Universe has the number '0' and so on.",initialvalue=0,parent=guivars.windows.main)
							if addr == None: addr = tkSD.askinteger(f"Create fixture {repr(name)}","Please enter the address of the Fixture. It can be any integer from 1 to 512.",parent=guivars.windows.main) #,minvalue=1,maxvalue=512)
							
							if None in (name,channels,universe,addr):
								proceed = False
								ret = tkMB.askretrycancel("Create fixture failed","Some of the data you have entered for new fixture creation isn't given. Retry or cancel new fixture creation.",parent=guivars.windows.main)
								if ret == False:
									log("GUI/_tkinter.guicmds."+cFN(),"okay","User chose to exit fixture creation dialog")
									root.destroy()
									return "OK Aborted"
							else:
								ret = tkMB.askyesno(f"Create fixture {repr(name)}",f"Is this data correct?\nname={repr(name)}\nuniverse={repr(universe)}\naddress={repr(addr)}\nchannels={repr(channels)}",parent=guivars.windows.main)
								if ret == False:
									log("GUI/_tkinter.guicmds."+cFN(),"okay","User denied fixture creation due to wrong data entered")
									root.destroy()
									return "OK Aborted"
								proceed = True
						cmdtext = f"new fixture {name} {channels} addr={addr} universe={universe}"
					
					if not showgui: root.destroy()
					
					if len(cmdtext.split()) >= 4: #Would mean "new fixture NAME channel1;channel2;channel3 addr=1 (universe=0)
						log("GUI/_tkinter.guicmds."+cFN(),"info","Trying to create new fixture from command")
						name = cmdtext.split()[2]
						channels = cmdtext.split()[3].split(";")
						addr = 1
						universe = 0
						try:
							for word in cmdtext.split()[-2:]:
								wlst = word.split("=")
								if "'" in wlst[1] and "{" not in wlst[1]:
									if wlst[0] == "addr": addr = int(eval(wlst[1]))
									elif wlst[0] == "universe": universe = int(eval(wlst[1]))
								else:
									if wlst[0] == "addr": addr = int(wlst[1])
									elif wlst[0] == "universe": universe = int(wlst[1])
						except Exception as exc:
							log("GUI/_tkinter.guicmds."+cFN(),"error",f"Failed to create new fixture from command ({exc})")
							if showgui: tkMB.showerror("Creating new fixture failed",f"Failed to load fixture data ({exc})",parent=guivars.windows.main)
							if showgui: root.destroy()
							return f"ERR {'_'.join(str(exc).split())}"
						
						log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Got fixture data: name={repr(name)} channels={repr(channels)} addr={addr} universe={universe}")
						
						if addr < 1 or addr > 512:
							log("GUI/_tkinter.guicmds."+cFN(),"error",f"Addr ({addr}) has to be between 1 and 512")
							if showgui: tkMB.showerror("Creating new fixture failed",f"DMX Address of Fixture is not between 1 and 512 ({addr})",parent=guivars.windows.main)
							if showgui: root.destroy()
							return f"ERR DmxAddressOutOfRange {addr}"
						
						log("GUI/_tkinter.guicmds."+cFN(),"info","Checking if fixture configuration is vailid & available")
						for char in (" ","\\","'",'"',".","/","{","}","[","]","=","$"):
							if char in name:
								log("GUI/_tkinter.guicmds."+cFN(),"error",f"Character {repr(char)} isn't allowed to be used in a fixture's name")
								if showgui: tkMB.showerror("Creating new fixture failed",f"Invailid character ({repr(char)}) used in fixture name",parent=guivars.windows.main)
								if showgui: root.destroy()
								return f"ERR InvailidCharUsed {repr(char)}"
						
						for fixtname in list(guivars.general.show["fixtures"].keys()):
							fixt = guivars.general.show["fixtures"][fixtname]
							if fixtname == name:
								log("GUI/_tkinter.guicmds."+cFN(),"error",f"Chosen fixture name is already existing ({repr(fixtname)})")
								if showgui: tkMB.showerror("Creating new fixture failed",f"Fixture with chosen name ({repr(name)}) is already existing: ({repr(fixtname)})",parent=guivars.windows.main)
								if showgui: root.destroy()
								return "ERR NameForbidden"
							elif (fixt["addr"],fixt["universe"]) == (addr,universe) or (fixt["universe"] == universe and addr+(len(channels)-1) == fixt["addr"]) or (fixt["universe"] == universe and (fixt["addr"] <= addr and (fixt["addr"] + len(fixt["channels"]) > addr))):
								log("GUI/_tkinter.guicmds."+cFN(),"error",f"Address of new fixture would overlap with other fixture")
								if showgui: tkMB.showerror("Creating new fixture failed",f"New Fixture would overlap other fixture's address ({repr(fixtname)})",parent=guivars.windows.main)
								if showgui: root.destroy()
								return f"ERR AddrAlreadyInUse {fixtname}"
						log("GUI/_tkinter.guicmds."+cFN(),"okay","Fixture configuration is vailid")
						
						log("GUI/_tkinter.guicmds."+cFN(),"info","Storing new fixture")
						guivars.general.show["fixtures"][name] = {"universe":dc(universe),"addr":dc(addr),"channels":dc(channels)}
						log("GUI/_tkinter.guicmds."+cFN(),"okay","New fixture added")
						tkMB.showinfo("Create new fixture",f"New fixture {name} created",parent=guivars.windows.main)
						if showgui: root.destroy()
						return "OK NewFixtureAdded"
			
			elif cmdtext.split()[0] == "var":
				args = cmdtext.split()
				operation = args[1]
				name = args[2]
				try: _type = args[3]
				except IndexError: _type = "str"
				try: value = args[4]
				except IndexError: value = None
				
				if operation == "set":
					if value == None:
						win = tk.Tk()
						win.withdraw()
						log("GUI/_tkinter.guicmds."+cFN(),"info","Prepearing dialog for variable creation")
						if _type == "str": val = tkSD.askstring(f"Value for '{name}'",f"Please enter a value for the variable '{name}'",parent=guivars.windows.main)
						elif _type == "int": val = tkSD.askinteger(f"Value for '{name}'",f"Please enter a value for the variable '{name}'",parent=guivars.windows.main)
						elif _type == "float": val = tkSD.askfloat(f"Value for '{name}'",f"Please enter a value for the variable '{name}'",parent=guivars.windows.main)
						else:
							log("GUI/_tkinter.guicmds."+cFN(),"error",f"No valid datatype requested ({_type})")
							return "ERR InvailidType"
					if _type not in ("str","int","float"):
						log("GUI/_tkinter.guicmds."+cFN(),"error",f"No valid datatype requested ({_type})")
						return "ERR InvailidType"
					guivars.general.usrvars[name] = val if value == None else eval(f"{_type}(value)")
					log("GUI/_tkinter.guicmds."+cFN(),"okay",f"Set value of variable '{name}' to {repr(val if value == None else value)}")
					if value == None: win.destroy()
					return "OK VarSet"
				elif operation == "get":
					log("GUI/_tkinter.guicmds."+cFN(),"info",f"Reading variable '{name}'")
					try: val = guivars.general.usrvars[name]
					except KeyError:
						log("GUI/_tkinter.guicmds."+cFN(),"error",f"Variable '{name}' not found")
						return "ERR VarNotFound"
					log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Value of variable '{name}' is {repr(val)}")
					return f"OK got_value {repr(val)}"
				elif operation == "calc":
					operation = _type
					val = args[4]
					if operation not in ("+","-","*","/"):
						log("GUI/_tkinter.guicmds."+cFN(),"error",f"Invailid var operation: {repr(operation)}")
						return "ERR InvailidOperation"
					log("GUI/_tkinter.guicmds."+cFN(),"info",f"Executing operation {repr(operation)} on variable '{name}' with {repr(val)}")
					try:
						var = guivars.general.usrvars[name]
						if type(var) == int: val = int(val)
						elif type(var) == float: val = float(val)
						else:
							raise Exception(f"Variable has invailid type")
						guivars.general.usrvars[name] = eval(f"guivars.general.usrvars[name] {operation} {val}")
					except KeyError:
						log("GUI/_tkinter.guicmds."+cFN(),"error",f"Variable '{name}' not found")
						return "ERR VarNotFound"
					except Exception as exc:
						log("GUI/_tkinter.guicmds."+cFN(),"error",f"Operation on Variable '{name}' could not be finished ({exc})")
						return f"ERR {'_'.join(str(exc).split())}"
					log("GUI/_tkinter.guicmds."+cFN(),"okay","Operation executed")
					return "OK OperationExecuted"
				
				return "ERR InvailidCommand"
	
		class main():
			def execcmd(CONFIG):
				log("GUI/_tkinter.guicmds."+cFN(),"info","Trying to execute entered command")
				cmdtext = guivars.elements.main.cmd_ent.get()
				log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Command loaded is: {repr(cmdtext)}")
				guivars.elements.main.cmdhistory_txt.configure(state="normal")
				guivars.elements.main.cmdhistory_txt.insert("0.0",f"> {cmdtext}\n")
				guivars.elements.main.cmdhistory_txt.configure(state="disabled")
				guivars.elements.main.cmd_ent.delete(0,tk.END)
				guivars.windows.main.update()
				
				if cmdtext == "":
					guivars.elements.main.cmdhistory_txt.configure(state="normal")
					guivars.elements.main.cmdhistory_txt.insert("0.0","[ERR] No command text supplied\n")
					guivars.elements.main.cmdhistory_txt.configure(state="disabled")
					log("GUI/_tkinter.guicmds.main."+cFN(),"warn","No command text supplied")
					return
				
				noreply = True if cmdtext.split()[0] == "!noreply" else False
				
				"""if cmdtext.split()[0] not in ("exit","halt","shutdown","macro","cuelist","quit","help","clear",""):
					log("GUI/_tkinter.guicmds.main."+cFN(),"info","Sending command to DMX Server")
					#resp = vars.dmxComm.sendCommand(_cmd,expectResponse=False if _cmd.split()[0] == "!noreply" else True)
					resp = guivars.general.dmxComm.sendCommand(cmdtext,expectResponse=not noreply)
					if not noreply:
						log("GUI/_tkinter.guicmds.main."+cFN(),"debug",f"Response from Server: {resp}")
						splt_resp = resp.split()
						guivars.elements.main.cmdhistory_txt.configure(state="normal")
						guivars.elements.main.cmdhistory_txt.insert("1.0",f"[{splt_resp[0]}] {splt_resp[1]}\n")
						guivars.elements.main.cmdhistory_txt.configure(state="disabled")
				elif cmdtext.split()[0] in ("help"):
					with open("dmxServer.help.txt","r") as fle: help = ''.join(fle.readlines())
					help = "HELP\n---------------\n"+help
					guivars.elements.main.cmdhistory_txt.configure(state="normal")
					guivars.elements.main.cmdhistory_txt.insert("0.0",f"{help}\n")
					guivars.elements.main.cmdhistory_txt.configure(state="disabled")
				elif cmdtext.split()[0] in ("halt","shutdown","quit","exit"):
					_tkinter.guicmds.quit(CONFIG)"""
				
				resp = _tkinter.guicmds.execcmd(CONFIG,cmdtext)
				if cmdtext.split()[0] not in ("exit","halt","shutdown","macro","cuelist","quit","help","clear",""):
					splt_resp = resp.split()
					if not noreply:
						guivars.elements.main.cmdhistory_txt.configure(state="normal")
						guivars.elements.main.cmdhistory_txt.insert("1.0",f"[{splt_resp[0]}] {' '.join(splt_resp[1:])}\n")
						guivars.elements.main.cmdhistory_txt.configure(state="disabled")
				
				log("GUI/_tkinter.guicmds.main."+cFN(),"okay","Command executed")
			
			class run():
				def macroInThread(CONFIG,loc:str,code:list[str],clr:str,resetOnEnd=True,repeatOnEnd=False):
					x,y = map(int,loc.split("x"))
					log("GUI/_tkinter.guicmds.main.run."+cFN(),"debug",f"{repr(x)} {repr(y)}")
					clrmap = {"red":"#400","orange":"#630","yellow":"#440","green":"#040","cyan":"#044","blue":"#004","purple":"#404","white":"#444"}
					guivars.elements.main.macros_btn_lst[y][x].configure(fg_color=clrmap[clr],hover_color=clrmap[clr])
					guivars.elements.main.macros_btn_lst[y][x].update()
					restore = {}
					for line in code:
						if resetOnEnd:
							if "addr=" in line or "fixt=" in line:
								pos = [0]
								for elm in line.split():
									if "addr=" in elm: break
									elif "fixt=" in elm: break
									pos[0] = pos[0] + 1
								if "universe=" in line and not "fixt=" in line:
									pos.append(0)
									for elm in line.split():
										if "universe=" in elm: break
										pos[1] = pos[1] + 1
								restaddr = line.split()[pos[0]] if len(pos) == 1 else f"{line.split()[pos[0]]} {line.split()[pos[1]]}"
								if restaddr not in list(restore.keys()):
									try:
										resp = _tkinter.guicmds.execcmd(CONFIG,f"channels getChannel {restaddr}",expectResponse=True)
										try: restore[restaddr] = int(resp.split("_")[3])
										except IndexError: pass
									except Exception as exc:
										log("GUI/_tkinter.guicmds.main.run."+cFN(),"error",f"Failed to save channel state of {line.split()[pos[0]]} ({exc})")
						
						resp = _tkinter.guicmds.execcmd(CONFIG,line,expectResponse=True)
						if resp.split()[0] == "ERR":
							NewPyDMX.tools.dialogs.error("Failed to run Macro",f"Some error occured while trying to execute macro at {loc}: {' '.join(resp.split()[1:])}")
							del guivars.general.mthr_active[guivars.general.mthr_active.index(loc)]
						if loc not in guivars.general.mthr_active:
							if resetOnEnd:
								for key in list(restore.keys()):
									_tkinter.guicmds.execcmd(CONFIG,f"channels setChannel {key} value='{restore[key]}'",expectResponse=True)
							break
					
					while repeatOnEnd and loc in guivars.general.mthr_active:
						for line in code:
							resp = _tkinter.guicmds.execcmd(CONFIG,line,expectResponse=True)
							if resp.split()[0] == "ERR":
								NewPyDMX.tools.dialogs.error("Failed to run Macro",f"Some error occured while trying to execute macro at {loc}: {' '.join(resp.split()[1:])}")
								del guivars.general.mthr_active[guivars.general.mthr_active.index(loc)]
							if loc not in guivars.general.mthr_active:
								if resetOnEnd:
									for key in list(restore.keys()):
										_tkinter.guicmds.execcmd(CONFIG,f"channels setChannel {key} value='{restore[key]}'",expectResponse=True)
								break
					
					guivars.elements.main.macros_btn_lst[y][x].configure(fg_color="#161616",hover_color="#161616")
					guivars.elements.main.macros_btn_lst[y][x].update()
					del guivars.general.mthr_active[guivars.general.mthr_active.index(loc)]
				
				def macro(CONFIG,location:str): #Location needs to be like "5x3"
					log("GUI/_tkinter.guicmds.main.run."+cFN(),"info",f"Trying to execute macro at {repr(location)}")
					try:
						macro_data = guivars.general.show["macros"][location]
					except KeyError:
						log("GUI/_tkinter.guicmds.main.run."+cFN(),"error",f"Could not find macro at {repr(location)} (not found)")
						return
					if location in guivars.general.mthr_active:
						del guivars.general.mthr_active[guivars.general.mthr_active.index(location)]
						log("GUI/_tkinter.guicmds.main.run."+cFN(),"warn",f"Macro {repr(location)} is getting executed, execution stopped")
						return
					else: guivars.general.mthr_active.append(location)
					guivars.general.macrothr.append(Thread(target=lambda:_tkinter.guicmds.main.run.macroInThread(CONFIG,location,macro_data["code"],macro_data["color"],resetOnEnd=macro_data["resetOnEnd"],repeatOnEnd=macro_data["repeatOnEnd"])))
					guivars.general.macrothr[len(guivars.general.macrothr)-1].start()
					log("GUI/_tkinter.guicmds.main.run."+cFN(),"okay",f"Ended macro executor for macro at {repr(location)}")
					"""guivars.elements.main.macros_btn_lst[int(location.split("x")[0])][int(location.split("x")[1])].configure(fg_color="#161616")
					guivars.elements.main.macros_btn_lst[int(location.split("x")[0])][int(location.split("x")[1])].update()
					del guivars.general.mthr_active[guivars.general.mthr_active.index(location)]"""
	
	class editmacro_toplvl:
		def __init__(self,CONFIG,loc=""):
			log("GUI/_tkinter.editmacro_toplvl","info","Building, initializing and creating toplevel for macro edit")
			
			name = guivars.general.show["macros"][loc]["name"]
			self.loc = loc
			
			try:
				self.root = ctk.CTk()
				self.root.withdraw()
				self.tl = ctk.CTkToplevel(self.root)
				self.tl.title(f"Edit macro '{name}'")
				self.tl.configure(fg_color=CONFIG.gui.style.main.background)
				self.root.bind("<Control-s>",lambda event:self.save())
				self.root.bind("<Control-x>",lambda event:self.quit())
				self.root.bind("<Escape>",lambda event:self.quit())
				self.tl.bind("<Control-s>",lambda event:self.save())
				self.tl.bind("<Control-x>",lambda event:self.quit())
				self.tl.bind("<Escape>",lambda event:self.quit())
				
				#Place the window on the screen
				try:
					tktools.placeWinOnMonitor(self.tl,fullscreen=True,monitor=get_screen_name_for("windows.macros.coding")) #tktools.primaryMonitorName()) #tktools.getSecondaryMonitors()[0]["name"])
					if get_screen_index_for("windows.macros.coding") == 1: #If should be on the same screen as screen2 windows are, hide them
						guivars.windows.screen2.mainclass.hideall()
				except Exception as exc:
					log("GUI/_tkinter.editmacro_toplvl","error",f"Failed to place window on screen and hide screen2 window ({exc})")
					tktools.placeWinOnMonitor(self.tl,fullscreen=True,monitor=tktools.getSecondaryMonitors()[0]["name"])
				try:
					if get_screen_index_for("windows.macros.coding") == get_screen_index_for("windows.main"):
						guivars.windows.main.attributes("-fullscreen",False)
						guivars.windows.main.withdraw()
				except Exception as exc: log("GUI/_tkinter.editmacro_toplvl","error",f"Failed to hide main window ({exc})")
				self.tl.update_idletasks()
				self.tl.lift()
				self.tl.focus_force()
				#self.tl.grab_set()
				self.tl.attributes("-topmost",True)
				self.tl.after(100,lambda:self.tl.attributes("-topmost",False))
			except Exception as exc:
				log("GUI/_tkinter.editmacro_toplvl","error",f"Failed to do basic window configuration ({exc})")
				return
			
			try:
				self.frame = tk.Frame(self.tl,bg=CONFIG.gui.style.main.framebg)
				self.frame.pack(anchor="center",expand=True)
				#self.frame.bind("<Control-s>",lambda event:self.save())
				self.name_ent = ctk.CTkEntry(self.frame,placeholder_text="Name of Macro",border_color=CONFIG.gui.style.general.buttonborder,border_width=2,fg_color=CONFIG.gui.style.main.frames.cmdexec.entrybg,text_color=CONFIG.gui.style.main.frames.cmdexec.entryfg,placeholder_text_color=CONFIG.gui.style.main.frames.cmdexec.entryfg,width=guivars.windows.main.winfo_width()-300,font=("monospace",14))
				self.name_ent.grid(row=0,column=0,columnspan=2,sticky="W",pady=4)
				self.code_txt = ctk.CTkTextbox(self.frame,border_color=CONFIG.gui.style.general.buttonborder,border_width=2,fg_color=CONFIG.gui.style.main.frames.cmdexec.entrybg,text_color=CONFIG.gui.style.main.frames.cmdexec.entryfg,width=guivars.windows.main.winfo_width()-300,height=400,font=("monospace",11))
				self.code_txt.grid(row=1,column=0,rowspan=50)
				#self.code_txt.bind("<Control-s>",lambda event:self.save())
				self.repOE = ctk.CTkSwitch(self.frame,text="Repeat On End",text_color=CONFIG.gui.style.main.frames.cmdexec.entryfg)
				self.repOE.grid(row=1,column=1,padx=4)
				#self.repOE.bind("<Control-s>",lambda event:self.save())
				self.rstOE = ctk.CTkSwitch(self.frame,text="Reset Addr on End",text_color=CONFIG.gui.style.main.frames.cmdexec.entryfg)
				self.rstOE.grid(row=2,column=1,padx=4)
				#self.rstOE.bind("<Control-s>",lambda event:self.save())
				self.save_btn = ctk.CTkButton(self.frame,width=100,height=65,text="Save changes",fg_color=CONFIG.gui.style.general.buttonbg,hover_color=CONFIG.gui.style.general.buttonbg,text_color=CONFIG.gui.style.general.buttontxt,border_width=CONFIG.gui.style.general.buttonborderwidth,border_color=CONFIG.gui.style.general.buttonborder,command=self.save) #lambda:log("GUI/window/saveMacroBtn","okay","Click event detected"))
				self.save_btn.grid(row=3,column=1)
				self.exit_btn = ctk.CTkButton(self.frame,width=100,height=65,text="Close",fg_color=CONFIG.gui.style.general.buttonbg,hover_color=CONFIG.gui.style.general.buttonbg,text_color=CONFIG.gui.style.general.buttontxt,border_width=CONFIG.gui.style.general.buttonborderwidth,border_color=CONFIG.gui.style.general.buttonborder,command=self.quit) #lambda:log("GUI/window/saveMacroBtn","okay","Click event detected"))
				self.exit_btn.grid(row=4,column=1)
				
				log("GUI/_tkinter.editmacro_toplvl","info","Configuring states of widgets")
				self.code_txt.insert("1.0",'\n'.join(guivars.general.show["macros"][loc]["code"]))
				self.code_txt.update()
				self.name_ent.insert("end",guivars.general.show["macros"][loc]["name"])
				self.name_ent.update()
				if guivars.general.show["macros"][loc]["repeatOnEnd"]: self.repOE.select()
				else: self.repOE.deselect()
				if guivars.general.show["macros"][loc]["resetOnEnd"]: self.rstOE.select()
				else: self.rstOE.deselect()
			except Exception as exc:
				log("GUI/_tkinter.editmacro_toplvl","error",f"Failed to configure widgets ({exc}), closing window")
				self.root.destroy()
			log("GUI/_tkinter.editmacro_toplvl","okay","GUI built")
		
		def mainloop(self):
			log("GUI/_tkinter.editmacro_toplvl","info","Starting mainloop...")
			self.root.mainloop()
			log("GUI/_tkinter.editmacro_toplvl","okay","Done")
		
		def quit(self):
			self.root.destroy()
			#guivars.windows.screen2.mainclass.showcurrent()
			try:
				if get_screen_index_for("windows.macros.coding") == get_screen_index_for("windows.main"):
					guivars.windows.main.attributes("-fullscreen",True)
					guivars.windows.main.deiconify()
			except: pass
			try:
				if get_screen_index_for("windows.macros.coding") == 1:
					guivars.windows.screen2.mainclass.showcurrent()
			except: pass
		
		def save(self):
			code = self.code_txt.get("1.0","end")[:-1]
			repOE = True if self.repOE.get() == 1 else False
			rstOE = True if self.rstOE.get() == 1 else False
			guivars.general.show["macros"][self.loc]["name"] = self.name_ent.get()
			guivars.general.show["macros"][self.loc]["code"] = code.split("\n") if code != "" else []
			guivars.general.show["macros"][self.loc]["repeatOnEnd"] = repOE
			guivars.general.show["macros"][self.loc]["resetOnEnd"] = rstOE
			
			x,y = map(int,self.loc.split("x"))
			try:
				guivars.elements.main.macros_btn_lst[y][x].configure(text=guivars.general.show["macros"][self.loc]["name"],command=eval(f'lambda:_tkinter.guicmds.main.run.macro(guivars.general.config,"{x}x{y}")') if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else eval(f'lambda:log("GUI/window/macro{x}x{y}_btn","okay","Click event detected")'))
			except Exception as exc: log("GUI/_tkinter.editmacro_toplvl."+cFN(),"error",f"Failed to configure macro button for macro at {x}x{y} ({exc})")
			
			NewPyDMX.tools.dialogs.info("Edit Macro - Saved","The changes you've made were saved",monitor=tktools.getSecondaryMonitors()[0]["name"])
	
	class loadwin():
		def init():
			log("GUI/loadwin.init","info","Building, initializing and creating loadwindow")
			guivars.loadwin.win = ctk.CTk()
			#guivars.loadwin.win.geometry(f"150x150{int(guivars.loadwin.win.winfo_screenwidth()/2)-75}+{int(guivars.loadwin.win.winfo_screenheight()/2)-75}")
			tktools.placeWinOnMonitor(guivars.loadwin.win,fullscreen=False,monitor=tktools.primaryMonitorName(),center=True,width=150,height=150)
			guivars.loadwin.win.title("PyDMX - Loading")
			guivars.loadwin.win.overrideredirect(True)
			guivars.loadwin.img = Image.open("resources/PyDMX_logos/PyDMX_logo_origin.png")
			guivars.loadwin.imglbl = ctk.CTkLabel(guivars.loadwin.win,image=ctk.CTkImage(light_image=guivars.loadwin.img,size=(100,100)),text="")
			guivars.loadwin.imglbl.pack()
			guivars.loadwin.stplbl = ctk.CTkLabel(guivars.loadwin.win,text="",font=("monospace",15))
			guivars.loadwin.stplbl.pack()
			guivars.loadwin.inflbl = ctk.CTkLabel(guivars.loadwin.win,text="",font=("Arial",12))
			guivars.loadwin.inflbl.pack()
			guivars.loadwin.win.update()
			log("GUI/loadwin.init","okay","Loadwindow created")
		
		def setstep(step="Initializing",desc=""):
			log("GUI/loadwin.setstep","info",f"Changing texts of loadwin to: step={repr(step)} | text={repr(desc)}")
			guivars.loadwin.win.title(f"PyDMX - {step}")
			guivars.loadwin.stplbl.configure(text=step)
			guivars.loadwin.inflbl.configure(text=desc)
			guivars.loadwin.win.update()
			log("GUI/loadwin.setstep","okay","Loadwin texts changed")
		
		def destroy():
			time.sleep(randint(200,1500)/1000)
			guivars.loadwin.win.destroy()
	
	class screen2:
		currentwin = None
		currentexceptions = ["editmacro"]
		
		def __init__(self,CONFIG):
			#log("GUI/_tkinter.screen2."+cFN(),"abc","def")
			log("GUI/_tkinter.screen2."+cFN(),"debug",f"Has internal class identifier: {str(self)[1:-1]}")
			log("GUI/_tkinter.screen2."+cFN(),"info","Configuring system relevant variables for screen2 class")
			self.screenind = int((0-int(get_screen_index_for("windows.main")/1))+1)
			log("GUI/_tkinter.screen2."+cFN(),"debug",f"Default screen index of screen2 windows is {self.screenind}")
			log("GUI/_tkinter.screen2."+cFN(),"okay","System relevant variables configured")
			
			log("GUI/_tkinter.screen2."+cFN(),"info","Creating window classes for screen2...")
			guivars.windows.screen2.settings = self.settings
			guivars.windows.screen2.programmer = self.programmer
			guivars.windows.screen2.fixturepool = self.fixturepool
			guivars.windows.screen2.macropool = self.macropool
			guivars.windows.screen2.editmacro = self.editmacro
			
			"""log("GUI/_tkinter.screen2."+cFN(),"info","Initializing window classes for screen2...")
			guivars.windows.screen2.settings(CONFIG,self)
			guivars.windows.screen2.programmer(CONFIG,self)
			guivars.windows.screen2.fixturepool(CONFIG,self)
			guivars.windows.screen2.macropool(CONFIG,self)
			guivars.windows.screen2.editmacro(CONFIG,self)"""
			
			log("GUI/_tkinter.screen2."+cFN(),"info","Saving window classes for screen2...")
			self.wins = {
				"settings":guivars.windows.screen2.settings(CONFIG,self),
				"programmer":guivars.windows.screen2.programmer(CONFIG,self),
				"fixturepool":guivars.windows.screen2.fixturepool(CONFIG,self),
				"macropool":guivars.windows.screen2.macropool(CONFIG,self),
				"editmacro":guivars.windows.screen2.editmacro(CONFIG,self)
			}
			log("GUI/_tkinter.screen2."+cFN(),"okay","Screen2 Windows created")
		
		def showinitialwin(self):
			log("GUI/_tkinter.screen2."+cFN(),"info","Loading window address to be shown")
			win = None
			for addr in list(self.wins.keys()):
				if guivars.general.show["config"]["screens"][f"windows.{addr}"] == self.screenind:
					win = addr
					break
			log("GUI/_tkinter.screen2."+cFN(),"debug",f"Window loaded: {repr(win)}")
			#if addr not in self.currentexceptions:
			self.currentwin = dc(addr)
			self.hideall()
			self.showwin(addr)
			log("GUI/_tkinter.screen2."+cFN(),"okay","Initial window shown")
		
		def showwin(self,addr:str,passargs=(),passkwargs={}):
			log("GUI/_tkinter.screen2."+cFN(),"info",f"Trying to show window {repr(addr)}")
			try:
				#if addr not in self.currentexceptions: get_screen_name_for(f"windows.{addr}",nolog=True)
				get_screen_index_for(f"windows.{addr}",nolog=True)
			except Exception as exc:
				log("GUI/_tkinter.screen2."+cFN(),"warn",f"Could not display window {repr(addr)} - Window is not existant({exc})")
				return
			self.currentwin = dc(addr) if addr not in self.currentexceptions else self.currentwin
			#if addr not in self.currentexceptions: 
			guivars.general.show["config"]["screens"][f"windows.{addr}"] = self.screenind
			self.wins[addr].show(self.wins[addr],*passargs,**passkwargs)
			for key in list(self.wins.keys()):
				if key != addr:
					if guivars.general.show["config"]["screens"][f"windows.{key}"] == self.screenind: # and addr not in self.currentexceptions:
						guivars.general.show["config"]["screens"][f"windows.{key}"] = None
						self.wins[key].hide(self.wins[key])
			log("GUI/_tkinter.screen2."+cFN(),"okay","Window shown")
		
		def hideall(self):
			log("GUI/_tkinter.screen2."+cFN(),"info","Hiding all according windows")
			for elm in list(self.wins.keys()):
				try: self.wins[elm].hide(self.wins[elm])
				except Exception as exc: log("GUI/_tkinter.screen2."+cFN(),"warn",f"Failed to hide window {repr(elm)} (exc), ignoring")
			log("GUI/_tkinter.screen2."+cFN(),"okay","All according windows hidden")
		
		def showcurrent(self):
			log("GUI/_tkinter.screen2."+cFN(),"info","Re-Showing currently selected window")
			self.hideall()
			guivars.general.show["config"]["screens"][f"windows.{self.currentwin}"] = self.screenind
			self.wins[self.currentwin].show(self.wins[self.currentwin])
			log("GUI/_tkinter.screen2."+cFN(),"okay","Currently selected window re-assinged")
		
		def bind(self,event,action):
			log("GUI/_tkinter.screen2."+cFN(),"info",f"Binding action to key event {repr(event)} in all existing windows...")
			for elm in list(self.wins.keys()):
				self.wins[elm].win.bind(event,action)
			log("GUI/_tkinter.screen2."+cFN(),"okay","Bound action to event")
		
		def unbind(self,event):
			log("GUI/_tkinter.screen2."+cFN(),"info",f"Unbinding every action from key event {repr(event)} in all existing windows...")
			for elm in list(self.wins.keys()):
				self.wins[elm].win.unbind(event)
			log("GUI/_tkinter.screen2."+cFN(),"okay","Unbound actions from event")
		
		class window:
			name = ""
			visib_timeout = 1000
			
			def check_visibility(self):
				if get_screen_index_for(f"windows.{self.name}",nolog=True) == None: self.win.withdraw()
				else: tktools.placeWinOnMonitor(self.win,fullscreen=True,monitor=get_screen_name_for(f"windows.{self.name}",nolog=True))
				self.win.after(self.visib_timeout,self.check_visibility)
			
			def start_loop(self):
				self.win.after(self.visib_timeout,self.check_visibility)
			
			def show(self,*args,**kwargs):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info",f"Trying to show window {repr(self.name)}...")
				try:
					tktools.placeWinOnMonitor(self.win,fullscreen=True,monitor=get_screen_name_for(f"windows.{self.name}"),width=self.width,height=self.height)
					self.win.deiconify()
					self.win.update_idletasks()
					self.win.update()
					#self.win.attributes("-fullscreen",True)
				except Exception as exc:
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"error",f"Failed ({exc})")
					return
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
				try:
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Executing custom show function...")
					self.cshow(*args,**kwargs)
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
				except Exception as exc: log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"warn",f"No executable custom show function found, skipped ({exc})")
			
			def hide(self,*args,**kwargs):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info",f"Trying to hide window {repr(self.name)}...")
				try:
					#self.win.update_idletasks()
					#self.win.update()
					#self.win.attributes("-fullscreen",False)
					self.win.withdraw()
					self.win.update_idletasks()
					self.win.update()
				except Exception as exc:
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"error",f"Failed ({exc})")
					return
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
				try:
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Executing custom quit function...")
					self.cquit(*args,**kwargs)
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
				except Exception as exc: log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"warn",f"No executable custom quit function found, skipped ({exc})")
			
			def __init__(self,CONFIG,screen):
				#log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"abc","def")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info",f"Initializing screen2 window '{self.name}'")
				self.CONFIG = CONFIG
				self.screen = screen
				self.win = ctk.CTkToplevel(guivars.windows.main)
				self.width = CONFIG.gui.style.main.size.width
				self.height = CONFIG.gui.style.main.size.height
				if get_screen_index_for(f"windows.{self.name}") == None: self.win.withdraw()
				else: tktools.placeWinOnMonitor(self.win,fullscreen=True,monitor=get_screen_name_for(f"windows.{self.name}"),width=self.width,height=self.height)
				self.win.title(f"PyDMX - {self.name[0].upper()+''.join(self.name[1:])}")
				self.win.overrideredirect(True)
				self.win.configure(bg=CONFIG.gui.style.main.background)
				self.masterfrm = ctk.CTkFrame(self.win,width=self.width,fg_color=CONFIG.gui.style.main.background)
				self.masterfrm.pack(fill="both",expand=True)
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay",f"Screen2 window '{self.name}' initialized")
				
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Storing default variables")
				self.stdfrmsettings = {
					"bd":CONFIG.gui.style.main.framebg,
					"bd":CONFIG.gui.style.main.framebordersize,
					"relief":CONFIG.gui.style.main.framerelief
				}
				self.stdbtnargs = {
					"fg_color":CONFIG.gui.style.general.buttonbg,
					"hover_color":CONFIG.gui.style.general.buttonhover,
					"text_color":CONFIG.gui.style.general.buttontxt,
					"border_width":CONFIG.gui.style.general.buttonborderwidth,
					"border_color":CONFIG.gui.style.general.buttonborder
				}
				self.stdtextclr = CONFIG.gui.style.main.frames.cmdexec.entryfg
				self.stdtextclr_ctk = {
					"text_color": self.stdtextclr,
					"fg_color": CONFIG.gui.style.main.framebg,
					"font": ("Roboto",15)
				}
				self.stdtextclr_tk = {
					"fg": self.stdtextclr,
					"bg": CONFIG.gui.style.main.framebg,
					"font": ("Roboto",15)
				}
				self.switchstandart = {
					"button_color":self.stdtextclr,
					"button_hover_color":self.stdtextclr,
					"fg_color":"red",
					"progress_color":"green",
					"text_color":self.stdtextclr,
					"font":("Roboto",15)
				}
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug","Creating links to widget classes for {repr(self.name)}")
				self.frmclass = eval(f"guivars.frames.screen2.{dc(self.name)}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Created frames class at {str(self.frmclass)[1:-1]}")
				self.elmclass = eval(f"guivars.elements.screen2.{dc(self.name)}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Created elements class at {str(self.elmclass)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Default variables stored")
				
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Prepearing standart GUI elements")
				self.prepeare_frames()
				self.generate_sidebar()
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Standart GUI elements created")
				
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info",f"Calling widget create method for screen2 window '{self.name}'")
				self.build_widgets()
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Widgets configured, window ready")
				
				self.hide()
			
			def prepeare_frames(self):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Configuring frames")
				self.frmclass.topframe = ctk.CTkFrame(self.masterfrm,width=self.width-4,fg_color="black")
				self.frmclass.topframe.grid(row=0,column=0,columnspan=20,pady=2)
				self.elmclass.title_lbl = ctk.CTkLabel(self.frmclass.topframe,text=f"{self.name[0].upper()+''.join(self.name[1:])}",text_color=self.stdtextclr,font=("Monospace Bold",30),bg_color="black")
				self.elmclass.title_lbl.pack()
				self.frmclass.menuframe = ctk.CTkFrame(self.masterfrm,fg_color=self.CONFIG.gui.style.main.background)
				self.frmclass.menuframe.grid(row=1,rowspan=19,column=19,pady=2,padx=2)
				self.frmclass.mainframe = ctk.CTkFrame(self.masterfrm,fg_color=self.CONFIG.gui.style.main.framebg,height=self.win.winfo_height()-self.frmclass.topframe.winfo_height(),width=self.win.winfo_width()-self.frmclass.menuframe.winfo_width()+105)
				self.frmclass.mainframe.grid(row=1,rowspan=39,column=0,columnspan=19,pady=2,padx=2)
				for i in range(20):
					self.masterfrm.grid_rowconfigure(i, weight=1, minsize=50)
					self.masterfrm.grid_columnconfigure(i, weight=1, minsize=47)
				for i in range(39):
					self.frmclass.mainframe.grid_rowconfigure(i, weight=1, minsize=30)
					if i < 19: self.frmclass.mainframe.grid_columnconfigure(i, weight=1, minsize=47)
				self.frmclass.mainframe.grid_propagate(True)
				self.masterfrm.update_idletasks()
				self.masterfrm.update()
				self.win.update_idletasks()
				self.win.update()
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Frames configured")
			
			def generate_sidebar(self):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Generating sidebar menu")
				menulst = {
					"Settings":lambda:self.screen.showwin("settings"),
					"Programmer":lambda:self.screen.showwin("programmer"),
					"Fixturepool":lambda:self.screen.showwin("fixturepool"),
					"Macropool":lambda:self.screen.showwin("macropool")
				}
				self.elmclass.sidebar_btns = []
				for elm in list(menulst.items()):
					self.elmclass.sidebar_btns.append(ctk.CTkButton(self.frmclass.menuframe,text=elm[0],command=elm[1],width=84,height=84,**self.stdbtnargs))
					self.elmclass.sidebar_btns[-1:][0].grid(row=len(self.elmclass.sidebar_btns),column=0,pady=2)
					self.elmclass.sidebar_btns[-1:][0].grid_propagate(False)
			
			def build_widgets(self):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"warn","This method should have been overwritten")
		
		class settings(window):
			name = "settings"
			
			"""class frmclass(): ...
			class elmclass(): ..."""
			
			def build_widgets(self):
				"""
				"width":CONFIG.gui.style.main.size.width,
				"height":CONFIG.gui.style.main.size.height
				"""
				
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info",f"Configuring elements")
				gargs = {"pady":2,"padx":2}
				self.elmclass.framework_lbl = tk.Label(self.frmclass.mainframe,text="GUI Framework (Tkinter/PyQt):",**self.stdtextclr_tk)
				self.elmclass.framework_lbl.grid(row=0,column=0,columnspan=4,sticky="W",**gargs)
				self.elmclass.framework_swt = ctk.CTkSwitch(self.frmclass.mainframe,text="ON=Tkinter;OFF=PyQt",**self.switchstandart)
				self.elmclass.framework_swt.grid(row=0,column=5,sticky="W",**gargs)
				self.elmclass.framework_swt.select()
				
				self.elmclass.svrip_lbl = tk.Label(self.frmclass.mainframe,text="DMX Server IP (Restart needed):",**self.stdtextclr_tk)
				self.elmclass.svrip_lbl.grid(row=1,column=0,columnspan=4,sticky="W",**gargs)
				self.elmclass.svrip_ent = ctk.CTkEntry(self.frmclass.mainframe,**self.stdtextclr_ctk)
				self.elmclass.svrip_ent.grid(row=1,column=5,sticky="W",**gargs)
				self.elmclass.svrip_ent.insert(0,guivars.general.config["preferences"]["dmxcontrol"]["ip"])
				
				self.elmclass.svrport_lbl = tk.Label(self.frmclass.mainframe,text="DMX Server Port (Restart needed):",**self.stdtextclr_tk)
				self.elmclass.svrport_lbl.grid(row=2,column=0,columnspan=4,sticky="W",**gargs)
				self.elmclass.svrport_ent = ctk.CTkEntry(self.frmclass.mainframe,**self.stdtextclr_ctk)
				self.elmclass.svrport_ent.grid(row=2,column=5,sticky="W",**gargs)
				self.elmclass.svrport_ent.insert(0,guivars.general.config["preferences"]["dmxcontrol"]["port"])
				
				self.elmclass.save_btn = ctk.CTkButton(self.frmclass.mainframe,text="Save changes",command=self.save_settings,**self.stdbtnargs)
				self.elmclass.save_btn.grid(row=4,column=0,columnspan=3,**gargs)
				self.elmclass.save_btn = ctk.CTkButton(self.frmclass.mainframe,text="Save show",command=self.save_show,**self.stdbtnargs)
				self.elmclass.save_btn.grid(row=4,column=2,columnspan=3,**gargs)
				"""
				"text_color": self.stdtextclr,
				"fg_color": CONFIG.gui.style.main.framebg,
				"font": ("Roboto",15)
				"""
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Elements configured")
				
				#self.win.after(150,self.check_visibility)
			
			def save_settings(self):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Saving settings")
				try:
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug","Loading settings from GUI")
					guiframework = "tk" if self.elmclass.framework_swt.get() in (True,1) else "qt"
					svrip = self.elmclass.svrip_ent.get()
					svrport = int(self.elmclass.svrport_ent.get())
					
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug","Storing settings")
					guivars.general.config["preferences"]["gui"]["framework"] = dc(guiframework)
					guivars.general.config["preferences"]["dmxcontrol"]["ip"] = dc(svrip)
					guivars.general.config["preferences"]["dmxcontrol"]["port"] = dc(svrport)
				except Exception as exc:
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"error",f"Could not save settings ({exc})")
					tkMB.showerror("Error","Could not save settings",detail=str(exc))
					return
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Settings saved")
				tkMB.showinfo("Information","Settings were saved")
			
			def save_show(self):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info",f"Saving showfile (triggered by user request) ({CONFIG.preferences.general.currentshow})...")
				try:
					with open(CONFIG.preferences.general.currentshow,"w+") as fle: jsdump(guivars.general.show,fle)
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Showfile saved")
					tkMB.showinfo("Show saved","Showfile got saved",detail=CONFIG.preferences.general.currentshow)
				except Exception as exc:
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"error",f"Failed to save showfile ({exc})")
					tkMB.showerror("Error","Showfile could not be saved.",detail=str(exc))
	
		class programmer(window):
			name = "programmer"
			
		class fixturepool(window):
			name = "fixturepool"
		
		class macropool(window):
			name = "macropool"
		
		class editmacro(window):
			name = "editmacro"
			mcrloc = ""
			oldkeybind = ""
			
			def build_widgets(self):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Creating widgets...")
				self.elmclass.name_ent = ctk.CTkEntry(self.frmclass.mainframe,placeholder_text="Name of Macro",border_color=self.CONFIG.gui.style.general.buttonborder,border_width=2,fg_color=self.CONFIG.gui.style.main.frames.cmdexec.entrybg,text_color=self.CONFIG.gui.style.main.frames.cmdexec.entryfg,placeholder_text_color=self.CONFIG.gui.style.main.frames.cmdexec.entryfg,width=guivars.windows.main.winfo_width()-300,font=("monospace",14))
				self.elmclass.name_ent.grid(row=0,column=0,rowspan=2,columnspan=18,sticky="W",pady=4)
				self.elmclass.code_txt = ctk.CTkTextbox(self.frmclass.mainframe,border_color=self.CONFIG.gui.style.general.buttonborder,border_width=2,fg_color=self.CONFIG.gui.style.main.frames.cmdexec.entrybg,text_color=self.CONFIG.gui.style.main.frames.cmdexec.entryfg,width=guivars.windows.main.winfo_width()-300,height=400,font=("monospace",11))
				self.elmclass.code_txt.grid(row=1,column=0,rowspan=15,columnspan=18)
				#self.code_txt.bind("<Control-s>",lambda event:self.save())
				self.elmclass.repOE = ctk.CTkSwitch(self.frmclass.mainframe,text="Repeat On End",text_color=self.CONFIG.gui.style.main.frames.cmdexec.entryfg)
				self.elmclass.repOE.grid(row=1,column=18,rowspan=1,padx=4)
				#self.repOE.bind("<Control-s>",lambda event:self.save())
				self.elmclass.rstOE = ctk.CTkSwitch(self.frmclass.mainframe,text="Reset Addr on End",text_color=self.CONFIG.gui.style.main.frames.cmdexec.entryfg)
				self.elmclass.rstOE.grid(row=2,column=18,rowspan=1,padx=4)
				#self.rstOE.bind("<Control-s>",lambda event:self.save())
				self.elmclass.keybind = ctk.CTkEntry(self.frmclass.mainframe,placeholder_text="Keybind",border_color=self.CONFIG.gui.style.general.buttonborder,border_width=2,fg_color=self.CONFIG.gui.style.main.frames.cmdexec.entrybg,text_color=self.CONFIG.gui.style.main.frames.cmdexec.entryfg,placeholder_text_color=self.CONFIG.gui.style.main.frames.cmdexec.entryfg,width=100,font=("monospace",14))
				self.elmclass.keybind.grid(row=3,column=18,rowspan=1,padx=4)
				self.elmclass.save_btn = ctk.CTkButton(self.frmclass.mainframe,width=100,height=65,text="Save changes",fg_color=self.CONFIG.gui.style.general.buttonbg,hover_color=self.CONFIG.gui.style.general.buttonbg,text_color=self.CONFIG.gui.style.general.buttontxt,border_width=self.CONFIG.gui.style.general.buttonborderwidth,border_color=self.CONFIG.gui.style.general.buttonborder,command=self.save) #lambda:log("GUI/window/saveMacroBtn","okay","Click event detected"))
				self.elmclass.save_btn.grid(row=4,column=18,rowspan=2)
				self.elmclass.exit_btn = ctk.CTkButton(self.frmclass.mainframe,width=100,height=65,text="Close",fg_color=self.CONFIG.gui.style.general.buttonbg,hover_color=self.CONFIG.gui.style.general.buttonbg,text_color=self.CONFIG.gui.style.general.buttontxt,border_width=self.CONFIG.gui.style.general.buttonborderwidth,border_color=self.CONFIG.gui.style.general.buttonborder,command=self.exit) #lambda:log("GUI/window/saveMacroBtn","okay","Click event detected"))
				self.elmclass.exit_btn.grid(row=6,column=18,rowspan=2)
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
				
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Configuring keybinds...")
				self.win.bind("<Control-s>",lambda event:self.save())
				self.win.bind("<Control-x>",lambda event:self.exit())
				self.win.bind("<Escape>",lambda event:self.exit())
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
				
				#self.win.after(150,self.check_visibility)
				
				"""log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Configuring states of widgets...")
				self.elmclass.code_txt.insert("1.0",'\n'.join(guivars.general.show["macros"][loc]["code"]))
				self.elmclass.code_txt.update()
				self.elmclass.name_ent.insert("end",guivars.general.show["macros"][loc]["name"])
				self.elmclass.name_ent.update()
				if guivars.general.show["macros"][loc]["repeatOnEnd"]: self.elmclass.repOE.select()
				else: self.elmclass.repOE.deselect()
				if guivars.general.show["macros"][loc]["resetOnEnd"]: self.elmclass.rstOE.select()
				else: self.elmclass.rstOE.deselect()
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")"""
			
			def cshow(self,*args,loc=""):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Validating location...")
				if loc in ("",None) and self.mcrloc in ("",None):
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"error","No macro location found, aborting...")
					self.screen.hideall(screen)
					self.screen.showcurrent(screen)
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Aborted")
					return
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
				if loc != self.mcrloc:
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Storing location value...")
					if loc not in ("",None) and loc != self.mcrloc:
						self.mcrloc = dc(loc)
					elif loc in ("",None) and self.mcrloc not in ("",None) and loc != self.mcrloc:
						loc = dc(self.mcrloc)
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
					
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info",f"Configuring widgets for macro location {repr(loc)}")
					self.elmclass.name_ent.delete(0,len(self.elmclass.name_ent.get()))
					self.elmclass.name_ent.insert(0,guivars.general.show["macros"][loc]["name"])
					self.elmclass.name_ent.update()
					self.elmclass.code_txt.delete("1.0","end")
					self.elmclass.code_txt.insert("1.0",'\n'.join(guivars.general.show["macros"][loc]["code"]))
					self.elmclass.code_txt.update()
					self.elmclass.keybind.delete(0,len(self.elmclass.keybind.get()))
					self.elmclass.keybind.insert(0,guivars.general.show["keybinds"][loc] if "<KeyPress-" not in guivars.general.show["keybinds"][loc] else guivars.general.show["keybinds"][loc][-2])
					self.elmclass.keybind.update()
					try: self.oldkeybind = dc(guivars.general.show["keybinds"][loc])
					except: self.oldkeybind = ""
					if guivars.general.show["macros"][loc]["repeatOnEnd"]: self.elmclass.repOE.select()
					else: self.elmclass.repOE.deselect()
					self.elmclass.repOE.update()
					if guivars.general.show["macros"][loc]["resetOnEnd"]: self.elmclass.rstOE.select()
					else: self.elmclass.rstOE.deselect()
					self.elmclass.repOE.update()
					self.win.update_idletasks()
					self.win.update()
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Widgets configured")
				else: log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Skipped widget configuration part due to equal macro name")
			
			def save(self):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Saving changes...")
				code = str(self.elmclass.code_txt.get("1.0","end"))[:-1]
				repOE = True if self.elmclass.repOE.get() == 1 else False
				rstOE = True if self.elmclass.rstOE.get() == 1 else False
				guivars.general.show["macros"][self.mcrloc]["name"] = self.elmclass.name_ent.get()
				guivars.general.show["macros"][self.mcrloc]["code"] = code.split("\n") if code != "" else []
				guivars.general.show["macros"][self.mcrloc]["repeatOnEnd"] = repOE
				guivars.general.show["macros"][self.mcrloc]["resetOnEnd"] = rstOE
				if self.elmclass.keybind.get() != "":
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Re-configuring keybind for macro")
					try: guivars.windows.main.unbind(self.oldkeybind)
					except: pass
					try: self.screen.unbind(self.oldkeybind)
					except: pass
					kp = ""
					try:
						kp = self.elmclass.keybind.get() if len(self.elmclass.keybind.get()) > 1 else f"<KeyPress-{self.elmclass.keybind.get()}>"
						log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Event adress: {repr(kp)}")
						guivars.general.show["keybinds"][self.mcrloc] = dc(kp)
						x,y = map(int,self.mcrloc.split("x"))
						guivars.windows.main.bind(kp,eval(f'lambda event:_tkinter.guicmds.main.run.macro(guivars.general.config,"{x}x{y}")') if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else eval(f'lambda event:log("GUI/window/macroexec_from_key/{kb[1:-1]}"","okay","Click event detected")'))
						self.screen.bind(kp,eval(f'lambda event:_tkinter.guicmds.main.run.macro(guivars.general.config,"{x}x{y}")') if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else eval(f'lambda event:log("GUI/window/macroexec_from_key/{kb[1:-1]}"","okay","Click event detected")'))
						log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Keybind configured")
					except Exception as exc:
						log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"warn",f"Failed to configure keybinding{' '+repr(kp) if kp != '' else ''} for macro ({exc})")
						tkMB.showerror("Error","Could not configure keybinding",detail=str(exc))
				else:
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Unbinding current key from macro...")
					try: guivars.windows.main.unbind(self.oldkeybind)
					except: pass
					try: del guivars.general.show["keybinds"][self.mcrloc]
					except: pass
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
				
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Trying to reconfigure macro button...")
				x,y = map(int,self.mcrloc.split("x"))
				try:
					guivars.elements.main.macros_btn_lst[y][x].configure(text=guivars.general.show["macros"][self.mcrloc]["name"],command=eval(f'lambda:_tkinter.guicmds.main.run.macro(guivars.general.config,"{x}x{y}")') if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else eval(f'lambda:log("GUI/window/macro{x}x{y}_btn","okay","Click event detected")'))
					log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
				except Exception as exc: log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"warn",f"Failed to configure macro button for macro at {x}x{y} ({exc})")
				
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Changes saved")
				tkMB.showinfo("Edit Macro - Saved","The changes you've made were saved")
			
			def exit(self):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"debug",f"Found internal class identifier in 'self' parameter: {str(self)[1:-1]}")
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Exiting from edit macro GUI")
				self.screen.showcurrent()
				self.mcrloc = ""
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","edit macro GUI hidden")
			
			def cquit(self,*args,**kwargs):
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"info","Quitting Editmacro window, resetting macro location...")
				self.mcrloc = ""
				log(f"GUI/_tkinter.screen2.{self.name}."+cFN(),"okay","Done")
	
	class main():
		def set_title(title:str):
			log("GUI/_tkinter.main."+cFN(),"info",f"Changing title of main window to {repr(title)}")
			guivars.windows.main.title(title)
			log("GUI/_tkinter.main."+cFN(),"okay","Title of main window changed")
		
		def build_gui(CONFIG):
			log("GUI/_tkinter.main.build_gui","info","Building main GUI")
			
			#Initialize window
			log("GUI/_tkinter.main.build_gui","info","Initializing main window")
			guivars.windows.main = tk.Tk()
			log("GUI/_tkinter.main.build_gui","okay","Main window initialized")
			
			#Configure window
			log("GUI/_tkinter.main.build_gui","info","Configuring main window")
			guivars.windows.main.title("PyDMX")
			#guivars.windows.main.geometry(f"{CONFIG.gui.style.main.size.width}x{CONFIG.gui.style.main.size.height}")
			try: tktools.placeWinOnMonitor(guivars.windows.main,monitor=get_screen_name_for("windows.main")) #tktools.getSecondaryMonitors()[0]["name"]) #tktools.getMonitors(_return="list")[1]["name"]
			except: tktools.placeWinOnMonitor(guivars.windows.main,monitor=tktools.getSecondaryMonitors()[0]["name"])
			guivars.windows.main.bind("<Escape>",lambda event:_tkinter.guicmds.quit())
			log("GUI/_tkinter.main.build_gui","okay","Main window configured")
			
			#Configure style of window
			log("GUI/_tkinter.main.build_gui","info","Configuring style of main window")
			log("GUI/_tkinter.main.build_gui","debug",f"Configured background color of main window is: {repr(CONFIG.gui.style.main.background)}")
			guivars.windows.main.configure(bg=CONFIG.gui.style.main.background)
			log("GUI/_tkinter.main.build_gui","okay","Configured style of main window")
			
			#create main frame
			log("GUI/_tkinter.main.build_gui","info","Creating main frame")
			guivars.frames.main.main = tk.Frame(guivars.windows.main,bg=CONFIG.gui.style.main.framebg,bd=CONFIG.gui.style.main.framebordersize,relief=CONFIG.gui.style.main.framerelief,width=CONFIG.gui.style.main.size.width,height=CONFIG.gui.style.main.size.height)
			guivars.frames.main.main.grid()
			#configure row size in main frame
			for i in range(8):
				guivars.frames.main.main.rowconfigure(i,weight=1)
			log("GUI/_tkinter.main.build_gui","okay","Main frame created")
			
			#create other widgets on main frame
			_tkinter.main.create_widgets(CONFIG)
			
			log("GUI/_tkinter.main.build_gui","okay","Main GUI builded")
		
		def create_widgets(CONFIG):
			log("GUI/main.create_widgets","info","Creating widgets for user interaction")
			
			log("GUI/main.create_widgets","info","Creating frame for CMD execution")
			guivars.windows.main.update()
			log("GUI/main.create_widgets","debug",f"Main window has a size of [W:{guivars.windows.main.winfo_width()} H:{guivars.windows.main.winfo_height()}]")
			guivars.frames.main.cmdframe = tk.Frame(guivars.frames.main.main,bg=CONFIG.gui.style.main.frames.cmdexec.background,bd=2,relief="sunken")
			guivars.frames.main.cmdframe.grid(row=0,column=0,rowspan=3,sticky="N")
			guivars.elements.main.cmdhistory_txt = ctk.CTkTextbox(guivars.frames.main.cmdframe,fg_color=CONFIG.gui.style.main.frames.cmdexec.entrybg,text_color=CONFIG.gui.style.main.frames.cmdexec.entryfg,state="disabled",width=guivars.windows.main.winfo_width()-20,height=200)
			guivars.elements.main.cmdhistory_txt.grid(row=0,column=0,rowspan=8,columnspan=4)
			guivars.elements.main.cmd_ent = ctk.CTkEntry(guivars.frames.main.cmdframe,fg_color=CONFIG.gui.style.main.frames.cmdexec.entrybg,text_color=CONFIG.gui.style.main.frames.cmdexec.entryfg,placeholder_text_color=CONFIG.gui.style.main.frames.cmdexec.entryph,width=guivars.windows.main.winfo_width()-150,placeholder_text="Enter command")
			guivars.elements.main.cmd_ent.grid(row=8,column=0,columnspan=3,sticky="E",pady=4)
			guivars.elements.main.cmd_ent.bind("<Return>",lambda event:_tkinter.guicmds.main.execcmd(CONFIG)) #lambda event:log("GUI/window/cmd_ent","okay","Keypress on enter detected"))
			guivars.elements.main.cmd_ent.bind("<KP_Enter>",lambda event:_tkinter.guicmds.main.execcmd(CONFIG))
			guivars.elements.main.cmdsend_btn = ctk.CTkButton(guivars.frames.main.cmdframe,fg_color=CONFIG.gui.style.general.buttonbg,hover_color=CONFIG.gui.style.general.buttonhover,text_color=CONFIG.gui.style.general.buttontxt,border_width=CONFIG.gui.style.general.buttonborderwidth,border_color=CONFIG.gui.style.general.buttonborder,text="Execute Command",command=lambda:_tkinter.guicmds.main.execcmd(CONFIG)) #command=lambda:log("GUI/window/cmdsend_btn","okay","Click event detected"))
			guivars.elements.main.cmdsend_btn.grid(row=8,column=3,sticky="W",pady=4)
			log("GUI/main.create_widgets","okay","CMD exec frame created")
			
			log("GUI/main.create_widgets","info","Creating frame for macros")
			guivars.frames.main.macros = tk.Frame(guivars.frames.main.main,height=325,width=1260,background="black") #Per button: [W:84 H:65]
			guivars.frames.main.macros.grid_propagate(False)
			
			guivars.elements.main.macros_btn_lst = []
			for y in range(5):
				guivars.elements.main.macros_btn_lst.append([])
				cury = guivars.elements.main.macros_btn_lst[y]
				for x in range(15):
					try:
						title = guivars.general.show["macros"][f"{x}x{y}"]["name"] if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else ""
						clr = guivars.general.show["macros"][f"{x}x{y}"]["color"] if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else "#f00"
						cury.append(ctk.CTkButton(guivars.frames.main.macros,width=84,height=65,text=title,fg_color="#161616",hover_color="#161616",text_color=CONFIG.gui.style.general.buttontxt,border_width=CONFIG.gui.style.general.buttonborderwidth,border_color=clr,command=eval(f'lambda:_tkinter.guicmds.main.run.macro(guivars.general.config,"{x}x{y}")') if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else eval(f'lambda:log("GUI/window/macro{x}x{y}_btn","okay","Click event detected")')))
						cur = cury[x]
						cur.grid_propagate(False)
						cur.grid(row=y,column=x,padx=0,pady=0)
						cur.bind("<Button-3>",eval(f'lambda event:guivars.elements.main.cmd_ent.insert("end",str(" " if guivars.elements.main.cmd_ent.get()[-1:] != " " else "") + "{x}x{y}")'))
					except Exception as exc: log("GUI/main.create_widgets","warn",f"Failed to create Macro button at {x}x{y} ({exc})")
			
			guivars.frames.main.macros.grid(row=3,column=0,rowspan=5)
			log("GUI/main.create_widgets","okay","Macro frame in main window created")
			
			log("GUI/main.create_widgets","info","Creating cuelist list frame")
			guivars.frames.main.cuelistframe = tk.Frame(guivars.frames.main.main,bg=CONFIG.gui.style.main.frames.cmdexec.background)
			guivars.frames.main.cuelistframe.grid(row=8,column=0)
			guivars.elements.main.cl_btn_lst = []
			guivars.elements.main.cl_desc_lst = []
			log("GUI/main.create_widgets","debug","Generating cuelist buttons")
			for i in range(15):
				guivars.elements.main.cl_desc_lst.append({"title":None,"cue_last_lbl":None,"cue_current_lbl":None,"cue_follow_lbl":None,"state":None})
				guivars.elements.main.cl_btn_lst.append(ctk.CTkButton(guivars.frames.main.cuelistframe,text="",width=84,height=150,fg_color=CONFIG.gui.style.general.buttonbg,hover_color=CONFIG.gui.style.general.buttonbg,text_color=CONFIG.gui.style.general.buttontxt,border_width=CONFIG.gui.style.general.buttonborderwidth,border_color=CONFIG.gui.style.general.buttonborder,command=eval(f'lambda:log("GUI/window/cl{i}_btn","okay","Click event detected")'))) #Width should be 85.33
				current = guivars.elements.main.cl_btn_lst[i]
				current.grid_propagate(False)
				current.grid(row=0,column=i)
				current.bind("<Button-3>",eval(f'lambda event:log("GUI/window/cl{i}_btn","okay","Menu click event detected")'))
				
				current.columnconfigure(0,weight=1)
				for e in range(5): current.rowconfigure(e,weight=1)
				
				log("GUI/main.create_widgets","debug",f"Creating GUI for Cuelist button at CL{i}")
				mthd = "grid"
				try:
					curitm = guivars.elements.main.cl_desc_lst[i]
					
					curitm["title"] = ctk.CTkLabel(guivars.elements.main.cl_btn_lst[i],text=f"CL{i}",font=("Roboto",13),text_color="white")
					if mthd == "grid":
						curitm["title"].grid(row=0,column=0,padx=0,pady=0)
					curitm["cue_last_lbl"] = ctk.CTkLabel(current,text="LastCue",font=("Roboto",10),text_color="white")
					if mthd == "grid":
						curitm["cue_last_lbl"].grid(row=1,column=0,padx=0,pady=0)
					curitm["cue_current_lbl"] = ctk.CTkLabel(current,text="CurCue",font=("Roboto",10),text_color="white")
					if mthd == "grid":
						curitm["cue_current_lbl"].grid(row=2,column=0,padx=0,pady=0)
					curitm["cue_follow_lbl"] = ctk.CTkLabel(current,text="FollowCue",font=("Roboto",10),text_color="white")
					if mthd == "grid":
						curitm["cue_follow_lbl"].grid(row=3,column=0,padx=0,pady=0)
					curitm["state"] = ctk.CTkLabel(current,text="Inactive",font=("Roboto",10),text_color="white",bg_color="#f00")
					if mthd == "grid":
						curitm["state"].grid(row=4,column=0,padx=2,pady=0,sticky="ew")
					
					for elm in curitm:
						curitm[elm].bind("<Button-1>",eval(f'lambda event:log("GUI/window/cl{i}_btn","okay","Click event detected")'))
						curitm[elm].bind("<Button-3>",eval(f'lambda event:log("GUI/window/cl{i}_btn","okay","Menu click event detected")'))
					
					if mthd == "pack":
						for elm in curitm: curitm[elm].pack(padx=0,pady=0)
				except Exception as exc:
					log("GUI/main.create_widgets","error",f"Some error occured while trying to generate Cuelist Buttons ({exc})")
				
			log("GUI/main.create_widgets","okay","Cuelist list frame created")
			
			log("GUI/main.create_widgets","okay","Done")
		
		def keybind_config():
			log("GUI/main.keybind_config","info","Configuring keybinds")
			for loc in list(guivars.general.show["keybinds"].keys()):
				x,y = map(int,loc.split("x"))
				kb = guivars.general.show["keybinds"][loc]
				try:
					log(f"GUI/main.keybind_config."+cFN(),"debug",f"Trying to configure key event {repr(kb)} to execute macro at {repr(loc)}")
					guivars.windows.main.bind(kb,eval(f'lambda event:_tkinter.guicmds.main.run.macro(guivars.general.config,"{x}x{y}")') if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else eval(f'lambda event:log("GUI/window/macroexec_from_key/{kb[1:-1]}","okay","Click event detected")'))
					guivars.windows.screen2.mainclass.bind(kb,eval(f'lambda event:_tkinter.guicmds.main.run.macro(guivars.general.config,"{x}x{y}")') if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else eval(f'lambda event:log("GUI/window/macroexec_from_key/{kb[1:-1]}"","okay","Click event detected")'))
				except Exception as exc: log(f"GUI/main.create_widgets."+cFN(),"warn",f"Failed to configure macro keybind for macro at {x}x{y} ({exc})")
			log("GUI/main.keybind_config","okay","Keybinds configured")
		
		def mainloop(CONFIG):
			log("GUI/main.mainloop","info","Initializing mainloop of main window\n\nIN MAINLOOP/PROGRAM EVENTS\n"+"="*50+"\n\n\n\n\n")
			guivars.windows.main.mainloop()
			log("GUI/main.mainloop","info","Mainloop ended")
			
			#Save showfile
			if CONFIG.preferences.dmxcontrol.isclient:
				log(cFN(),"info","Saving showfile")
				try:
					with open(CONFIG.preferences.general.currentshow,"w+") as fle: jsdump(guivars.general.show,fle)
					log(cFN(),"okay","Show saved")
				except Exception as exc:
					log(cFN(),"fatal",f"Could not save showfile ({exc})")
					NewPyDMX.tools.dialogs.error("Show save failed","Failed to save show. Please check the logs and message the developers to correct this issue.")
		
		def destroy(CONFIG):
			log("GUI/main.destroy","info","Destroying main window")
			try:
				guivars.windows.main.destroy()
				log("GUI/main.destroy","okay","Main window destroyed")
			except Exception as exc:
				log("GUI/main.destroy","error",f"Failed to destroy main window ({exc})")
				raise errs.ExecutionError(f"Failed to destroy main window ({exc})")
			
			#Save showfile
			if CONFIG.preferences.dmxcontrol.isclient:
				log("GUI/_tkinter.main.destroy"+cFN(),"info","Saving showfile")
				try:
					with open(CONFIG.preferences.general.currentshow,"w+") as fle: jsdump(guivars.general.show,fle)
					log("GUI/_tkinter.main.destroy"+cFN(),"okay","Show saved")
				except Exception as exc:
					log("GUI/_tkinter.main.destroy"+cFN(),"fatal",f"Could not save showfile ({exc})")
					NewPyDMX.tools.dialogs.error("Show save failed","Failed to save show. Please check the logs and message the developers to correct this issue.")

class pyqt():
	class RightClickButton(QPushButton):
		def __init__(self,*args,right_click=None,**kwargs):
			super().__init__(*args,**kwargs)
			self.right_click = right_click
		
		def mousePressEvent(self,event):
			try:
				if event.button() == Qt.RightButton and self.right_click:
					self.right_click(event)
				else:
					super().mousePressEvent(event)
			except Exception as exc:
				log("GUI/pyqt.RightClickButton.mousePressEvent","error",f"Failed to execute command corresponding to event: {exc}")

	# ────────────────────────────────────────────────
	# GUI COMMANDS
	# ────────────────────────────────────────────────
	class guicmds():
		
		def move_window_to_screen(window, screen_index):
			"""screen = QApplication.screens()[screen_index]
			
			# Attach window to screen BEFORE showing
			window.windowHandle().setScreen(screen)
			
			# Move to screen's origin
			geo = screen.geometry()
			window.move(geo.x(), geo.y())"""
			
			screens = QApplication.screens()

			if screen_index >= len(screens):
				screen = QApplication.primaryScreen()
			else:
				screen = screens[screen_index]
			
			geo = screen.geometry()
			
			# Move and resize BEFORE fullscreen
			window.setGeometry(
				geo.x(),
				geo.y(),
				geo.width(),
				geo.height()
			)
			
			# Optional: remove decorations (kiosk mode)
			window.setWindowFlags(Qt.FramelessWindowHint)
			
			# Show fullscreen
			window.showFullScreen()

		@staticmethod
		def quit(CONFIG,shutdown=False,saveshow=True):
			"""log("GUI/pyqt.guicmds.quit","info","Quitting PyDMX")
			guivars.general.dmxComm.sendCommand("!noreply channels allOff", False)
			time.sleep(1)
			guivars.general.dmxComm.sendCommand("!noreply render stop", False)
			time.sleep(1)
			guivars.general.dmxComm.sendCommand("!noreply channels allOff", False)
			guivars.general.mthr_active.clear()
			if CONFIG.preferences.dmxcontrol.isclient:
				log("GUI/pyqt.guicmds."+cFN(),"info","Saving showfile")
				try:
					with open(CONFIG.preferences.general.currentshow,"w+") as fle: jsdump(guivars.general.show,fle)
					log("GUI/pyqt.guicmds."+cFN(),"okay","Show saved")
				except Exception as exc:
					log("GUI/pyqt.guicmds"+cFN(),"fatal",f"Could not save showfile ({exc})")
					NewPyDMX.tools.dialogs.error("Show save failed","Failed to save show. Please check the logs and message the developers to correct this issue.")
			save_config()
			guivars.windows.main.close()
			QApplication.quit()
			sys.exit()"""
			log("GUI/pyqt.guicmds."+cFN(),"info","Quitting PyDMX due to User request\n\n\n\n\n"+"="*50+"\nAFTER MAINLOOP/PROGRAM EVENTS\n\n")
			#log("GUI/pyqt.guicmds."+cFN(),"info","Quitting PyDMX due to User request")
			guivars.general.dmxComm.sendCommand("!noreply channels allOff",expectResponse=False)
			time.sleep(1)
			guivars.general.dmxComm.sendCommand("!noreply render stop",expectResponse=False)
			time.sleep(1)
			guivars.general.dmxComm.sendCommand("!noreply channels allOff",expectResponse=False)
			guivars.general.mthr_active = []
			if saveshow == True: save_config()
			if not shutdown:
				log("GUI/pyqt.guicmds."+cFN(),"okay","Destroying windows, executing 'sys.exit()'")
				guivars.windows.main.close()
				QApplication.quit()
				sys.exit()
			else:
				log("GUI/pyqt.guicmds."+cFN(),"warn","Executing halt commands ('halt || shutdown -s -t 0 -c \"Shutdown of console requested\"')")
				try: shcall(["halt","||","shutdown","-s","-t","10","-c","'Shutdown","of","console","requested'"])
				except Exception as exc:
					log("GUI/pyqt.guicmds."+cFN(),"error",f"Shutdown failed, destroying GUI and executing 'sys.exit()' ({exc})")
					guivars.windows.main.close()
					QApplication.quit()
					sys.exit()

		@staticmethod
		def execcmd(CONFIG, cmdtext, expectResponse=True):
			#Replace variables
			log("GUI/pyqt.guicmds."+cFN(),"info","Replacing variables in cmd string")
			splt = cmdtext.split("$")
			for i in range(len(splt)-1):
				name = splt[i+1].split()[0]
				log("GUI/pyqt.guicmds."+cFN(),"debug",f"Trying to load value of '{name}'")
				try: val = guivars.general.usrvars[name]
				except KeyError: return "ERR VarNotFound"
				log("GUI/pyqt.guicmds."+cFN(),"debug",f"Variable '{name}' has a value of {repr(val)}")
				splt2 = splt[i+1].split()[1:]
				splt[i+1] = f"{repr(val)} {' '.join(splt2)}"
			cmdtext = ''.join(splt)
			log("GUI/pyqt.guicmds."+cFN(),"debug",f"Resulting command string: {repr(cmdtext)}")
			log("GUI/pyqt.guicmds."+cFN(),"okay","Variables in cmd string replaced")
			
			#Replace fixtures
			log("GUI/pyqt.guicmds."+cFN(),"info","Replacing fixtures in cmd string")
			splt = cmdtext.split("fixt=")
			for i in range(len(splt)-1):
				name = splt[i+1].split()[0]
				val = ""
				try: fixt = guivars.general.show["fixtures"][name.split(".")[0]]
				except KeyError:
					log("GUI/pyqt.guicmds."+cFN(),"error",f"Fixture {repr(name.split('.')[0])} not found")
					return "ERR FixtNotFound"
				universe = fixt["universe"]
				try: addr = fixt["addr"] + fixt["channels"].index(name.split(".")[1])
				except IndexError:
					log("GUI/pyqt.guicmds."+cFN(),"error",f"No channel information supplied for fixture")
					return "ERR NoChannelInfoSupplied"
				except ValueError:
					log("GUI/pyqt.guicmds."+cFN(),"error",f"Channel {repr(name.split('.')[1])} is not existant for fixture {repr(name.split('.')[0])}")
					return f"ERR ChannelNotFound {repr(name.split('.')[1])}"
				val = f"universe='{universe}' addr='{addr}'"
				splt2 = splt[i+1].split()[1:]
				splt[i+1] = f"{val} {' '.join(splt2)}"
			cmdtext = ''.join(splt)
			log("GUI/pyqt.guicmds."+cFN(),"debug",f"Resulting command string: {repr(cmdtext)}")
			
			splt = cmdtext.split("§")
			for i in range(len(splt)-1):
				name = splt[i+1].split()[0]
				val = ""
				try: fixt = guivars.general.show["fixtures"][name.split(".")[0]]
				except KeyError:
					log("GUI/pyqt.guicmds."+cFN(),"error",f"Fixture {repr(name.split('.')[0])} not found")
					return "ERR FixtNotFound"
				universe = fixt["universe"]
				try: addr = fixt["addr"] + fixt["channels"].index(str(name.split(".")[1]).split(",")[0])
				except IndexError:
					log("GUI/pyqt.guicmds."+cFN(),"error",f"No channel information supplied for fixture")
					return "ERR NoChannelInfoSupplied"
				except ValueError:
					log("GUI/pyqt.guicmds."+cFN(),"error",f"Channel {repr(name.split('.')[1])} is not existant for fixture {repr(name.split('.')[0])}")
					return f"ERR ChannelNotFound {repr(name.split('.')[1])}"
				val = f"({universe},{addr}),"
				splt2 = splt[i+1].split(",")[1:]
				splt[i+1] = f"{val}{' '.join(splt2)}"
			cmdtext = ''.join(splt)
			log("GUI/pyqt.guicmds."+cFN(),"debug",f"Resulting command string: {repr(cmdtext)}")
			
			log("GUI/pyqt.guicmds."+cFN(),"okay","Fixtures in cmd string replaced")
			
			#Replace dimmer values
			log("GUI/pyqt.guicmds."+cFN(),"info","Applying dimmer onto command")
			cnv = True
			if len(cmdtext.split("value=")) < 2:
				cnv = False
				log("GUI/pyqt.guicmds."+cFN(),"warn","No 'value' parameter supplied")
			if cnv:
				beforeval = cmdtext.split("value=")[0]
				valtxt = cmdtext.split("value=")[1].split(" ")[0]
				try: afterval = cmdtext.split("value=")[1].split(" ")[1]
				except IndexError: afterval = ""
				log("GUI/pyqt.guicmds."+cFN(),"debug",f"Value defined in command is: {repr(valtxt)}")
			if (valtxt[0],valtxt[-1]) not in (("'","'"),('"','"')):
				cnv = False
				log("GUI/pyqt.guicmds."+cFN(),"warn",f"Could not apply dimmer (String not completed)")
			if cnv:
				for char in valtxt:
					if char not in "1234567890'" and char not in ('"'):
						log("GUI/pyqt.guicmds."+cFN(),"warn",f"Could not apply dimmer (Invailid character {repr(char)})")
						cnv = False
			if cnv:
				val = int(eval(valtxt))
				final = int((val/100)*applyDimmer)
				log("GUI/pyqt.guicmds."+cFN(),"debug",f"Dimmer applied to value ({val} -> {final})")
				cmdtext = f"{beforeval}value='{final}' {afterval}"
				log("GUI/pyqt.guicmds."+cFN(),"okay",f"Command changed")
			
			#Execute command
			if cmdtext.split()[0] == "!IF":
				log("GUI/pyqt.guicmds."+cFN(),"info","Found IF condition in command")
				var = cmdtext.split()[1]
				op = cmdtext.split()[2]
				val = cmdtext.split()[3]
				if len(cmdtext.split()) > 4: act = cmdtext.split()[4]
				else: act = "!RETURN"
				if var not in list(guivars.general.usrvars.keys()):
					log("GUI/pyqt.guicmds."+cFN(),"error","Requested variable not existant")
					return "ERR VarNotFound"
				if op not in ("==",">",">=","<","<=","!=","not"):
					log("GUI/pyqt.guicmds."+cFN(),"error",f"Invailid operation in conditional command: {op}")
					return "ERR InvailidOperation"
				vartxt = f"guivars.general.usrvars['{var}']"
				if not eval(f"{vartxt} {op} {val}"):
					log("GUI/pyqt.guicmds."+cFN(),"warn","Condition not True, returning")
					return "OK ConditionChecked False"
				if act == "!RETURN":
					log("GUI/pyqt.guicmds."+cFN(),"debug","No command execution requested, returning")
					return "OK ConditionChecked True"
				elif act != "!RUN":
					log("GUI/pyqt.guicmds."+cFN(),"error","Invailid action specification at end of condition in command - Returning")
					return "ERR InvailidConditionAction"
				bfr = cmdtext.split()
				for i in range(5): del bfr[0]
				cmdtext = ' '.join(bfr)
				log("GUI/pyqt.guicmds."+cFN(),"okay","Proceeding with command execution")
			
			if cmdtext.split()[0] not in ("exit","halt","shutdown","cuelist","quit","help","clear","","var","new","edit","copy","delete","wait"):
				return guivars.general.dmxComm.sendCommand(cmdtext, expectResponse)

			if cmdtext.startswith("help"):
				with open("dmxServer.help.txt","r") as fle: help = ''.join(fle.readlines())
				with open("guicommands.txt","r") as fle: help = help + "\n" + ''.join(fle.readlines())
				help = "HELP\n---------------\n"+help
				w = guivars.elements.main.cmdhistory_txt
				w.setReadOnly(False)
				w.insertPlainText(help + "\n")
				w.setReadOnly(True)
				guivars.windows.main.cmdhistory.moveCursor(QTextCursor.End)

			elif cmdtext.split()[0] in ("halt","shutdown","quit"):
				log("GUI/pyqt.guicmds."+cFN(),"info","Shutdown was requested")
				ret = tkMB.askyesnocancel("Shutdown requested","Do you really want to shutdown the controller without saving the show?\n- 'Yes' will just shutdown the controller\n- 'No' will first save the show",parent=guivars.windows.main)
				if ret == None:
					log("GUI/pyqt.guicmds."+cFN(),"warn","User aborted shutdown")
					return "ERR Aborted"
				if ret == True: log("GUI/pyqt.guicmds."+cFN(),"info","User wants to shutdown without saving the showfile")
				log("GUI/pyqt.guicmds."+cFN(),"warn","Shutting down console")
				_tkinter.guicmds.quit(CONFIG,shutdown=True,saveshow=True if ret == True else False)
			
			elif cmdtext.split()[0] in ("exit"):
				log("GUI/pyqt.guicmds."+cFN(),"info","Program exit was requested")
				ret = tkMB.askyesnocancel("Shutdown requested","Do you really want to exit the program without saving the show?\n- 'Yes' will just quit the program\n- 'No' will first save the show",parent=guivars.windows.main)
				if ret == None:
					log("GUI/pyqt.guicmds."+cFN(),"warn","User aborted exit")
					return "ERR Aborted"
				if ret == True: log("GUI/pyqt.guicmds."+cFN(),"info","User wants to exit program without saving the showfile")
				log("GUI/pyqt.guicmds."+cFN(),"warn","Quitting program")
				_tkinter.guicmds.quit(CONFIG,shutdown=False,saveshow=True if ret == True else False)
			
			elif cmdtext.split()[0] in ("wait"):
				log("GUI/pyqt.guicmds."+cFN(),"info",f"Waiting for {cmdtext.split()[1]} seconds")
				try: time.sleep(float(cmdtext.split()[1]))
				except Exception as exc:
					log("GUI/pyqt.guicmds."+cFN(),"error",f"Could not interrupt code execution with command wait ({exc})")
					return "ERR Failed"
				return "OK Waited"
			
			elif cmdtext.split()[0] == "edit":
				if cmdtext.split()[1] == "preference":
					if cmdtext.split()[2] == "gui/framework":
						log("GUI/pyqt.guicmds."+cFN(),"info","User requested to change GUI Framework preference, building up dialog")
						try:
							_set = cmdtext.split()[3]
							if _set not in ("qt","tk"): raise Exception("")
						except: _set = None
						if _set == None:
							ret = NewPyDMX.tools.dialogs.yesno("Edit Preference",f"Do you want the GUI to be build up with tkinter ('yes') or PyQT ('no')?\nHint: tkinter is more failure-proof in general and will recieve any updates at first")
							guivars.general.config["gui"]["framework"] = "tk" if ret else "qt"
						else: guivars.general.config["gui"]["framework"] = dc(_set)
						log("GUI/pyqt.guicmds."+cFN(),"debug",f"User chose framework '{'tk' if ret else 'qt'}' for GUI")
						log("GUI/pyqt.guicmds."+cFN(),"okay","Preference of GUI framework changed")
						return "OK ChangedPreference (Please restart program)"
					elif cmdtext.split()[2] == "dmx/server/addr":
						log("GUI/pyqt.guicmds."+cFN(),"info","User requested to change DMX Server address, prompting for new")
						ret, ok = QInputDialog.getText(None,"Set Server Addr.","Please enter new address of DMX Server (You'll need to restart program to let changes be applied)")
						if not ok or len(ret.split(".")) != 4:
							log("GUI/pyqt.guicmds."+cFN(),"error",f"User entered invailid IP: {repr(ret)}")
							NewPyDMX.tools.dialogs.error("Set Server Addr. failed",f"Failed to change IP address: The entered IP ({repr(ret)} is invailid")
							return "ERR InvailidAddr"
						guivars.general.config["preferences"]["dmxcontrol"]["ip"] = ret
						log("GUI/pyqt.guicmds."+cFN(),"debug",f"Set server addres to {repr(ret)}")
						log("GUI/pyqt.guicmds."+cFN(),"okay","Server address changed")
						return "OK AddrChanged"
					elif cmdtext.split()[2] == "dmx/server/port":
						log("GUI/pyqt.guicmds."+cFN(),"info","User requested to change DMX Server port, prompting for new")
						ret, ok = QInputDialog.getInt(None,"Set Server Port","Please enter new port of DMX Server (You'll need to restart program to let changes be applied)")
						if not ok or ret > 35676:
							log("GUI/pyqt.guicmds."+cFN(),"error",f"User entered invailid Port: {repr(ret)}")
							NewPyDMX.tools.dialogs.error("Set Server Port failed",f"Failed to change Port: The entered port ({repr(ret)} is invailid")
							return "ERR InvailidPort"
						guivars.general.config["preferences"]["dmxcontrol"]["port"] = ret
						log("GUI/pyqt.guicmds."+cFN(),"debug",f"Set server port to {ret}")
						log("GUI/pyqt.guicmds."+cFN(),"okay","Server port changed")
						return "OK PortChanged"
					elif cmdtext.split()[2] == "show/name":
						log("GUI/pyqt.guicmds."+cFN(),"info","User requested to change show name, prompting for new")
						root = tk.Tk()
						root.withdraw()
						ret, ok = QInputDialog.getText(None,"Change show name","Please enter new name of show")
						root.destroy()
						if not ok:
							log("GUI/pyqt.guicmds."+cFN(),"error","User skipped dialog, aborting show renaming process")
							return "ERR RenamingDialogSkipped"
						if ret == None or ret == "":
							log("GUI/pyqt.guicmds."+cFN(),"error",f"Invailid show name ({repr(ret)})")
							return f"ERR InvailidShowName {repr(ret)}"
						guivars.general.show["name"] = ret
						newpath = '/'.join(CONFIG.preferences.general.currentshow.split("/")[:-1]) + "/" + ret + ".json"
						log("GUI/pyqt.guicmds."+cFN(),"info",f"Moving current showfile from {repr(CONFIG.preferences.general.currentshow)} to {repr(newpath)}")
						try:
							plpath(CONFIG.preferences.general.currentshow).rename(newpath)
							CONFIG.preferences.general.currentshow = dc(newpath)
							guivars.general.config["preferences"]["general"]["currentshow"] = dc(newpath)
						except Exception as exc:
							log("GUI/pyqt.guicmds."+cFN(),"error",f"Failed to move showfile ({exc})")
						log("GUI/pyqt.guicmds."+cFN(),"debug",f"New show name is: {repr(ret)}")
						log("GUI/pyqt.guicmds."+cFN(),"okay","Show name changed")
						return "OK ShowNameChanged"
				
				elif cmdtext.split()[1] == "fixture":
					edit = True
					log("GUI/pyqt.guicmds."+cFN(),"info","Prepearing for fixture editing")
					try: name = cmdtext.split()[2]
					except IndexError:
						log("GUI/pyqt.guicmds."+cFN(),"error",f"Fixture name has to be supplied")
						return "ERR NoNameSupplied"
					try: fixt = guivars.general.show["fixtures"][name]
					except KeyError:
						log("GUI/pyqt.guicmds."+cFN(),"error",f"Fixture {repr(name)} not found")
						return f"ERR FixtNotFound {repr(name)}"
					
					while edit == True:
						log("GUI/pyqt.guicmds."+cFN(),"info","Starting edit possibility for user")
						r = tk.Tk()
						r.withdraw()
						nname, nok = QInputDialog.getText(None,f"Edit fixture {repr(name)}","Enter name of fixture",text=name)
						channelsstr, cok = QInputDialog.getText(None,f"Edit fixture {repr(name)}","Please enter the channels of the fixture:",text=';'.join(fixt["channels"]))
						universe, uok = QInputDialog.getInt(None,f"Edit fixture {repr(name)}","Please enter the universe of the fixture. Keep in mind that the first Universe is universe 0, and so on.",value=fixt["universe"])
						addr, aok = QInputDialog.getInt(None,f"Edit fixture {repr(name)}","Please enter the address of the fixture. It can be any integer from 1 to 512",value=fixt["addr"],min=1,max=512)
						
						if False not in (nok,cok,uok,aok):
							ret = NewPyDMX.tools.dialogs.yesno(f"Edit fixture {repr(name)}",f"Is this data correct?\nname={repr(nname)}\nuniverse={repr(universe)}\naddr={repr(addr)}\nchannels={repr(channelsstr)}")
							if ret == True:
								log("GUI/pyqt.guicmds."+cFN(),"okay","User confirmed edited data for fixture, validating entered data")
								edit = False
							else:
								log("GUI/pyqt.guicmds."+cFN(),"okay","User denied that edited data for fixture is correct, asking for retry")
								ret = NewPyDMX.tools.dialogs.retrycancel(f"Edit fixture {repr(name)}",f"Do you want to retry editing the fixture?")
								if ret == False:
									log("GUI/pyqt.guicmds."+cFN(),"okay","Aborting fixture editing process due to user selection")
									r.destroy()
									return "OK Aborted"
								else: log("GUI/pyqt.guicmds."+cFN(),"okay","User requested retry of fixture editing process")
						
						if False in (nok,cok,uok,aok):
							log("GUI/pyqt.guicmds."+cFN(),"warn","Some setting the user made is empty.")
							ret = NewPyDMX.tools.dialogs.retrycancel(f"Edit fixture {repr(name)}",f"Some of the data you could change is empty. Do you want to retry?")
							if ret == False:
								log("GUI/pyqt.guicmds."+cFN(),"okay","User chose to abort fixture editing process")
								r.destroy()
								return "OK Aborted"
					
					log("GUI/pyqt.guicmds."+cFN(),"info","Validating entered changes")
					
					channels = channelsstr.split(";")
					editname = True
					editaddr = True
					editaddrcmt = []
					
					log("GUI/pyqt.guicmds."+cFN(),"debug",f"Validating fixture name {repr(nname)}")
					for char in (" ","\\","'",'"',".","/","{","}","[","]","=","$"):
						if char in nname:
							log("GUI/pyqt.guicmds."+cFN(),"error",f"Character {repr(char)} isn't allowed to be used in a fixture's name")
							editname = False
					
					for fixtname in list(guivars.general.show["fixtures"].keys()):
						fixt = guivars.general.show["fixtures"][fixtname]
						if fixtname != name:
							if nname == fixtname: editname = False
							if ((fixt["addr"],fixt["universe"]) == (addr,universe)) or (fixt["universe"] == universe and addr+(len(channels)-1) == fixt["addr"]) or (fixt["universe"] == universe and (fixt["addr"] <= addr and (fixt["addr"] + len(fixt["channels"]) > addr))):
								log("GUI/pyqt.guicmds."+cFN(),"error",f"Address of new fixture would overlap with other fixture")
								editaddr = False
								editaddrcmt.append(fixtname)
					
					save = True
					if False in (editname,editaddr):
						ret = NewPyDMX.tools.dialogs.yesno(f"Edit fixture {repr(name)}",f"{'Name can not get changed either because new is used or invailid' if not editname else ''}{'Channels, Address and Universe can not be changed because they would then overlap with other fixtures: '+';'.join(editaddrcmt) if not editaddr else ''}\nDo you want to save the vailid settings?")
						if ret == False:
							save = False
							log("GUI/pyqt.guicmds."+cFN(),"okay","User chose to not only save the valid settings")
					
					if save:
						fixtdta = guivars.general.show["fixtures"][name]
						del guivars.general.show["fixtures"][name]
						if editaddr == True:
							fixtdta["channels"] = channels
							fixtdta["addr"] = addr
							fixtdta["universe"] = universe
						guivars.general.show["fixtures"][nname if editname else name] = dc(fixtdta)
						log("GUI/pyqt.guicmds."+cFN(),"okay","Data saved")
						NewPyDMX.tools.dialogs.info(f"Edit fixture {repr(name)}","Changes saved")
						r.destroy()
						return "OK Saved"
					
					r.destroy()
					return "OK Aborted"
			
			elif cmdtext.split()[0] == "delete":
				if cmdtext.split()[1] == "macro":
					try:
						pos = cmdtext.split()[2]
						if len(pos.split("x")) != 2:
							return "ERR InvailidPos"
						if pos not in list(guivars.general.show["macros"].keys()):
							log("GUI/pyqt.guicmds."+cFN(),"error",f"No macro found on position {repr(pos)}")
							return "ERR NotFound"
						log("GUI/pyqt.guicmds."+cFN(),"info",f"Trying to delete macro at {repr(pos)}")
						
						log("GUI/pyqt.guicmds."+cFN(),"info",f"Disabling macro thread of macro at {repr(pos)} if running")
						try:
							del guivars.general.mthr_active[guivars.general.mthr_active.index(pos)]
							log("GUI/pyqt.guicmds."+cFN(),"okay","Macro thread disabled")
						except Exception as exc: log("GUI/_tkinter.guicmds."+cFN(),"okay","Macro thread for macro wasn't active")
						
						del guivars.general.show["macros"][pos]
						
						x,y = map(int,pos.split("x"))
						
						guivars.elements.main.macros_btn_lst[y][x].setText("")
						guivars.elements.main.macros_btn_lst[y][x].setStyleSheet(f"background:#161616;border:2px solid #444;color:white")
						try: guivars.elements.main.macros_btn_lst[y][x].clicked.disconnect()
						except: pass
						guivars.elements.main.macros_btn_lst[y][x].clicked.connect(eval(f'lambda event:log("GUI/window/macro{x}x{y}_btn","okay","Click event detected")'))
						
						log("GUI/pyqt.guicmds."+cFN(),"okay",f"Macro at {repr(pos)} deleted")
						return "OK MacroDeleted"
					except Exception as exc:
						log("GUI/pyqt.guicmds."+cFN(),"error",f"Failed to delete macro at {repr(pos)}")
						return "ERR FailedToDelete"
			
			elif cmdtext.split()[0] == "new":
				if cmdtext.split()[1] == "macro":
					r = tk.Tk()
					r.withdraw()
					pos = cmdtext.split()[2]
					if len(pos.split("x")) != 2:
						NewPyDMX.tools.dialogs.error(f"Error",f"Failed to create Macro: Invailid position")
						r.destroy()
						return "ERR InvailidPos"
					name,nok = QInputDialog.getText(None,f"Create Macro","Please enter the name of the new macro")
					rstOE = NewPyDMX.tools.dialogs.yesno(f"Create Macro {repr(name)}",f"Reset changed DMX Values on end?")
					repOE = NewPyDMX.tools.dialogs.yesno(f"Create Macro {repr(name)}",f"Repeat macro code until it is stopped?")
					clr,cok = QInputDialog.getText(None,f"Create Macro {repr(name)}",f"Enter color of macro in grid (Can be: red/orange/yellow/green/cyan/blue/purple/white)")
					if clr not in ("red","orange","yellow","green","cyan","blue","purple","white"):
						NewPyDMX.tools.dialogs.error(f"Error",f"Failed to create Macro: Invailid color")
						r.destroy()
						return "ERR InvailidColor"
					
					if not nok or not cok:
						log("GUI/pyqt.guicmds."+cFN(),"error","Either 'name' or 'color' dialog got no vailid value")
						return "ERR InvailidColorOrName"
					
					guivars.general.show["macros"][pos] = {"name":name,"resetOnEnd":rstOE,"repeatOnEnd":repOE,"code":[],"color":clr}
					
					x,y = map(int,pos.split("x"))
					try:
						title = guivars.general.show["macros"][f"{x}x{y}"]["name"] if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else ""
						clr = guivars.general.show["macros"][f"{x}x{y}"]["color"] if f"{x}x{y}" in list(guivars.general.show["macros"].keys()) else "#444"
						guivars.elements.main.macros_btn_lst[y][x].setText(title)
						guivars.elements.main.macros_btn_lst[y][x].setStyleSheet(f"background:#161616;border:2px solid {clr};color:white")
						try: guivars.elements.main.macros_btn_lst[y][x].clicked.disconnect()
						except: pass
						guivars.elements.main.macros_btn_lst[y][x].clicked.connect(lambda _,l=pos:pyqt.guicmds.main.run.macro(CONFIG,l))
					except Exception as exc: log("GUI/pyqt.guicmds."+cFN(),"error",f"Configure macro button for new macro at {x}x{y} ({exc})")
					
					r.destroy()
					log("GUI/pyqt.guicmds."+cFN(),"okay","Macro created")
					return "OK Macro created"
				elif cmdtext.split()[1] == "fixture":
					showgui = False
					root = tk.Tk()
					root.withdraw()
					if len(cmdtext.split()) < 4:
						showgui = True
						proceed = False
						name = None
						channels = None
						universe = None
						addr = None
						while proceed == False:
							if name == None: name, nok = QInputDialog.getText(None,"Create fixture","Please enter the name of the new fixture")
							if channels == None: channels, cok = QInputDialog.getText(None,f"Create fixture {repr(name)}","Please enter the channels of the new fixture.\nPlease split with ';'. For example, use the following channel names:\ndimm / red / yellow / green / cyan / blue / magenta / white / pan / tilt / span / stilt / zoom / shutter")
							if universe == None: universe, uok = QInputDialog.getInt(None,f"Create fixture {repr(name)}","Please enter the universe of the Fixture. Keep in mind that the first Universe has the number '0' and so on.",value=0)
							if addr == None: addr, aok = QInputDialog.getInt(None,f"Create fixture {repr(name)}","Please enter the addr of the Fixture. In can be any integer from 1 to 512.",min=1,max=512)
							
							if False in (nok,cok,uok,aok):
								proceed = False
								ret = NewPyDMX.tools.dialogs.retrycancel("Create fixture failed","Some of the data you have entered for new fixture creation isn't given. Retry or cancel new fixture creation.")
								if ret == False:
									log("GUI/pyqt.guicmds."+cFN(),"okay","User chose to exit fixture creation dialog")
									return "OK Aborted"
							else:
								ret = NewPyDMX.tools.dialogs.yesno(f"Create fixture {repr(name)}",f"Is this data correct?\nname={repr(name)}\nuniverse={repr(universe)}\naddress={repr(addr)}\nchannels={repr(channels)}")
								if ret == False:
									log("GUI/pyqt.guicmds."+cFN(),"okay","User denied fixture creation due to wrong data entered")
									return "OK Aborted"
								proceed = True
						cmdtext = f"new fixture {name} {channels} addr={addr} universe={universe}"
					
					if not showgui: root.destroy()
					
					if len(cmdtext.split()) >= 4: #Would mean "new fixture NAME channel1;channel2;channel3 addr=1 (universe=0)
						log("GUI/pyqt.guicmds."+cFN(),"info","Trying to create new fixture from command")
						name = cmdtext.split()[2]
						channels = cmdtext.split()[3].split(";")
						addr = 1
						universe = 0
						try:
							for word in cmdtext.split()[-2:]:
								wlst = word.split("=")
								if "'" in wlst[1] and "{" not in wlst[1]:
									if wlst[0] == "addr": addr = int(eval(wlst[1]))
									elif wlst[0] == "universe": universe = int(eval(wlst[1]))
								else:
									if wlst[0] == "addr": addr = int(wlst[1])
									elif wlst[0] == "universe": universe = int(wlst[1])
						except Exception as exc:
							log("GUI/pyqt.guicmds."+cFN(),"error",f"Failed to create new fixture from command ({exc})")
							if showgui: NewPyDMX.tools.dialogs.error("Creating new fixture failed",f"Failed to load fixture data ({exc})")
							if showgui: root.destroy()
							return f"ERR {'_'.join(str(exc).split())}"
						
						log("GUI/_tkinter.guicmds."+cFN(),"debug",f"Got fixture data: name={repr(name)} channels={repr(channels)} addr={addr} universe={universe}")
						
						if addr < 1 or addr > 512:
							log("GUI/pyqt.guicmds."+cFN(),"error",f"Addr ({addr}) has to be between 1 and 512")
							if showgui: NewPyDMX.tools.dialogs.error("Creating new fixture failed",f"DMX Address of Fixture is not between 1 and 512 ({addr})")
							if showgui: root.destroy()
							return f"ERR DmxAddressOutOfRange {addr}"
						
						log("GUI/pyqt.guicmds."+cFN(),"info","Checking if fixture configuration is vailid & available")
						for char in (" ","\\","'",'"',".","/","{","}","[","]","=","$"):
							if char in name:
								log("GUI/pyqt.guicmds."+cFN(),"error",f"Character {repr(char)} isn't allowed to be used in a fixture's name")
								if showgui: NewPyDMX.tools.dialogs.error("Creating new fixture failed",f"Invailid character ({repr(char)}) used in fixture name")
								if showgui: root.destroy()
								return f"ERR InvailidCharUsed {repr(char)}"
						
						for fixtname in list(guivars.general.show["fixtures"].keys()):
							fixt = guivars.general.show["fixtures"][fixtname]
							if fixtname == name:
								log("GUI/pyqt.guicmds."+cFN(),"error",f"Chosen fixture name is already existing ({repr(fixtname)})")
								if showgui: NewPyDMX.tools.dialogs.error("Creating new fixture failed",f"Fixture with chosen name ({repr(name)}) is already existing: ({repr(fixtname)})")
								if showgui: root.destroy()
								return "ERR NameForbidden"
							elif (fixt["addr"],fixt["universe"]) == (addr,universe) or (fixt["universe"] == universe and addr+(len(channels)-1) == fixt["addr"]) or (fixt["universe"] == universe and (fixt["addr"] <= addr and (fixt["addr"] + len(fixt["channels"]) > addr))):
								log("GUI/pyqt.guicmds."+cFN(),"error",f"Address of new fixture would overlap with other fixture")
								if showgui: NewPyDMX.tools.dialogs.error("Creating new fixture failed",f"New Fixture would overlap other fixture's address ({repr(fixtname)})")
								if showgui: root.destroy()
								return f"ERR AddrAlreadyInUse {fixtname}"
						log("GUI/pyqt.guicmds."+cFN(),"okay","Fixture configuration is vailid")
						
						log("GUI/pyqt.guicmds."+cFN(),"info","Storing new fixture")
						guivars.general.show["fixtures"][name] = {"universe":dc(universe),"addr":dc(addr),"channels":dc(channels)}
						log("GUI/pyqt.guicmds."+cFN(),"okay","New fixture added")
						NewPyDMX.tools.dialogs.info("Create new fixture",f"New fixture {name} created")
						if showgui: root.destroy()
						return "OK NewFixtureAdded"

			elif cmdtext.startswith("var"):
				try:
					args = cmdtext.split()
					op, name = args[1], args[2]
					typ = args[3] if len(args) > 3 else "str"
				except:
					op, name, typ = "", "", ""

				if op == "set":
					if typ == "str":
						val, ok = QInputDialog.getText(None,"Variable",f"Value for {name}")
					elif typ == "int":
						val, ok = QInputDialog.getInt(None,"Variable",f"Value for {name}")
					elif typ == "float":
						val, ok = QInputDialog.getDouble(None,"Variable",f"Value for {name}")
					else:
						return "ERR InvalidType"
					if ok:
						guivars.general.usrvars[name] = val
						return "OK VarSet"

				elif op == "get":
					log("GUI/pyqt.guicmds."+cFN(),"info",f"Reading variable '{name}'")
					try: val = guivars.general.usrvars[name]
					except KeyError:
						log("GUI/pyqt.guicmds."+cFN(),"error",f"Variable '{name}' not found")
						return "ERR VarNotFound"
					log("GUI/pyqt.guicmds."+cFN(),"debug",f"Value of variable '{name}' is {repr(val)}")
					return f"OK got_value {repr(val)}"
				
				elif op == "calc":
					operation = typ
					val = args[4]
					if operation not in ("+","-","*","/"):
						log("GUI/pyqt.guicmds."+cFN(),"error",f"Invailid var operation: {repr(operation)}")
						return "ERR InvailidOperation"
					log("GUI/pyqt.guicmds."+cFN(),"info",f"Executing operation {repr(operation)} on variable '{name}' with {repr(val)}")
					try:
						var = guivars.general.usrvars[name]
						if type(var) == int: val = int(val)
						elif type(var) == float: val = float(val)
						else:
							raise Exception(f"Variable has invailid type")
						guivars.general.usrvars[name] = eval(f"guivars.general.usrvars[name] {operation} {val}")
					except KeyError:
						log("GUI/pyqt.guicmds."+cFN(),"error",f"Variable '{name}' not found")
						return "ERR VarNotFound"
					except Exception as exc:
						log("GUI/pyqt.guicmds."+cFN(),"error",f"Operation on Variable '{name}' could not be finished ({exc})")
						return f"ERR {'_'.join(str(exc).split())}"
					log("GUI/pyqt.guicmds."+cFN(),"okay","Operation executed")
					return "OK OperationExecuted"
				
				return "ERR InvailidCommand"
		
		class main():
			class run():
				@staticmethod
				def macroInThread(CONFIG, loc: str, code: list[str], clr: str, resetOnEnd=True, repeatOnEnd=False):
					x, y = map(int, loc.split("x"))
					clrmap = {
						"red": "#400",
						"orange": "#630",
						"yellow": "#440",
						"green": "#040",
						"cyan": "#044",
						"blue": "#004",
						"purple": "#404",
						"white": "#444"
					}

					btn = guivars.elements.main.macros_btn_lst[y][x]
					btn.setStyleSheet(f"background-color: {clrmap[clr]}; border:2px solid {clr};color:white")
					QApplication.processEvents()

					restore = {}
					for line in code:
						if resetOnEnd:
							if "addr=" in line or "fixt=" in line:
								pos = [0]
								for elm in line.split():
									if "addr=" in elm: break
									elif "fixt=" in elm: break
									pos[0] = pos[0] + 1
								if "universe=" in line and not "fixt=" in line:
									pos.append(0)
									for elm in line.split():
										if "universe=" in elm: break
										pos[1] = pos[1] + 1
								restaddr = line.split()[pos[0]] if len(pos) == 1 else f"{line.split()[pos[0]]} {line.split()[pos[1]]}"
								if restaddr not in list(restore.keys()):
									try:
										resp = pyqt.guicmds.execcmd(CONFIG,f"channels getChannel {restaddr}",expectResponse=True)
										try: restore[restaddr] = int(resp.split("_")[3])
										except IndexError: pass
									except Exception as exc:
										log("GUI/pyqt.guicmds.main.run."+cFN(),"error",f"Failed to save channel state of {line.split()[pos[0]]} ({exc})")

						resp = pyqt.guicmds.execcmd(CONFIG, line, expectResponse=True)
						if resp.split()[0] == "ERR":
							NewPyDMX.tools.dialogs.error("Failed to run Macro",
														 f"Error at {loc}: {' '.join(resp.split()[1:])}")
							if loc in guivars.general.mthr_active:
								guivars.general.mthr_active.remove(loc)
						if loc not in guivars.general.mthr_active:
							if resetOnEnd:
								for key in restore:
									pyqt.guicmds.execcmd(CONFIG, f"channels setChannel {key} setto='{restore[key]}'", expectResponse=True)
							break

					while repeatOnEnd and loc in guivars.general.mthr_active:
						for line in code:
							resp = pyqt.guicmds.execcmd(CONFIG, line, expectResponse=True)
							if resp.split()[0] == "ERR":
								NewPyDMX.tools.dialogs.error("Failed to run Macro",
															 f"Error at {loc}: {' '.join(resp.split()[1:])}")
								if loc in guivars.general.mthr_active:
									guivars.general.mthr_active.remove(loc)
							if loc not in guivars.general.mthr_active:
								if resetOnEnd:
									for key in restore:
										pyqt.guicmds.execcmd(CONFIG, f"channels setChannel {key} setto='{restore[key]}'", expectResponse=True)
								break

					btn = guivars.elements.main.macros_btn_lst[y][x]
					btn.setStyleSheet(f"background-color: #161616; border:2px solid {clr};color:white")
					QApplication.processEvents()
					if loc in guivars.general.mthr_active:
						guivars.general.mthr_active.remove(loc)
				
				@staticmethod
				def macro(CONFIG, location: str):
					try:
						macro_data = guivars.general.show["macros"][location]
					except KeyError:
						log("GUI/pyqt.guicmds.main.run.macro", "error", f"Macro {location} not found")
						return

					if location in guivars.general.mthr_active:
						guivars.general.mthr_active.remove(location)
						log("GUI/pyqt.guicmds.main.run.macro", "warn", f"Macro {location} execution stopped")
						return

					guivars.general.mthr_active.append(location)
					thr = Thread(
						target=lambda: pyqt.guicmds.main.run.macroInThread(
							CONFIG, location, macro_data["code"], macro_data["color"],
							resetOnEnd=macro_data["resetOnEnd"], repeatOnEnd=macro_data["repeatOnEnd"]
						)
					)
					guivars.general.macrothr.append(thr)
					thr.start()
					log("GUI/pyqt.guicmds.main.run.macro", "info", f"Started macro at {location}")

	# ────────────────────────────────────────────────
	# MAIN WINDOW
	# ────────────────────────────────────────────────
	class main(QMainWindow):
		
		def set_title(self,title:str):
			log("GUI/pyqt.main."+cFN(),"info",f"Changing title of main window to {repr(title)}")
			guivars.windows.main.setWindowTitle(title)
			log("GUI/pyqt.main."+cFN(),"okay","Title of main window changed")

		def __init__(self, CONFIG, config):
			super().__init__()
			guivars.general.config = config
			guivars.windows.main = self
			self.setWindowTitle("PyDMX")
			self.setStyleSheet(f"background:{CONFIG.gui.style.main.background}")
			self.resize(
				CONFIG.gui.style.main.size.width,
				CONFIG.gui.style.main.size.height
			)

			central = QWidget()
			self.setCentralWidget(central)
			layout = QGridLayout()
			central.setLayout(layout)

			# ───────────── CMD FRAME ─────────────
			cmdframe = QFrame()
			cmdframe.setStyleSheet("background:#111;border:2px inset #333")
			cmdlayout = QGridLayout()
			cmdframe.setLayout(cmdlayout)
			cmd_style = f"""
QFrame {{
	background: {CONFIG.gui.style.main.frames.cmdexec.background};
}}

QTextEdit, QLineEdit {{
	background: {CONFIG.gui.style.main.frames.cmdexec.entrybg};
	color: {CONFIG.gui.style.main.frames.cmdexec.entryfg};
	selection-background-color: #555;
	selection-color: white;
}}

QPushButton {{
	color: {CONFIG.gui.style.main.frames.cmdexec.entryfg};
}}"""
			cmdframe.setStyleSheet(cmd_style)

			self.cmdhistory = QTextEdit()
			self.cmdhistory.setReadOnly(True)
			self.cmdhistory.setFixedHeight(170)
			self.cmdhistory.setStyleSheet(
				f"background:{CONFIG.gui.style.main.frames.cmdexec.entrybg};"
				f"color:{CONFIG.gui.style.main.frames.cmdexec.entryfg}"
			)

			self.cmdentry = QLineEdit()
			self.cmdentry.setPlaceholderText("Enter command")
			self.cmdentry.returnPressed.connect(
				lambda: self.exec_cmd(CONFIG)
			)

			btn = QPushButton("Execute Command")
			btn.clicked.connect(lambda: self.exec_cmd(CONFIG))

			cmdlayout.addWidget(self.cmdhistory,0,0,8,4)
			cmdlayout.addWidget(self.cmdentry,8,0,1,3)
			cmdlayout.addWidget(btn,8,3)

			layout.addWidget(cmdframe,0,0,3,1)

			guivars.elements.main.cmdhistory_txt = self.cmdhistory
			guivars.elements.main.cmd_ent = self.cmdentry

			# ───────────── MACROS GRID ─────────────
			macros = QFrame()
			macrolayout = QGridLayout()
			macros.setLayout(macrolayout)
			macrolayout.setSpacing(0)
			macrolayout.setContentsMargins(0,0,0,0)
			guivars.elements.main.macros_btn_lst = []

			for y in range(5):
				row=[]
				for x in range(15):
					loc=f"{x}x{y}"
					title = ""
					color = "#444"
					if loc in guivars.general.show["macros"]:
						title = guivars.general.show["macros"][loc]["name"]
						color = guivars.general.show["macros"][loc]["color"]

					#b = QPushButton(title)
					b = pyqt.RightClickButton(title,right_click=eval(f'lambda event:guivars.elements.main.cmd_ent.setText(guivars.elements.main.cmd_ent.text() + str(" " if guivars.elements.main.cmd_ent.text()[-1:] != " " else "") + "{x}x{y}")'))
					b.setFixedSize(84,65)
					b.setStyleSheet(
						f"background:#161616;border:2px solid {color};color:white"
					)
					if title:
						b.clicked.connect(
							lambda _,l=loc: pyqt.guicmds.main.run.macro(CONFIG,l)
						)
					macrolayout.addWidget(b,y,x)
					row.append(b)
				guivars.elements.main.macros_btn_lst.append(row)

			layout.addWidget(macros,3,0,5,1)
			
			# ───────────── CUELIST FRAME ─────────────
			"""
			UPDATE
			---------------
			guivars.elements.main.cl_desc_lst[3]["cue_current_lbl"].setText("Cue 12")
			guivars.elements.main.cl_desc_lst[3]["state"].setStyleSheet("background:#0f0;color:black")
			"""
			cuelist_frame = QFrame()
			cuelist_layout = QGridLayout()
			cuelist_layout.setSpacing(0)
			cuelist_layout.setContentsMargins(0,0,0,0)
			cuelist_frame.setLayout(cuelist_layout)
			
			guivars.frames.main.cuelistframe = cuelist_frame
			guivars.elements.main.cl_btn_lst = []
			guivars.elements.main.cl_desc_lst = []
			
			for i in range(15):
				# container button
				btn = QPushButton()
				btn.setFixedSize(84, 150)
				btn.setStyleSheet(
					f"""
					QPushButton {{
						background: {CONFIG.gui.style.general.buttonbg};
						border: {CONFIG.gui.style.general.buttonborderwidth}px solid
								{CONFIG.gui.style.general.buttonborder};
						color: {CONFIG.gui.style.general.buttontxt};
					}}
					"""
				)
			
				btn.clicked.connect(
					lambda _, idx=i: log("GUI/window", "okay", f"Click event detected on CL{idx}")
				)
			
				# internal layout (vertical)
				vbox = QVBoxLayout(btn)
				vbox.setContentsMargins(2, 2, 2, 2)
			
				title = QLabel(f"CL{i}")
				title.setAlignment(Qt.AlignCenter)
				title.setStyleSheet("color:white;font-size:13px")
			
				lastcue = QLabel("LastCue")
				lastcue.setAlignment(Qt.AlignCenter)
				lastcue.setStyleSheet("color:white;font-size:10px")
			
				curcue = QLabel("CurCue")
				curcue.setAlignment(Qt.AlignCenter)
				curcue.setStyleSheet("color:white;font-size:10px")
			
				followcue = QLabel("FollowCue")
				followcue.setAlignment(Qt.AlignCenter)
				followcue.setStyleSheet("color:white;font-size:10px")
			
				state = QLabel("Inactive")
				state.setAlignment(Qt.AlignCenter)
				state.setStyleSheet(
					"background:#f00;color:white;font-size:10px"
				)
			
				# add widgets
				vbox.addWidget(title)
				vbox.addWidget(lastcue)
				vbox.addWidget(curcue)
				vbox.addWidget(followcue)
				vbox.addWidget(state)
			
				# right-click support (menu click equivalent)
				btn.setContextMenuPolicy(Qt.CustomContextMenu)
				btn.customContextMenuRequested.connect(
					lambda _, idx=i: log("GUI/window", "okay", f"Menu click event detected on CL{idx}")
				)
			
				# store references (important!)
				guivars.elements.main.cl_btn_lst.append(btn)
				guivars.elements.main.cl_desc_lst.append({
					"title": title,
					"cue_last_lbl": lastcue,
					"cue_current_lbl": curcue,
					"cue_follow_lbl": followcue,
					"state": state
				})
			
				cuelist_layout.addWidget(btn, 0, i)
			
			# add cuelist frame to main grid
			layout.addWidget(cuelist_frame, 8, 0)
			
			#Align window to monitor
			pyqt.guicmds.move_window_to_screen(self,get_screen_index_for("windows.main"))
			self.showFullScreen()
			
			log("GUI/main.mainloop","info","Initializing mainloop of main window\n\nIN MAINLOOP/PROGRAM EVENTS\n"+"="*50+"\n\n\n\n\n")
			
		def exec_cmd(self, CONFIG):
			cmd = self.cmdentry.text()
			self.cmdentry.clear()
			self.cmdhistory.insertPlainText(f"> {cmd}\n")
			if not cmd:
				self.cmdhistory.insertPlainText("[ERR] No command text supplied\n")
				self.cmdhistory.moveCursor(QTextCursor.End)
				return
			resp = pyqt.guicmds.execcmd(CONFIG, cmd)
			if resp:
				self.cmdhistory.insertPlainText(f"[{resp.split()[0]}] {' '.join(resp.split()[1:])}\n")
				self.cmdhistory.moveCursor(QTextCursor.End)
