from json import load as jsload
from tkinter import *
from customtkinter import *
from pytools.progressbar import progressbar as pgb
from copy import deepcopy

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
