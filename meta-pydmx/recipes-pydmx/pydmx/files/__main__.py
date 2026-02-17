print("==============================================================================")

debug = False

try: #Import module largefont for NewPyDMX log heading in terminal, not needed
	from largefont import pixelFontGen as pFG
	pF = pFG(fontFile="largeFont.json")
	pF.newLine("   PYDMX")
	pF.generate("\033[36m")
	pF._return("terminal")
except: pass

try:
	#Import pytools and tkinter for log and updater
	from pytools.variables import FE, cFN
	from pytools.configTools import load as loadcnf
	from pytools.logger import clearLogFile,logfile
	from pytools import exceptions
	from tkinter import *
	import log as lm

	def log(tpe:str,msg:str,errtpe="normal"):
		"""
		Prints a colored logline in the terminal, formatted like
		"[PyDMX/init] [<tpe>] <msg>"
		if errtpe is set to "normal", loglines with type "err" or "error" will be colored yellow. Otherwise they will be colored red.
		"""
		global debug
		color = FE["cyan"] if tpe in ("info","inf") else FE["blue"] if tpe == "debug" else FE["green"] if tpe in ("okay","ok","done") else FE["yellow"] if tpe == "warn" or (tpe in ("err","error") and errtpe == "normal") else FE["red"] if tpe in ("fatal","err","error") else ''
		if debug or tpe != "debug":
			print(color+f"[NewPyDMX/init] [{tpe.upper()}] {msg}"+FE["reset"])
			#logfile(f"NewPyDMX/init",f"[{tpe.upper()}] {msg}")
	
	log("info","Initializing logfile")
	lm.set_program_name("PyDMX/__main__")
	lm.write_log_to_file(True)
	lm.init_logfile(title="Logfile of PyDMX")
	log("okay","Logfile initialized")
	lm.log("base-initializer","okay","Logfile initialized")

	import_errors = []

	#clearLogFile() #Clears the log file

	def impErr(imp:str,err):
		global import_errors
		import_errors.append(("import",imp,err))
		lm.log("base-initializer","err",f"Could not import '{imp}' due to the following exception: {err}")

	def impFromErr(_from:str,imp:str,err):
		global import_errors
		import_errors.append(("from/import",(_from,imp),err))
		lm.log("base-initializer","err",f"Could not import '{imp}' from '{_from}' due to the following exception: {err}")

	def impFromAsErr(_from:str,imp:str,_as:str,err):
		global import_errors
		import_errors.append(("from/import/as",(_from,imp,_as),err))
		lm.log("base-initializer","err",f"Could not import '{imp}' from '{_from}' as '{_as}' due to the following exception: {err}")

	lm.log("base-initializer","info","Starting NewPyDMX...")

	#debug = loadcnf("config.json")["general"]["debug"] #Checks if debug messages should be shown
	cnf = loadcnf("config.new.json") #Loads config file
	#print(debug)
	#lm.log("base-initializer","info",f"Debugmode is {'enabled' if debug == True else 'disabled'}")

	try:
		lm.log("base-initializer","debug","Importing 'exit' from sys...")
		from sys import exit
		lm.log("base-initializer","debug","Imported")
	except Exception as exc:
		impFromErr("sys","exit",exc)

	if __name__ != "__main__": #Checks if this file is the main process - if not, NewPyDMX won't start
		lm.log("base-initializer","fatal","Can not run NewPyDMX (main file) as module - exiting")
		exit()
	
	lm.log("base-initializer","info","Checking for needed Modules...")
	with open("imports.txt","r") as fle: #Load list of needed modules from file
		imports = fle.readlines()
	
	for imp in imports:
		_imp = imp.strip()
		try: #try to import every module from file. If there are ImportErrors, these will be saved, but the list will be finished before the program stops
			lm.log("base-initializer","debug",f"Importing '{_imp}'...")
			exec(f"import {_imp}")
			lm.log("base-initializer","debug",f"Imported '{_imp}'")
		except Exception as exc:
			impErr(_imp,exc)

	lm.log("base-initializer","debug","Ran through imports")

	_imp = "NewPyDMX" #Tries to import Mainprogram NewPyDMX.py If there is an error, this would be really bad
	try:
		lm.log("base-initializer","debug",f"Importing '{_imp}'...")
		import NewPyDMX
		lm.log("base-initializer","debug",f"Imported '{_imp}'")
	except Exception as exc:
		impErr(_imp,exc)

	updated = False

	if import_errors == []: #Only if there are no import errors, the updater will be imported and then started
		_imp = "updater"
		try:
			lm.log("base-initializer","debug",f"Importing '{_imp}'...")
			import updater
			lm.log("base-initializer","debug",f"Imported '{_imp}'")
		except Exception as exc:
			impErr(_imp,exc)

		updated = updater.updater(cnf["system"]["version"])

	if import_errors == [] and updated == False: #NewPyDMX will only be started when no update occured (Files need to be reloaded) and no import errors occured
		lm.log("base-initializer","ok","Dependencies are all reachable.")
		lm.log("base-initializer","info","Prepearing start of application...")
		try:
			from NewPyDMX import start as PyDMXstartTest #Only a test. If the start method of NewPyDMX is not reachable, NewPyDMX won't start
		except Exception as exc:
			lm.log("base-initializer","fatal",f"Starting NewPyDMX failed because start method of NewPyDMX is not reachable. Skipping program and exiting...")
			exit()
		lm.log("base-initializer","ok","Start method of NewPyDMX reachable, trying to launch program through NewPyDMX.start()")
		try:
			NewPyDMX.start() #Starts NewPyDMX
		except exceptions.criticalException as exc:
			lm.log("base-initializer","fatal",f"Execution of NewPyDMX raised criticalException: \"{exc}\" - Exiting...")
			try: NewPyDMX.vars.dmxComm.close()
			except: pass
			try: NewPyDMX.vars.dmxServ.stopServer()
			except: pass
			try: NewPyDMX.vars.threadStop.set()
			except: pass
			NewPyDMX.vars.load = False
			exit()
		except exceptions.ExitRequest as exc:
			lm.log("base-initializer","done",f"Recieved ExitRequest Exception from maincode: \"{exc}\" - Exiting...")
			try: NewPyDMX.vars.dmxComm.close()
			except: pass
			try: NewPyDMX.vars.dmxServ.stopServer()
			except: pass
			try: NewPyDMX.vars.threadStop.set()
			except: pass
			NewPyDMX.vars.load = False
			exit()
		except Exception as exc:
			lm.log("base-initializer","fatal",f"Executing NewPyDMX failed due to the following exception: \"{exc}\" - Exiting...")
			try: NewPyDMX.vars.pixelDisp.quit()
			except: pass
			try: NewPyDMX.vars.dmxComm.close()
			except: pass
			try: NewPyDMX.vars.dmxServ.stopServer()
			except: pass
			try: NewPyDMX.vars.threadStop.set()
			except: pass
			NewPyDMX.vars.load = False
			exit()
		lm.log("base-initializer","ok","Successfully finished execution of NewPyDMX")
	elif updated == True:
		lm.log("base-initializer","warn",f"Quitting start of NewPyDMX because code got updated. User has to restart NewPyDMX manually")
	else:
		lm.log("base-initializer","fatal","Could not start NewPyDMX because import_errors is not empty")
		for elm in import_errors:
			if elm[0] == "import":
				lm.log("base-initializer","err",f"Could not import '{elm[1]}': {elm[2]}")
			elif elm[0] == "from/import":
				lm.log("base-initializer","err",f"Could not import '{elm[1][1]}' from '{elm[1][0]}': {elm[2]}")
			elif elm[0] == "from/import/as":
				lm.log("base-initializer","err",f"Could not import '{elm[1][1]}' from '{elm[1][0]}' as '{elm[1][2]}': {elm[2]}")
			else:
				lm.log("base-initializer","err",f"Failed to import in unknown type - Error data: {elm}")
except Exception as exc:
	print(f"\033[31m\033[1mMasterException occured while trying to prepeare for NewPyDMX launch: {exc}\nExiting...\033[0m")
finally:
	try: NewPyDMX.vars.pixelDisp.quit()
	except: pass
	print("==============================================================================")
	time.sleep(120)
	try:
		exit()
		exit()
		exit()
	except: pass
