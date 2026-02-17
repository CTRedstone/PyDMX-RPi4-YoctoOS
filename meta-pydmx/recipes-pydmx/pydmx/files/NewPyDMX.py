import gui
import socket
import requests
from log import *
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from tkinter import messagebox as tkMB
from copy import deepcopy as dc
import jsonToClass as jTC
from pytools.variables import cFN
import pytools.ctktools as tktools
from json import load as jsload, dump as jsdump
from threading import Thread, Event as threadEvent
from olaTerminal import PyDMX
from dmxServer import dmxServer, reloadHelpFile as dmxServerRHF
from dmxClient import dmxClient
from PyQt5.QtWidgets import QApplication

class errs():
	class StopError(Exception): ...
	class FileError(Exception): ...
	class DataError(Exception): ...
	class SystemError(Exception): ...

class vars():
	dmxComm = None
	dmxServ = None
	pixelDisp = None
	threadStop = threadEvent()
	config = None
	
	class screensize():
		size = {}
		width = None
		height = None
	
	class templates():
		showtemplate = {
			"name": "New Show",
			"config": {
				"screens": {
					"windows.main": 1,
					"windows.programmer": 0,
					"windows.settings": None,
					"windows.fixturepool": None,
					"windows.macropool": None,
					"windows.macros.coding": 0,
					"windows.editmacro": None
				}
			},
			"keybinds": {},
			"fixtures": {},
			"macros": {},
			"cuelists": {}
		}

class CONFIG(): ...

class tools():
	class dialogs():
		def error(title,message,monitor=None):
			root = tk.Tk()
			tktools.placeWinOnMonitor(root,fullscreen=False,monitor=monitor,center=True)
			root.withdraw()
			tkMB.showerror(title,message,parent=root)
			root.destroy()
		
		def info(title,message,monitor=None):
			root = tk.Tk()
			tktools.placeWinOnMonitor(root,fullscreen=False,monitor=monitor,center=True)
			root.withdraw()
			tkMB.showinfo(title,message,parent=root)
			root.destroy()
		
		def warning(title,message,monitor=None):
			root = tk.Tk()
			tktools.placeWinOnMonitor(root,fullscreen=False,monitor=monitor,center=True)
			root.withdraw()
			tkMB.showwarning(title,message,parent=root)
			root.destroy()
		
		def yesno(title,message,monitor=None):
			root = tk.Tk()
			tktools.placeWinOnMonitor(root,fullscreen=False,monitor=monitor,center=True)
			root.withdraw()
			_return = tkMB.askyesno(title,message,parent=root)
			root.destroy()
			return _return
		
		def okcancel(title,message,monitor=None):
			root = tk.Tk()
			tktools.placeWinOnMonitor(root,fullscreen=False,monitor=monitor,center=True)
			root.withdraw()
			_return = tkMB.askokcancel(title,message,parent=root)
			root.destroy()
			return _return
		
		def retrycancel(title,message,monitor=None):
			root = tk.Tk()
			tktools.placeWinOnMonitor(root,fullscreen=False,monitor=monitor,center=True)
			root.withdraw()
			_return = tkMB.askretrycancel(title,message,parent=root)
			root.destroy()
			return _return
	
	class gui():
		def getScreenSize(): #Gets the screensize
			log(cFN(),"info","Loading screensize...")
			try:
				log(cFN(),"debug","Creating example window to load windowsize with")
				test = ctk.CTk()
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
	#Initialize log file
	#write_log_to_file(True)
	set_program_name("PyDMX")
	#init_logfile(title="Logfile of PyDMX")
	
	#Test if file is run as main
	if __name__ == "__main__": log(cFN(),"warn","PyDMX is executed as main process")
	
	#Informational window for user
	gui._tkinter.loadwin.init()
	
	#Waitwindow if netreq takes longer
	gui._tkinter.loadwin.setstep(desc="Authenticating")
	
	try:
		req = True
		try: requests.get("https://ctredstone.pythonanywhere.com")
		except:
			try: requests.get("https://ctredstone.com")
			except: req = False
		if req:
			try:
				try: result = requests.get("https://ctredstone.pythonanywhere.com/api/ce/WD6aT9ZLAYzF9tfo").json()
				except: result = requests.get("https://ctredstone.com/api/ce/WD6aT9ZLAYzF9tfo").json()
				if result["value"] != True: raise errs.SystemError()
			except:
				log(cFN(),"fatal","Some error occured")
				gui._tkinter.loadwin.setstep(desc="Something went wrong",step="Error")
				gui._tkinter.loadwin.destroy()
				return
	except KeyboardInterrupt:
		log(cFN(),"fatal","KeyboardInterrupt detected, exiting PyDMX")
		return
	
	#Initialize config class
	log(cFN(),"info","Loading configuration from file...")
	gui._tkinter.loadwin.setstep(desc="Loading config")
	try:
		with open("config.new.json","r") as fle: vars.config = jsload(fle)
	except Exception as exc:
		log(cFN(),"fatal",f"Failed to load config file ({exc})")
		tools.dialogs.error("Error","Failed to open config file")
		raise errs.FileError(f"Failed to load config file ({exc})")
	log(cFN(),"okay",f"Configuration file loaded ({len(vars.config)})")
	
	log(cFN(),"info","Checking if other server than 127.0.0.1 (loopback) is used")
	if vars.config["preferences"]["dmxcontrol"]["ip"] != "127.0.0.1":
		log(cFN(),"debug",f"Address {vars.config['preferences']['dmxcontrol']['ip']} defined for server, setting 'isserver' option to False")
		vars.config["preferences"]["dmxcontrol"]["isserver"] = False
		log(cFN(),"okay","'isserver' set to False since loopback isn't configured for dmxserver")
	else:
		log(cFN(),"okay","Nothing changed (loopback is configured as dmxserver address")
	
	log(cFN(),"info","Converting config dictonary into class")
	try: jTC.convert(CONFIG,vars.config)
	except Exception as exc:
		log(cFN(),"fatal",f"Failed to convert config into dictonary ({exc})")
		tools.dialogs.error("Error","Failed to load config")
		raise errs.DataError(f"Failed to convert config into dictonary ({exc})")
	log(cFN(),"okay","Config converted to dictonary")
	
	#Load screen size
	log(cFN(),"info","Loading screen size")
	vars.screensize.size = tools.gui.getScreenSize()
	vars.screensize.width,vars.screensize.height = vars.screensize.size["width"],vars.screensize.size["height"]
	log(cFN(),"okay",f"Screen size loaded ({vars.screensize.size})")
	
	#Start OLA
	if CONFIG.preferences.dmxcontrol.enableOLA == True and CONFIG.preferences.dmxcontrol.isserver:
		log(cFN(),"info","Starting PyDMX OLA")
		gui._tkinter.loadwin.setstep(desc="Starting OLA")
		vars.pydmx = PyDMX(universes=CONFIG.preferences.dmxcontrol.universes.listitems,debug=CONFIG.preferences.debug,mainApp="PyDMX",showprcwin=False)
		log(cFN(),"okay","OLA Started")
	else: log(cFN(),"warn","OLA wasn't started due to settings")
	
	#Start DMX Server
	if CONFIG.preferences.dmxcontrol.isserver:
		gui._tkinter.loadwin.setstep(desc="Starting DMX Server")
		log(cFN(),"info","Starting main DMX server in new thread...")
		vars.dmxServ = dmxServer(vars.pydmx,ip=CONFIG.preferences.dmxcontrol.ip,port=CONFIG.preferences.dmxcontrol.port)
		vars.dmxServThread = Thread(target=vars.dmxServ.startServer)
		vars.dmxServThread.deamon = True
		vars.dmxServThread.start()
		log(cFN(),"okay","DMX Server started")
		log(cFN(),"info","Reloading command list of DMX Server...")
		dmxServerRHF()
		log(cFN(),"okay","DMX Server command list reloaded")
	else: log(cFN(),"warn","DMX Server wasn't started due to settings")
	
	#Initialize client
	if CONFIG.preferences.dmxcontrol.isclient:
		log(cFN(),"info","Starting client communication with dmx server")
		gui._tkinter.loadwin.setstep(desc="Starting DMX client")
		vars.dmxComm = dmxClient(master="PyDMX",ip=CONFIG.preferences.dmxcontrol.ip,port=CONFIG.preferences.dmxcontrol.port)
		log(cFN(),"okay","DMX Client started")
		log(cFN(),"info","Connecting client to DMX Server")
		try:
			vars.dmxComm.connect()
			log(cFN(),"okay","Connected DMX Client to DMX Server")
		except Exception as exc:
			log(cFN(),"error","Failed to connect DMX Client to DMX Server ({exc})")
		gui.set_dmx_client(vars.dmxComm)
	else: log(cFN(),"warn","DMX Client wasn't started due to settings")
	
	#Load show
	if CONFIG.preferences.dmxcontrol.isclient:
		log(cFN(),"info","Trying to load showfile")
		gui._tkinter.loadwin.setstep(desc="Loading show")
		try:
			with open(CONFIG.preferences.general.currentshow,"r") as fle: vars.show = jsload(fle)
		except FileNotFoundError as exc:
			with open(CONFIG.preferences.general.currentshow,"w+") as fle: jsdump(vars.templates.showtemplate,fle)
			with open(CONFIG.preferences.general.currentshow,"r") as fle: vars.show = jsload(fle)
		except Exception as exc:
			log(cFN(),"warn",f"Couldn't open showfile ({exc})")
			vars.show = dc(vars.templates.showtemplate)
		log(cFN(),"okay",f"Showfile loaded ({len(vars.show)})")
		gui.set_show(vars.show)
	
	#Initialize main window of GUI
	if CONFIG.preferences.dmxcontrol.isclient: log(cFN(),"debug",f"Selected framework for GUI is: {CONFIG.gui.framework}")
	if CONFIG.preferences.dmxcontrol.isclient and CONFIG.gui.framework == "tk":
		gui.set_screen_size(vars.screensize.size)
		gui.set_config(vars.config)
		gui._tkinter.loadwin.setstep(desc="Building GUI")
		gui._tkinter.main.build_gui(CONFIG)
		gui.guivars.windows.screen2.mainclass = gui._tkinter.screen2(CONFIG)
		gui._tkinter.main.keybind_config()
	else: log(cFN(),"warn","GUI wasn't started because 'isclient' is False or framework 'qt' is set")
	
	#Start DMX render loop
	if CONFIG.preferences.dmxcontrol.isclient:
		log(cFN(),"info","Starting DMX render loop")
		gui._tkinter.loadwin.setstep(desc="Start DMX render")
		vars.dmxComm.sendCommand("render startLoop",expectResponse=True)
		log(cFN(),"okay","DMX render loop started")
	
	#Start window mainloop
	gui._tkinter.loadwin.setstep(desc="",step="Loaded")
	gui._tkinter.loadwin.destroy()
	if CONFIG.preferences.dmxcontrol.isclient:
		if CONFIG.gui.framework == "tk":
			try:
				gui._tkinter.main.set_title(f"PyDMX ({CONFIG.preferences.general.currentshow})")
				gui.guivars.windows.screen2.mainclass.showinitialwin()
				gui._tkinter.main.mainloop(CONFIG)
			except Exception as exc:
				log(cFN(),"fatal",f"Execution of PyDMX got interrupted due to exception ({exc})")
		elif CONFIG.gui.framework == "qt":
			try:
				app = QApplication([])
				win = gui.pyqt.main(CONFIG,vars.config)
				win.set_title(f"PyDMX ({CONFIG.preferences.general.currentshow})")
				win.show()
				app.exec_()
			except Exception as exc:
				log(cFN(),"fatal",f"Execution of PyDMX got interrupted due to exception ({exc})")
	else:
		win = CTk()
		win.title("PyDMX")
		btn = ctk.CTkButton(win,text="Stop PyDMX",command=lambda:1/0)
		btn.pack()
		win.mainloop()
	
	log(cFN(),"okay","Done")

if __name__ == "__main__":
	start()