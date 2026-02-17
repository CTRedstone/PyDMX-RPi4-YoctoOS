#TODO: Add possibility to re-assign widgets

import subprocess
from customtkinter import *
import qtCompCTk as qctk
from pytools.variables import FE as fe
from copy import deepcopy
from json import load as jsload
from pytools.progressbar import progressbar
import prgbarWin as pbw

debug = False

class utils():
	def whereIs(lst:list,key,match): #Searches a dictonary in a list, with a key property set to match
		global debug
		for elm in lst:
			try:
				if elm[key] == match: return elm
			except KeyError: pass
		#if debug: print(f"With key '{key}' should match '{match}' in data {lst} it is not able to find some data.")
		return None

"""
Usage of jsonWin:
extend another class with that class ("class yourClassName(jsonWin.jsonWin): ...")
To use commands in your window, define some command-functions in your extended class (recommendent in something
like a "commands" class) - Specify these then in your config.json file in the options section under the command
parameter with out brackets as string: "options":{"command":"eval('self.commands.yourFunction')"} IMPORTANT:
the eval function is important to get things really work
"""

class jsonWin:
	environment = None

	class exceptions():
		class invailidConfigException(Exception): ...

	def center_window(self,window): #Centers the window on the screen
		if self.environment == "ctk":
			try:
				window.update_idletasks()
				width = window.winfo_width()
				height = window.winfo_height()
				screen_width = window.winfo_screenwidth() + 10
				screen_height = window.winfo_screenheight() + 10
				x = int((screen_width / 2) - (width / 2))
				y = int((screen_height / 2) - (height / 2))
				window.geometry(f"{width}x{height}+{x}+{y}")
			except: pass

	def __init__(self,mode="default",**kwargs):
		"""
		@param mode can be ctk or qt, for different look of UI - Default (at invailid modes too: ctk)
		"""
		global debug
		self.filecnt = []
		self.elements = []
		try:
			self.copyElements = kwargs["stack"]
			if debug: print(f"Stackable items possible - arguments: {self.copyElements}")
		except KeyError: self.copyElements = False

		self.environment = mode if mode in ("ctk","qt") else "ctk"
		if self.environment == "qt": self.qtapp = qctk.QApplication([])

	def loadFile(self,filepath:str): #Loads a file with widget configs
		with open(filepath, "r") as fle: self.filecnt = jsload(fle)

	def addFile(self,filepath:str): #Adds a file with widget configs to the existing list
		global debug
		with open(filepath, "r") as fle:
			flecnt = jsload(fle)
		for elm in flecnt: self.filecnt.append(elm)

	def addElement(self,element): #Adds a new Elementclass
		self.elements.append(element)

	def addElementDataList(self,_list:list): #Adds a new Element Datalist
		self.elements.extend(_list)

	def getElementDataList(self): #Returns the widget config
		return self.elements

	def loadElmDict(self,_dict:dict): #Loads a widget config directly from a dictonary
		self.filecnt = _dict

	def verifyElements(self): #Verifies and assigns the widgets
		global debug

		#load progressbar values
		msteps = 0
		split = 6
		for elm in self.filecnt:
			try:
				if elm["copy"]: pass
				try:
					msteps += self.copyElements[elm["copy"]["copyName"]]["times"]
				except KeyError: raise self.exceptions.invailidConfigException(f"No values for stackable items (at item with copyName '{elm['copy']['copyName']}') found, but found item to stack")
			except KeyError: msteps += 1
		pgb = progressbar(msteps=int(msteps/split)+1,left=fe["darker"]+">"+fe["reset"],done=fe["yellow"]+">"+fe["reset"],msg=f"Processing Widget (split{split})...")

		pbw.clrtheme("black-orange.json")
		pgbw = pbw.initwin()
		pgbw = pbw.setinf(pgbw,inftxt="[PyDMX] Loading Widgets")
		pgbw = pbw.setprg(pgbw,progress=0)

		#verify elements
		rcnt = 0
		cnt = split
		for elm in self.filecnt:
			rcnt += 1
			try:
				if elm["copy"]: pass
				cpelm = True #Value to check that the Widget needs to be stacked multiple times
			except KeyError: cpelm = False
			if cpelm == True:
				try:
					cptimes = self.copyElements[elm["copy"]["copyName"]]["times"] #Stores the amount of how often the widget should be stacked
				except KeyError: raise self.exceptions.invailidConfigException(f"No values for stackable items (at item with copyName '{elm['copy']['copyName']}') found, but found item to stack")
			else: cptimes = 1
			if cpelm: cpargs = self.copyElements[elm["copy"]["copyName"]]
			cprowbfr = 0
			for i in range(cptimes):
				if cnt%split == 0: pgb.step("",1)
				pgbw = pbw.setprg(pgbw,prgfloat=rcnt/len(self.filecnt)) ############################################################
				cnt += 1
				if debug: print("Processing "+str(i)+" variant of widget with name '"+elm["name"]+f"{'/'+str(i) if cpelm else ''}'")
				try: stmaster = elm["master"] #Reads the master of the widget
				except KeyError: stmaster = None
				_elm = {}
				#Stores every needed Value in a new elm dict to not change the original data
				_elm["id"],_elm["type"],_elm["args"],_elm["group"],_elm["master"] = elm["name"]+f'/{i}' if cpelm else elm["name"],elm["type"],elm["options"],elm["group"],str(stmaster)
				_elm["assigned"] = False

				if cpelm and elm["copy"]["stackCmd"] == True: #The stackcmd command would also increment a positional argument for the function, which gets configured here
					elm["cmdargs"] = [i]

				try:
					_elm["grid"] = deepcopy(elm["grid"])
					if cpelm:
						_elm["grid"]["column"] = _elm["grid"]["column"] + i - (cpargs["maxColumnCopy"]*cprowbfr) #Configures grid data for stack elements
						_elm["grid"]["row"] += cprowbfr
						if debug: print(f"> cpelm enabled for widget with name {elm['name']} at cptimes {i} - grid content of element: {_elm['grid']}")
						if i%cpargs["maxColumnCopy"] == 0 and _elm["grid"]["column"] == cpargs["maxColumnCopy"]:
							if debug: print(f"> cpelm enabled and maxColumnCopy reached for widget with name {elm['name']} at cptimess {i} - changing column and row: [R: {elm['grid']['row'] + cprowbfr + 1} C: {elm['grid']['column']}]")
							_elm["grid"]["column"] = deepcopy(elm["grid"]["column"])
							cprowbfr += 1
							_elm["grid"]["row"] += cprowbfr
				except KeyError:
					try: _elm["pack"] = elm["pack"]
					except KeyError:
						if elm["type"] not in ("CTk","CTkToplevel"): raise self.exceptions.invailidConfigException("No assign-parameter found")

				if elm["type"] not in ("CTk","CTkToplevel"): #Checks if the element type is not in CTk or CTkTopLevel, because otherwise these classes would also be treated as normal widgets with arguments, etc.
					try: cmdargs = elm["cmdargs"]
					except KeyError: cmdargs = None if self.environment == "ctk" else ()
					try: cmdkwargs = elm["cmdkwargs"] if self.environment == "ctk" else {}
					except KeyError: cmdkwargs = None

					if self.environment == "ctk":
						try: #Creates the real widget from every argument
							if debug == True: print("Trying to execute cmd for widget class:",elm["type"]+f'(utils.whereIs(self.elements,"id",elm["master"])["class"],**elm["options"],command=eval("{elm["command"]}"){",cmdargs="+str(cmdargs) if cmdargs != None else ""}{",cmdkwargs="+str(cmdkwargs) if cmdkwargs != None else ""})')
							_elm["class"] = eval(elm["type"]+f'(utils.whereIs(self.elements,"id",elm["master"])["class"],**elm["options"],command=eval("{elm["command"]}"){",cmdargs=cmdargs" if cmdargs != None else ""}{",cmdkwargs=cmdkwargs" if cmdkwargs != None else ""})')
							try: #Tries to bind a command to the widget
								_elm["class"].bind(elm["bind"]["trigger"],eval(elm["bind"]["command"]))
							except KeyError: pass
							except Exception as exc:
								print(f"Failed to bind command '{elm['bind']['command']}' with trigger '{elm['bind']['trigger']}' to element with name '{elm['name']}'")
						except KeyError: _elm["class"] = eval(elm["type"]+f"(utils.whereIs(self.elements,'id',elm['master'])['class'],**elm['options'])")
					else:
						try: #Creates the real widget from every argument
							if debug == True: print("Trying to execute cmd for widget class:",elm["type"]+f'(utils.whereIs(self.elements,"id",elm["master"])["class"],**elm["options"],command=eval("{elm["command"]}"){",cmdargs="+str(cmdargs) if cmdargs != None else ""}{",cmdkwargs="+str(cmdkwargs) if cmdkwargs != None else ""})')
							_elm["class"] = eval("qctk."+elm["type"]+f'(utils.whereIs(self.elements,"id",elm["master"])["class"],**elm["options"],command=eval("{elm["command"]}"){",cmdargs=cmdargs" if cmdargs != None else ""}{",cmdkwargs=cmdkwargs" if cmdkwargs != None else ""})')
							try: #Tries to bind a command to the widget
								_elm["class"].bind("mouse-single" if elm["bind"]["trigger"] == "<Button-1>" else "keypress",elm["bind"]["trigger"],eval(elm["bind"]["command"]))
							except KeyError: pass
							except Exception as exc:
								print(f"Failed to bind command '{elm['bind']['command']}' with trigger '{elm['bind']['trigger']}' to element with name '{elm['name']}'")
						except KeyError: _elm["class"] = eval("qctk."+elm["type"]+f"(utils.whereIs(self.elements,'id',elm['master'])['class'],**elm['options'])")

				else: #Configures values for Windows
					if self.environment == "ctk":
						_elm["class"] = eval(elm["type"] + "()")
						try: set_default_color_theme(elm["colortheme"])
						except KeyError: pass
						try: _elm["class"].title(elm["title"])
						except KeyError: _elm["class"].title("jsonWin Application")
						try: _elm["class"].geometry(elm["geometry"])
						except KeyError: pass
						try: set_appearance_mode(elm["appearancemode"])
						except KeyError: set_appearance_mode("dark")

					else:
						_elm["class"] = eval("qctk." + elm["type"] + f"(application=self.qtapp)")
						try: qctk.ThemeManager.set_color_theme(elm["qtcolortheme"])
						except KeyError: pass
						try: _elm["class"].title(elm["title"])
						except KeyError: _elm["class"].title("jsonWin Application")
						try: _elm["class"].geometry(elm["geometry"])
						except KeyError: pass
						"""
						try: set_appearance_mode(elm["appearancemode"])
						except KeyError: set_appearance_mode("dark")"""

				self.elements.append(_elm) #Stores the widget (class) data
		pgb.finish()
		pbw.endwin(pgbw)

	def stackExistingElement(self,id:str,newName:str,changeCommand=None,changeRow=1,changeColumn=0,assignDirect=True): #Stacks an element already existing
		elmData = deepcopy(utils.whereIs(self.elements,'id',id))
		elmData["id"] = newName

		if "grid" in elmData.keys():
			elmData["grid"]["row"] = elmData["grid"]["row"] + changeRow
			elmData["grid"]["column"] = elmData["grid"]["column"] + changeColumn

		if changeCommand not in (None,False,True) and type(changeCommand) == dict:
			elmData["class"].configure(command=changeCommand["command"])
			if "cmdargs" in changeCommand.keys(): elmData["class"].configure(cmdargs=changeCommand["cmdargs"])
			if "cmdkwargs" in changeCommand.keys(): elmData["class"].configure(cmdkwargs=changeCommand["cmdkwargs"])

		if assignDirect:
			if "grid" in elmData.keys():
				elmData["class"].grid(**elmData["grid"])
			else:
				elmData["class"].pack(**elmData["pack"])
		self.elements.append(elmData)

	def assignElements(self,group): #Assigns elements of a group
		for elm in self.elements:
			if elm["group"] == group:
				try:
					elm["class"].grid(**elm["grid"])
					elm["assigned"] = True
				except KeyError:
					try:
						if self.environment == "ctk": elm["class"].pack(**elm["pack"])
						else: elm["class"].pack(direction="h",**elm["pack"])
						elm["assigned"] = True
					except KeyError: pass

	def assignElement(self,name:str): #Assigns an element with a name
		for elm in self.elements:
			if elm["id"] == name:
				try:
					elm["class"].grid(**elm["grid"])
					elm["assigned"] = True
				except KeyError:
					try:
						if self.environment == "ctk": elm["class"].pack(**elm["pack"])
						else: elm["class"].pack(direction="h",**elm["pack"])
						elm["assigned"] = True
					except KeyError: pass

	def unassignElements(self,group): #Unssigns elements of a group
		for elm in self.elements:
			if elm["group"] == group:
				if self.environment == "ctk":
					try:
						if elm["grid"]: pass
						elm["class"].grid_forget()
						elm["assigned"] = False
					except KeyError:
						try:
							if elm["pack"]: pass
							elm["class"].pack_forget()
							elm["assigned"] = False
						except KeyError: pass
				else:
					if "master" in list(elm.keys()) and utils.whereIs(self.elements,"id",elm["master"]) != None:
						print(f"INFO: Trying to remove the widget {repr(elm['id'])} from widget {repr(utils.whereIs(self.elements,'id',elm['master'])['id'])}")
						utils.whereIs(self.elements,"id",elm["master"])["class"].removeWidget(elm["class"])
						elm["assigned"] = False

	def unassignElement(self,name:str): #Unssigns an element with a name
		for elm in self.elements:
			if elm["id"] == name:
				if self.environment == "ctk":
					try:
						if elm["grid"]: pass
						elm["class"].grid_forget()
						elm["assigned"] = False
					except KeyError:
						try:
							if elm["pack"]: pass
							elm["class"].pack_forget()
							elm["assigned"] = False
						except KeyError: pass
				else:
					if "master" in list(elm.keys()) and utils.whereIs(self.elements,"id",elm["master"]) != None:
						print(f"INFO: Trying to remove the widget {repr(elm['id'])} from widget {repr(utils.whereIs(self.elements,'id',elm['master'])['id'])}")
						utils.whereIs(self.elements,"id",elm["master"])["class"].removeWidget(elm["class"])
						elm["assigned"] = False

	def assignAll(self): #Assigns every item known
		for elm in self.elements:
			if elm["type"] != "CTk":
				try:
					elm["class"].grid(**elm["grid"])
					elm["assigned"] = True
				except KeyError:
					try:
						if self.environment == "ctk": elm["class"].pack(**elm["pack"])
						else: elm["class"].pack(direction="h",**elm["pack"])
						elm["assigned"] = True
					except KeyError: pass

	def unassignAll(self): #Unssigns every item known
		for elm in self.elements:
			if self.environment == "ctk":
				if elm["type"] != "CTk":
					try:
						if elm["grid"]: pass
						elm["class"].grid_forget()
						elm["assigned"] = False
					except KeyError:
						try:
							if elm["pack"]: pass
							elm["class"].pack_forget()
							elm["assigned"] = False
						except KeyError: pass
			else:
				if "master" in list(elm.keys()) and utils.whereIs(self.elements,"id",elm["master"]) != None:
					print(f"INFO: Trying to remove the widget {repr(elm['id'])} from widget {repr(utils.whereIs(self.elements,'id',elm['master'])['id'])}")
					utils.whereIs(self.elements,"id",elm["master"])["class"].removeWidget(elm["class"])
					elm["assigned"] = False

	def getElements(self): #Prints out every Widget known in a tree-like view (textbased)
		_return = []
		for elm in self.elements:
			_return.append(f"Found new Element of type '{elm['type']}'")
			_return.append(f"   | Name: {elm['id']}")
			_return.append(f"   | Group: {elm['group']}")
			if elm["type"] != "CTk":
				gr = "\033[32m"
				rd = "\033[31m"
				try:
					if elm["grid"]: pass
					_return.append(f"   | {'Assigned by' if elm['assigned'] else 'Configured for'} \033[2m{gr if elm['assigned'] else rd}GRID\033[0m: {elm['grid']}")
				except KeyError:
					_return.append(f"   | {'Assigned by' if elm['assigned'] else 'Configured for'} \033[2m{gr if elm['assigned'] else rd}PACK\033[0m: {elm['pack']}")
				try:
					if elm["master"] in (None,"None","none"): raise KeyError("No master found")
					_return.append(f"   | Master: {elm['master']}")
				except KeyError: _return.append("   | Master: \033[31mNo master found/KeyError")
				_return.append(f"   | Options: {elm['args']}")
			else:
				_return.append(f"   | Options: {elm['args']}")
		print('\n'.join(_return))
		return _return

	def deleteTextFromEntry(self,id,first_index,last_index=None):
		utils.whereIs(self.elements,'id',id)["class"].delete(first_index,last_index=last_index)

	def configureElement(self,id,*args,**kwargs):
		utils.whereIs(self.elements,'id',id)["class"].configure(*args,**kwargs)

	def getElementClass(self,id):
		return utils.whereIs(self.elements,'id',id)["class"]

	def extractElementData(self,id):
		return utils.whereIs(self.elements,'id',id)

	def insertElement(self,id:str,index,text,tags=None):
		utils.whereIs(self.elements,'id',id)["class"].insert(index,text,tags=tags)

	def moreCharGetElm(self,id:str,index1,index2=None):
		return utils.whereIs(self.elements,'id',id)["class"].get(index1,index2=index2)

	def moreCharDelElm(self,id:str,index1,index2=None):
		return utils.whereIs(self.elements,'id',id)["class"].delete(index1,index2=index2)

	def cgetState(self,id,attribute):
		return utils.whereIs(self.elements,'id',id)["class"].cget(attribute)

	def getState(self,id):
		return utils.whereIs(self.elements,'id',id)["class"].get()

	def windowMainloop(self,id):
		utils.whereIs(self.elements,'id',id)["class"].mainloop()

	def windowUpdate(self,id):
		utils.whereIs(self.elements,'id',id)["class"].update()

	def windowDestroy(self,id):
		utils.whereIs(self.elements,'id',id)["class"].destroy()

	def windowCenter(self,id):
		self.center_window(utils.whereIs(self.elements,'id',id)["class"])

	def windowAfter(self,id:str,after:int,command):
		utils.whereIs(self.elements,'id',id)["class"].after(after,command)

	def getScreenSize(self,windowid):
		if self.environment == "ctk":
			win = utils.whereIs(self.elements,'id',windowid)["class"]
			width = win.winfo_screenwidth()
			height = win.winfo_screenheight()
			return {"width":width,"height":height}
		else:
			output = subprocess.check_output('xrandr | grep "*" | cut -d" " -f4', shell=True)
			resolution = output.decode().strip().split('x')
			width, height = int(resolution[0]), int(resolution[1])
			return {"width":width,"height":height}

if __name__ == "__main__":
	try:
		with open(".jsonWin_democonfig.json","r") as fle: pass
		fileselect = True
	except FileNotFoundError: fileselect = False
	load = input("Load Previous settings [Y/n] >>> ").lower()
	if fileselect and (len(load) == 0 or load[0] not in ("n")):
		with open(".jsonWin_democonfig.json","r") as fle:
			dta = fle.readlines()
		mode = dta[0].strip()
		file = dta[1].strip()
		main = dta[2].strip()
	else:
		mode = input("Mode (qt/ctk) >>> ")
		file = input("Load file >>> ")
		main = input("Input id of window to mainloop >>> ")
		with open(".jsonWin_democonfig.json","w+") as fle:
			fle.write(f"{mode}\n{file}\n{main}")
	cls = jsonWin(mode=mode)
	cls.loadFile(file)
	cls.verifyElements()
	cls.assignAll()
	cls.getElements()
	cls.windowMainloop(main)
