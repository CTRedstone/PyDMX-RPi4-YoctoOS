from json import load as jsload
from tkinter import *
from customtkinter import *
from pytools.progressbar import progressbar as pgb
from copy import deepcopy
from subprocess import run as shrun

def getMonitors(_return="dict") -> dict:
	"""
	@param _return can either be "dict" or "list"
	"""
	ret = shrun(["xrandr"],capture_output=True,text=True)
	retlines = ret.stdout.splitlines()
	
	monitors = [] if _return == "list" else {}
	for line in retlines:
		if " connected" in line:
			for word in line.split():
				if "x" in word and "+" in word:
					res, pos = word.split("+",1)
					w,h = map(int,res.split("x"))
					x,y = map(int,pos.split("+"))
					if _return == "list": monitors.append({"name":line.split()[0],"width":w,"height":h,"xpos":x,"ypos":y,"primary":True if " primary" in line else False})
					else: monitors[line.split()[0]] = {"width":w,"height":h,"xpos":x,"ypos":y,"primary":True if " primary" in line else False}
	
	return monitors

def primaryMonitorName() -> str:
	mtrs = getMonitors(_return="list")
	for elm in mtrs:
		if elm["primary"]: return elm["name"]

def getSecondaryMonitors(_return="list",firstIfNoOther=True):
	"""
	@param _return can either be "dict" or "list"
	"""
	mtrs = getMonitors(_return=_return)
	if _return == "dict":
		ind = ""
		for key in list(mtrs.keys()):
			if mtrs[key]["primary"]:
				ind = key
				break
	else:
		ind = 0
		for i in range(len(mtrs)):
			if mtrs[i]["primary"]:
				ind = i
				break
	
	if firstIfNoOther and len(mtrs) == 1: pass
	else: del mtrs[ind]
	return mtrs

def placeWinOnMonitor(win,monitors=None,monitor=None,fullscreen=True,center=False,width=0,height=0):
	if monitors == None and type(monitor) == str: monitors = getMonitors()
	try:
		if type(monitors) == dict and type(monitor) == str:
			xpos_center = 0
			ypos_center = 0
			if center:
				xpos_center = monitors[monitor]["xpos"] + (int(monitors[monitor]["width"]/2)-int(width/2))
				ypos_center = monitors[monitor]["ypos"] + (int(monitors[monitor]["height"]/2)-int(height/2))
			win.geometry(f"{monitors[monitor]['width'] if not center else width}x{monitors[monitor]['height'] if not center else height}+{monitors[monitor]['xpos'] if not center else xpos_center}+{monitors[monitor]['ypos'] if not center else ypos_center}")
		if fullscreen: win.attributes("-fullscreen",True)
	except KeyError:
		if type(monitors) == dict and type(monitor) == str:
			xpos_center = 0
			ypos_center = 0
			if center:
				xpos_center = monitors[primaryMonitorName()]["xpos"] + (int(monitors[primaryMonitorName()]["width"]/2)-int(width/2))
				ypos_center = monitors[primaryMonitorName()]["ypos"] + (int(monitors[primaryMonitorName()]["height"]/2)-int(height/2))
			win.geometry(f"{monitors[primaryMonitorName()]['width'] if not center else width}x{monitors[primaryMonitorName()]['height'] if not center else height}+{monitors[primaryMonitorName()]['xpos'] if not center else xpos_center}+{monitors[primaryMonitorName()]['ypos'] if not center else ypos_center}")
		if fullscreen: win.attributes("-fullscreen",True)

def lstfileToDict(file:str,assign:bool,mainloop:bool,**args):
	"""Use Argument 'append' to add lists with elements, Argument 'execs' to add a class with functions for the command parameters in json file (can get used in the json file as a normal text parameter in args - use argument "nolog" to disable logging output"""
	_flelst = []
	try: func = args["execs"]
	except: pass
	try: _return = args["append"]
	except: _return = {}
	try: disablelog = args["nolog"]
	except KeyError: disablelog = False
	with open(file,"r") as fle: _flelst = jsload(fle)
	log = pgb(msteps=len(_flelst),left=".",done="#",msg="Converting...",disable=disablelog)
	lineint = 0
	for i in range (len(_flelst)):
		item = deepcopy(_flelst[i])
		log.step(f"Processing item {lineint} of file with data {item}...",0)
		try:
			if item["command"]:
				log.step(f"trying to create command for string: '{item['command']}'",0)
				log.step(f"The command argument in Dictonary from file has the following type: {type(item['command'])}",0)
				try:
					try: _cmdargs = item["cmdargs"]
					except KeyError: _cmdargs = {}
					#item["args"]["command"] = lambda: eval(str(item["args"]["command"]))
					#item["args"]["command"] = func[item["command"]](**_cmdargs)
					#item["class"].bind("<Button-1>",lambda: func[item["command"]](**_cmdargs))
					eval("item['args']['command'] = lambda: func['" + item["command"] + "'](**_cmdargs)")
					print(item["command"],"                        \n")
					log.step(f"Bound python function ('{item['command']}') to item '{item['id']}'",0)
				except Exception as exc: log.step(f"Could not evaluate function from item.args.command because of the following exception: \"{exc}\"",0)
			else: pass
		except: pass
		try: _return[item["id"]] = eval(item["class"])(_return[item["master"]],**item["args"])
		except KeyError: _return[item["id"]] = eval(item["class"])()
		log.step(f"Item with id '{item['id']}' signed in _return...",0)
		try: _return[item["id"]+".grid"] = item["grid"]
		except KeyError:
			try:_return[item["id"]+".pack"] = item["pack"]
			except KeyError: pass
		if assign == True:
			try:
				_return[item["id"]].grid(**item["grid"])
				log.step(f"Bound item with id '{item['id']}' sucessfully to grid",1)
			except:
				try:
					_return[item["id"]].pack(**item["pack"])
					log.step(f"Bound item with id '{item['id']}' sucessfully with pack",1)
				except: log.step(f"Skipped binding item with id '{item['id']}' due to missing parameters in file",1)
		else: log.step(f"Configured widget with id '{item['id']}' without binding it to master",1)
		try:
			_return[item["id"]+".group"] = item["group"]
			log.step(f"Added group {item['group']} to return",0)
		except KeyError: pass
		if item["id"] in ["win","root"]:
			try:
				_return[item["id"]].title(item["title"])
				log.step(f"Set title of window (widget with name '{item['id']}') to '{item['title']}'",0)
			except KeyError as exc: log.step(f"Failed to set title because of the following KeyError: {exc}",0)
			try:
				_return[item["id"]].geometry(item["geometry"])
				log.step(f"Set geometry of window (widget with name '{item['id']}') to {item['geometry']}",0)
			except KeyError as exc: log.step(f"Failed to set geometry because of the following KeyError: {exc}",0)
		lineint += 1
	log.step(f"Ended up with {lineint} configurd items, returning resulting dictonary",0)
	if mainloop == True:
		try:
			_return["win"] = _return["win"]
			log.step("Starting mainloop of widget with id 'win'",0)
			log.finish()
			_return["win"].mainloop()
		except KeyError:
			try:
				_return["root"] = _return["root"]
				log.step("Starting mainloop of widget with id 'root'",0)
				log.finish()
				_return["root"].mainloop()
			except KeyError:
				log.step("Failed to start mainloop because there is no item called 'win' or 'root'",0)
				log.finish()
	else: log.finish()
	return _return

def wdgdict_mainloop(winid:str,wdgdict:dict):
	wdgdict[winid].mainloop()
