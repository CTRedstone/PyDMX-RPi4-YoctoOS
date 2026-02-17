import prgbarWin as pbw
from os import system as execute
from pytools.variables import FE
from pytools.progressbar import progressbar as pgb
from threading import Thread
from math import sin,cos,sqrt
from copy import deepcopy, deepcopy as dc
import time

try: from typing import Literal
except ImportError: from typing_extensions import Literal

class PyDMX:
	class exceptions():
		class invailidValueException(Exception): ...
		class invailidAddressException(Exception): ...

	def log(self,tpe:str,msg:str):
		color = FE["blue"] if tpe == "debug" else FE["red"] if tpe == "err" else FE["cyan"] if tpe in ("inf","info") else FE["green"] if tpe in ("done","ok","okay") else FE["yellow"] if tpe == "warn" else ""
		if self.debug == True or tpe != "debug": print(color+f"[{'' if self.mainapp == False else self.mainapp + '/'}olaTerminal] [{tpe.upper()}] {msg}"+FE["reset"])

	def __init__(self,**kwargs):
		"""
		a class to use the ola client through terminal commands

		Argument | Type | Description
		---------+------+---------------------------------
		universes| list | List of universe numbers that are used
		notAtOn  | list | List of tuples with (universe,address) of addresses who shouldn't be affected by an whiteout()
		mainApp  | str  | Name of main application which is using this module. Is optional
		"""

		try: self.debug = kwargs["debug"]
		except: self.debug = False

		try: self.whiteoutExceptions = kwargs["notAtOn"]
		except KeyError: self.whiteoutExceptions = []

		try: self.mainapp = kwargs["mainApp"]
		except KeyError: self.mainapp = False
		
		try: self.showprcwin = kwargs["showprcwin"]
		except KeyError: self.showprcwin = True

		self.log("info","Initializing...")

		self.log("warn","Trying to restart ola service...")
		execute("sudo systemctl restart olad") #Restarts OLA Service (to make sure it connects to the adapter)
		self.log("warn","Tried, waiting 5 secounds...")
		"""timeProg = pgb(msteps=20,left="..",done="##",msg="Time elapsed:")
		for i in range(20):
			timeProg.step("",1)
			time.sleep(0.25)
		timeProg.finish()
		del timeProg"""
		if self.showprcwin:
			pbw.clrtheme("black-orange.json")
			pgbw = pbw.initwin()
			pgbw = pbw.setinf(pgbw,"[PyDMX] Restarting olad")
			pgbw = pbw.setprg(pgbw,progress=0)
			for i in range(int(5/0.2)): #Wait five secounds to make sure ola is restarted when proceeding
				pgbw = pbw.setprg(pgbw,prgfloat=i/(5/0.2))
				time.sleep(0.2)
			pgbw = pbw.setprg(pgbw,progress=100)
			pbw.endwin(pgbw)
		else: time.sleep(5)

		self._render = "false"
		self.universes = kwargs["universes"] #Amount of universes
		self.dmxValues = {}
		for elm in self.universes: #Set all DMX channels to 0
			self.dmxValues[elm] = []
			for i in range (512): self.dmxValues[elm].append(str(0))
		self.effects = {"fxCount":{"sinFx":0,"cosFx":0,"shutterFx":0,"fadeFx":0,"baseFx":0}}
		#for i in range (512): self.effects[i] = {}
		
		#Initialize FX debug file
		with open("olaTerminal.fxdebug.txt","w+") as fle: fle.write("")
		
		self.log("done","Initialized")

	def getAddr(self,universe:int,addr:int): #Reads the DMX value of an address
		return int(self.dmxValues[universe][addr-1])

	def render(self,**kwargs): #Renderes the DMX values one time
		try: deb = kwargs["debug"]
		except KeyError: deb = True
		if deb == True: self.log("info","Rendering values for all universes...")
		for elm in self.universes: #render DMX Values for all Universes
			execute(f"ola_streaming_client -u {str(elm)} -d {','.join(list(map(str,self.dmxValues[elm])))}")
			if deb == True: self.log("debug",f"Rendering command: 'ola_streaming_client -u {elm} -d {','.join(list(map(str,self.dmxValues[elm])))}'")
		if deb == True: self.log("done","Rendered")

	def triggerDebug(self): self.debug = not self.debug #Triggers the debug mode of logging

	def renderloop(self): #Renders constantly (with breaks of 0.05 secounds)
		self._render = "true"
		self.log("info","Introducing renderloop")
		while True:
			if self._render == "true": self.render(debug=False)
			elif self._render == "pause": pass
			elif self._render == "false": pass
			elif self._render == "exit": break
			time.sleep(0.05)

	def triggerFX(self,universe:int,addr:int,type:str,id:str,*args): #Triggers an effect to on/off
		self.log("debug",f"trying to trigger FX of addr {addr} in universe {universe} with type '{type}' and id '{id}'")
		fxKey = tuple([universe,addr-1,type,id])
		try: self.effects[fxKey]["active"] = not self.effects[fxKey]["active"]
		except KeyError:
			self.log("err","No such effect")
			return "failed:notFound"
		return "proceed:done"
	
	def triggerFX_multiple(self,fixtures:list[tuple[int,int]],type:str,id:str,*args):
		_return = "proceed:done"
		for fixt in fixtures:
			_ret = self.triggerFX(fixt[0],fixt[1],type,id)
			if _ret.split(":")[0] == "failed": _return = _ret
		return _return

	def getFXstate(self,universe:int,addr:int,type:str,id:str,*args) -> bool: #Returns the state of an effect
		self.log("info",f"Trying to get state of FX of channel {addr} in universe {universe} with type '{type}' and id '{id}'")
		try: return self.effects[tuple([universe,addr-1,type,id])]["active"]
		except KeyError:
			self.log("err",f"No such effect")
			return None

	def deprecatedEffectRender(self,universe:int,addr:int,type:str,debug=False):
		element = None
		for i in range(len(self.effects)):
			elm = self.effects[i]
			try:
				if (elm["universe"],elm["addr"],elm["type"]) == (universe,addr,type):
					element = i
			except KeyError: pass
		if element == None:
			self.log("warn",f"Could not find effect in universe {universe} at address {addr} with type '{type}', skipping effectRender")
			return
		while self._render == "true":
			try:
				if (self.effects[element]["universe"],self.effects[element]["addr"],self.effects[element]["type"]) == (universe,addr,type):
					if self.effects[element]["active"] == True:
						self.dmxValues[universe][addr-1] = self.effects[element]["values"][self.effects[element]["value"]]
						if self.effects[element]["value"] == len(self.effects[element]["values"])-1 and self.effects[element]["autoStop"] == False:
							self.effects[element]["value"] = 0
						elif self.effects[element]["value"] == len(self.effects[element]["values"])-1 and self.effects[element]["autoStop"] == True:
							if debug: self.log("info",f"AutoStop of effect with type '{type}' at addr {addr} in universe {universe} active and FX reached end - exiting FX renderer for that effect")
							break
						else: self.effects[element]["value"] += 1
						try: time.sleep(0.1-(self.effects[element]["speed"]/1000))
						except ValueError:
							self.log("err",f"Speed of effects should not be larger than 100, stopping effect renderer of effect at addr {addr} in universe {universe} with type '{type}'")
							break
			except KeyError as exc:
				self.log("err",f"Got Unexpected keyerror in effect renderer for effect in universe {universe} at address {addr} with type '{type}', exiting renderer")
				break
			except IndexError as exc:
				self.log("err",f"Got unexpected IndexError in effect renderer for effect in universe {universe} at address {addr} with type '{type}', exiting renderer")
				break

	def effectRender(self,id:str,universe:int,addr:int,_type: Literal["sinFx","cosFx","fadeOn","fadeOff","shutterFx","fadeFx","baseFx"] = "baseFx",debug=False,render=False):
		#Renders one specific effect, should run in a thread to not block the other functionalities of the code
		if debug: self.log("info",f"Trying to start effect for [U:{universe} A:{addr}] of type [T:{_type}] and with ID '{id}'")
		effectKey = tuple([universe,addr-1,_type,id])
		fxName = f"[U:{universe} A:{addr} T:{_type} N:'{id}']"

		def relFD(fxKey):
			return self.effects[fxKey]

		try: fxdata = relFD(effectKey)
		except KeyError as exc:
			self.log("err",f"Could not find effect from identifier {exc}. Please make shure you call effectRender with the right universe, addr (address), type and id (identifier)")
			return

		if debug: self.log("info",f"Changing value 'active' of FX {fxName} to True (active) because new FX renderer started")
		self.effects[effectKey]["active"] = True

		if debug: self.log("info",f"Starting effectRender for FX {fxName}")
		nxttime = time.perf_counter()
		while effectKey in list(self.effects.keys()): #self._render == "true":
			#if fxdata["active"] == True: #Checks if the effect is active
			try:
				fxdata = relFD(effectKey)
				if not (type(fxdata["values"][fxdata["value"]]) == str and fxdata["values"][fxdata["value"]].split()[0] == "pausefor"):
					if fxdata["active"] == True: self.dmxValues[universe][addr-1] = fxdata["values"][fxdata["value"]] #Sets the value of the DMX address
					else: pass #print(fxdata["active"],end="\r")
				if fxdata["value"] == len(fxdata["values"])-1 and fxdata["autoStop"] == False:
					self.effects[effectKey]["value"] = 0
					if debug: self.log("debug",f"Returned to FX beginning of FX {fxName}")
				elif fxdata["value"] == len(fxdata["values"])-1 and fxdata["autoStop"] == True:
					if debug: self.log("info",f"RX {fxName} has set the autoStop data and reached the end, deactivating effect") #stopping effectRender")
					self.effects[effectKey]["active"] = False
					fxdata["active"] = False
				else:
					if type(fxdata["values"][fxdata["value"]]) == str and fxdata["values"][fxdata["value"]].split()[0] == "pausefor":
						val = fxdata["values"][fxdata["value"]]
						steps = int(val.split("~")[1])
						waitat = int(val.split("@")[1])
						if fxdata["active"] == True: self.dmxValues[universe][addr-1] = dc(waitat)
						else: print(fxdata["active"],end="\r")
						try:
							nxttime += ((1/fxdata["speed"])*steps)
							sleep = nxttime - time.perf_counter()
							if sleep > 0: time.sleep(sleep)
							#time.sleep((1/fxdata["speed"])*steps)
						except ZeroDivisionError:
							time.sleep(0.0001*steps)
					self.effects[effectKey]["value"] += 1
				if render: self.render()
				try:
					nxttime += (1/fxdata["speed"])
					sleep = nxttime - time.perf_counter()
					if sleep > 0: time.sleep(sleep)
					#time.sleep(1/fxdata["speed"])
				except ZeroDivisionError: pass
			except Exception as exc: self.log("err",f"Some error occured while trying to execute effect {fxName} ({exc})")
			"""while fxdata["active"] == False:
				time.sleep(0.001)"""
		self.log("done",f"Effect renderer for effect {fxName} stopped")

	def renderlist(self,universe:int,render,debug=False): #Renders the list of max. 512 integers in render to the universe given
		if debug: self.log("info","Trying to render given list...")
		execute(f"ola_streaming_client -u {universe} -d {','.join(render)}")
		if debug: self.log("done",f"Rendered list in universe ({universe}): {render}")

	def setChannel(self,universe:int,id:int,dest:int,fade:float,debug=False): #Sets the channel value to dest
		if id > 512 or id < 1:
			self.log("err",f"Invailid DMX Address: {id}")
			raise self.exceptions.invailidAddressException(f"Address can only be between 1 and 512")
		if dest > 512 or dest < 0:
			self.log("err",f"Invailid DMX Value: {dest}")
			raise self.exceptions.invailidValueException("Value has to be between 0 and 512")
		"""if fade > 100 or fade < 0:
			self.log("err",f"Invailid Fade value: {fade} (needs to be between 0 and 100)")
			raise self.exceptions.invailidValueException("'fade' needs to be between 0 and 100")"""
		if fade == 0.0:
			self.dmxValues[universe][id-1] = str(dest)
			self.log("done",f"Set value {dest} for channel {id} in universe {universe}") #continued that way: with rendering {'enabled' if render == True else 'disabled'}")
		else:
			def fadeAddr(self,universe:int,addr:int,value:int,steps:float):
				cur = self.getAddr(universe,addr)
				calc = 0.0
				diff = sqrt((value-cur)**2)
				rep = diff/(steps/10) #Amount of loops having get done
				if rep <= 0: return
				step = sqrt((diff/rep)**2) #What needs to be added to value per step
				for i in range(int(rep)):
					#self.setChannel(universe,addr,int(cur+(step*(i+1))),0.0)
					if value > cur:
						#self.log("info",f"Adding {int(cur+step*(i+1))} to current")
						self.dmxValues[universe][addr-1] = str(int(cur+step*(i+1)))
					else:
						#self.log("info",f"Removing {int(cur-step*(i+1))} from current")
						self.dmxValues[universe][addr-1] = str(int(cur-step*(i+1)))
					time.sleep(0.0001) #Value is seconds, value/1000 is 0.001
					if self._render == "exit": return
			thr = Thread(target=lambda:fadeAddr(self,universe,id,dest,fade))
			thr.start()
			thr.join()
			self.log("done","Started fade to named value")
		#if render == True: self.render() #is the last parameter of the function

	def blackout(self,debug=False): #Deactivates every Lamp, will pause the renderloop so that the blackout won't get overwritten
		for elm in self.universes:
			self.renderlist(elm,self.generators.dmxList(self,0),debug=debug)
		if debug: self.log("info","Blackout introduced")
		if self._render != "false": self._render = "pause"

	def whiteout(self,debug=False): #Sets every channel to 255 except the channels in PyDMX.whiteoutExceptions
		for elm in self.universes:
			rendbfr = self.generators.dmxList(self,255,debug=debug)
			for elm2 in self.whiteoutExceptions:
				if elm2[0] == elm: rendbfr[elm2[1]-1] = self.getAddr(elm2[0],elm2[1])
			self.renderlist(elm,self.generators.dmxList(self,255),debug=debug)
		self.log("info","Blackwhite introduced")
		if self._render != "false": self._render = "pause"

	def allOff(self,debug=False): #Resets every DMX Value known
		if debug: self.log("warn","Resetting all DMX Values back to 0...")
		for elm in self.universes:
			if debug: self.log("debug",f"Processing universe {elm}")
			self.dmxValues[elm] = self.generators.dmxList(self,0,debug=debug)
		self.log("done","Done")
		self.render(debug=debug)

	def pauseRender(self): #pauses the renderloop
		self.log("info","Pausing rendering...")
		if self._render != "false": self._render = "pause"
		self.log("done","Done")

	def continueRender(self): #Continues the renderloop
		self.log("info","Restarting rendering...")
		if self._render != "false": self._render = "true"
		self.log("done","Done")

	def stopRender(self): #Stops the renderloop
		self.log("warn","Exiting (stopping render-loop)...")
		self._render = "exit"
		self.log("done","Done")

	class generators():
		def dmxList(self,allto:int,debug=False): #Generates a full DMX-Universe of values set to allto
			_return = []
			for i in range(512): _return.append(str(allto))
			return _return
		"""
		class effects():
			def sinFX(self,universe:int,addr:int,start:int,end:int,speed:float,id:str):
				effectKey = str([universe,addr-1,"sinFx",id])
				self.effects["fxCount"]["sinFx"] += 1

				self.effects[effectKey] = {"autoStop":False,"type":"sin","minValue":start,"maxValue":end,"speed":speed,"value":0,"universe":universe,"addr":addr,"values":[],"active":False}

				#for i in range (359):
				#	self.effects[addr-1]["values"].append(str(sqrt(int(sin(i)*end+start)**2)))

				for i in range(end-start):
					self.effects[effectKey]["values"].append(str(start+i))
				for i in range(end-start):
					self.effects[effectKey]["values"].append(str(end-i))

				self.log("debug",f"Data of new sinFX in universe {universe} at address {addr}: {self.effects[effectKey]}")

			def cosFX(self,universe:int,addr:int,start:int,end:int,speed:float,id:str):
				effectKey = tuple([universe,addr-1,"cosFx",id])
				self.effects["fxCount"]["cosFx"] += 1

				self.effects[effectKey] = {"autoStop":False,"type":"cos","minValue":start,"maxValue":end,"speed":speed,"value":0,"universe":universe,"addr":addr,"values":[],"active":False}

				#for i in range (359):
				#	self.effects[effectKey]["values"].append(str(sqrt(int(sin(i)*end+start)**2)))

				for i in range(end-start):
					self.effects[effectKey]["values"].append(str(end-i))
				for i in range(end-start):
					self.effects[effectKey]["values"].append(str(start+i))

				self.log("debug",f"Data of new cosFX in universe {universe} at address {addr}: {self.effects[effectKey]}")

			def shutterFX(self,universe:int,addr:int,start:int,end:int,speed:float,id:str):
				effectKey = tuple([universe,addr-1,"shutterFx",id])
				self.effects["fxCount"]["shutterFx"] += 1

				self.effects[effectKey] = {"autoStop":False,"type":"shutter","minValue":start,"maxValue":end,"speed":speed,"value":0,"universe":universe,"addr":addr,"values":[],"active":False}

			def fadeFX(self,universe:int,addr:int,start:int,end:int,speed:float,id:str):
				effectKey = tuple([universe,addr-1,"fadeFx",id])
				self.effects["fxCount"]["fadeFx"] += 1

				self.effects[effectKey] = {"autoStop":True,"type":"fade","minValue":start,"maxValue":end,"speed":speed,"value":0,"universe":universe,"addr":addr,"values":[],"active":False}

				if end-start < 0:
					for i in range(start-end):
						self.effects[effectKey]["values"].append(str(start-i))
					self.effects[effectKey]["values"].append(str(end))
				elif end-start > 0:
					for i in range(end-start):
						self.effects[effectKey]["values"].append(str(start+i))
					self.effects[effectKey]["values"].append(str(end))
				else:
					self.log("warn",f"Could not generate fadeFX in universe {universe} at address {addr} due to unexcepted value ratios between start (-> {start}) and end (-> {end})")
					self.log("warn",f"Generating fadeFX list for universe {universe} and address {addr} for two frames at current value of address")
					for i in range(2):
						self.effects[effectKey]["values"].append(str(self.getAddr(universe,addr)))

				self.log("debug",f"Data of new fadeFX in universe {universe} at address {addr}: {self.effects[effectKey]}")"""
		
		def baseFX_moreFixtures(self,id:str,fixtures:list[tuple[int,int]],minval:int,maxval:int,speed:float,stepsInHigh:int,stepsInLow:int,fxType: Literal["sin","cos","triangle","fadeOn","fadeOff","default"],offset:float,offset_per_fixt:float,autoStop=False):
			"""
			Effect Generation:
			@param id is a custom name to re-identify the effect, if there are multiple effects for one address
			@param fixtures is a list with tuples with the data of affected fixtures, data needs to look like that: (universe,address)
			@param minval is the minimum value the channel can have in the effect
			@param maxval is the maximum value the channel can have in the effect
			@param speed is the speed in which the effect will be executed
			@param stepsInHigh defines the speed*stepsInHigh time in maxval for the channel
			@param stepsInLow defines the speed*stepsInLow time in minval for the channel
			@param fxType selects the effect generator
			@param autoStop is normally False, but if set to True, the effect will automatically stop after one execution
			"""
			
			try:
				done = []
				fail = None
				for fixt in fixtures:
					_ret = self.generators.baseFX(self,id,fixt[0],fixt[1],minval,maxval,speed,stepsInHigh,stepsInLow,fxType,offset+(offset_per_fixt*len(done)),autoStop=autoStop)
					if _ret.split(":")[0] == "failed":
						fail = _ret
						break
					done.append(dc(fixt))
				
				if fail != None:
					for fixt in fixtures:
						if fixt in done:
							break
						else:
							try: del self.effects[(fixt[0],fixt[1],fxType,id)]
							except: pass
					return fail
				else: return "proceed:done"
			except Exception as exc: return f"failed:{'_'.join(str(exc).split())}"
		
		def baseFX(self,id:str,universe:int,addr:int,minval:int,maxval:int,speed:float,stepsInHigh:int,stepsInLow:int,fxType: Literal["sin","cos","triangle","fadeOn","fadeOff","default"],offset:float,autoStop=False):
			"""
			Effect Generation:
			@param id is a custom name to re-identify the effect, if there are multiple effects for one address
			@param universe is the universe of the channel the effect will affect
			@param addr is the channel id in the universe the efffect will affect
			@param minval is the minimum value the channel can have in the effect
			@param maxval is the maximum value the channel can have in the effect
			@param speed is the speed in which the effect will be executed
			@param stepsInHigh defines the speed*stepsInHigh time in maxval for the channel
			@param stepsInLow defines the speed*stepsInLow time in minval for the channel
			@param fxType selects the effect generator
			@param autoStop is normally False, but if set to True, the effect will automatically stop after one execution
			"""
			effectKey = tuple([universe,addr-1,fxType,id])
			fxName = f"[U:{universe} A:{addr} T:{fxType} N:'{id}']"
			
			if offset > 360 or offset < 0:
				self.log("err",f"Could not generate baseFX {fxName} because 'offset' value is not between 0 and 360")
				return "failed:offset-invailid"
			else:
				offset = (offset/360)*100
				self.log("info",f"New generated offset is {offset}")
			
			self.effects["fxCount"]["baseFx"] += 1

			self.effects[effectKey] = {"universe":universe,"addr":addr,"autoStop":autoStop,"type":f"base/{type}","minValue":minval,"maxValue":maxval,"speed":speed,"value":0,"values":[],"active":False}

			if minval-maxval < 0:
				min = minval
				max = maxval
			elif minval-maxval > 0:
				min = maxval
				max = minval
			else:
				self.log("warn",f"Could not generate baseFX {fxName} because there is no distance between minval and maxval")
				self.effects[effectKey]["values"] = [0]
				return "failed:dist-0"
			
			def offsVals(values:list,off:float):
				_ret = []
				newnull = -1
				addvaluecnt = []
				addvalueind = []
				for i in range(len(values)):
					elm = values[i]
					if type(elm) == "str" and elm.split()[0] == "pausefor":
						addvaluecnt.append([dc(int(elm.split("~")[1])),dc(int(elm.split("@")[1]))])
						addvalueind.append(dc(i))
						
				addtoi = 0
				for i in range(len(values)):
					if i in addvalueind:
						stpsAppend = 0
						stpsInsert = 0
						cur = addvaluecnt[addvalueind.index(i)]
						for e in range(cur[0]):
							if ((i+addtoi+e)/360)*100 < off: stpsAppend += 1
							elif ((i*addtoi+e)/360)*100 >= off:
								if newnull == -1: newnull = dc(i)+1
								stpsInsert += 1
						_ret.append(f"pausefor ~{stpsAppend}~ @{cur[1]}@")
						_ret.insert(0,f"pausefor ~{stpsInsert}~ @{cur[1]}@")
						addtoi += dc(cur[0])
					else:
						if ((i+addtoi)/360)*100 < off: _ret.append(dc(values[i]))
						elif ((i+addtoi)/360)*100 >= off and newnull == -1:
							newnull = dc(i)
							_ret.append(dc(values[i]))
						else:
							_ret.insert(dc(i-newnull),dc(values[i]))
				return _ret

			values = []
			if fxType == "default": #default FX looks the following: -|_| #normal dash shows the max state
				#for i in range(stepsInHigh): values.append(max)
				#for i in range(stepsInLow): values.append(min)
				values.append(f"pausefor ~{stepsInHigh}~ @{max}@")
				values.append(f"pausefor ~{stepsInLow}~ @{min}@")
				
				self.effects[effectKey]["values"] = offsVals(values,offset)
				"""newnull = -1
				for i in range(len(values)):
					if (i/360)*100 < offset: self.effects[effectKey]["values"].append(dc(values[i]))
					elif (i/360)*100 >= offset and newnull == -1:
						newnull = dc(i)
						self.effects[effectKey]["values"].append(dc(values[i]))
					else:
						self.effects[effectKey]["values"].insert(dc(i-newnull),dc(values[i]))"""
			elif fxType == "triangle": #triangle FX looks the following: /-\_
				cv = 0 #current value, will help to set stepsInHigh/stepsInLow because it is kept after finishing the loops of changing values
				for i in range(max+1-min):
					values.append(min+i)
					cv = min+i
				#for i in range(stepsInHigh): values.append(cv)
				values.append(f"pausefor ~{stepsInHigh}~ @{cv}@")
				for i in range(max+1-min):
					values.append(max-i)
					cv = max-i
				#for i in range(stepsInLow): values.append(cv)
				values.append(f"pausefor ~{stepsInLow}~ @{cv}@")
				
				self.effects[effectKey]["values"] = offsVals(values,offset)
			elif fxType == "sin": #generates a sinus wave effect
				cv = int(sin(min/255)*255)
				for i in range(max+1-min):
					values.append(int(sin((min+i)/255)*255))
					cv = int(sin((min+i)/255)*255)
				#for i in range(stepsInHigh): values.append(cv)
				values.append(f"pausefor ~{stepsInHigh}~ @{cv}@")
				for i in range(max+1-min):
					values.append(int(sin((max-i)/255)*255))
					cv = int(sin((max-i)/255)*255)
				#for i in range(stepsInLow): values.append(cv)
				values.append(f"pausefor ~{stepsInLow}~ @{cv}@")
				
				self.effects[effectKey]["values"] = offsVals(values,offset)
			elif fxType == "cos": #generates a cosinus wave effect
				cv = int(cos(min/255)*255)
				for i in range(max+1-min):
					values.append(int(cos((min+i)/255)*255))
					cv = int(cos((min+i)/255)*255)
				#for i in range(stepsInHigh): values.append(cv)
				values.append(f"pausefor ~{stepsInHigh}~ @{cv}@")
				for i in range(max+1-min):
					values.append(int(cos((max-i)/255)*255))
					cv = int(cos((max-i)/255)*255)
				for i in range(stepsInLow): values.append(cv)
				values.append(f"pausefor ~{stepsInLow}~ @{cv}@")
				
				self.effects[effectKey]["values"] = offsVals(values,offset)
			elif fxType in ("fadeOn","fadeIn"): #generates a simple fade on effect like _/ and should be used with autoStop
				cv = min
				#for i in range(stepsInLow): values.append(cv)
				values.append(f"pausefor ~{stepsInLow}~ @{cv}@")
				for i in range(max+1-min):
					values.append(min+i)
					cv = min+i
				#for i in range(stepsInHigh): values.append(cv)
				values.append(f"pausefor ~{stepsInHigh}~ @{cv}@")
				
				self.effects[effectKey]["values"] = offsVals(values,offset)
			elif fxType in ("fadeOff","fadeOut"): #generates a simple fade off effect like \_ and should be used with autoStop
				cv = max
				for i in range(stepsInHigh): values.append(cv)
				values.append(f"pausefor ~{stepsInHigh}~ @{cv}@")
				for i in range(max+1-min):
					values.append(max-i)
					cv = max-i
				values.append(f"pausefor ~{stepsInLow}~ @{cv}@")
				
				self.effects[effectKey]["values"] = offsVals(values,offset)
			else:
				return "failed:unknown_type"
			
			self.effects[effectKey]["values"].append(min if fxType not in ("fadeOn","fadeIn") else max)
			
			with open("olaTerminal.fxdebug.txt","a") as fle:
				wrt = ["="*30,f"FX {fxName}","-"*30,str(self.effects[effectKey]["values"]),""]
				fle.write('\n'.join(wrt))

			self.log("ok",f"Generated fx {fxName}")
			return "proceed:done"

if __name__ == "__main__":
	print("\n================================================\n")

	def log(tpe:str,msg:str):
		print(f"[olaTerminal] [{tpe.upper()}] {msg}"+FE["reset"])

	log("info",FE["cyan"]+FE["bold"]+"Starting tutorial code for olaTerminal control"+FE["reset"])
	dp = PyDMX(universes=[0])
	log("info",FE["green"]+"Created class using 'dp = PyDMX(universes=[0])'")
	log("info",FE["green"]+"Using the module 'threading' ('from threading import Thread') we'll create an update thread")
	thr = Thread(target=dp.renderloop)
	log("info",FE["green"]+"This thread is created by 'thr = Thread(target=dp.renderloop)' and will be started with 'thr.start()'")
	thr.start()

	log("info",FE["purple"]+FE["bold"]+"Starting from here you can do what you want. In this example, you can set Channel-Values to a specific number")
	log("warn",FE["yellow"]+"From here, you should make a try/except block around the hole code. should something go wrong, the code in the except-block should say: 'dp.stopRender()'")
	log("info",FE["green"]+"One example: you can use the dp.setChannel method, to set an address [param.2] in universe [param.1] to value [param.3]. If you already have a render loop, you should set the render parameter [param.4] to False: 'dp.setChannel(0,1,512,False)'")

	try:
		while True:
			dp.setChannel(int(input("Universe >>> ")),int(input("Address >>> ")),int(input("Value >>> ")),False)
	except Exception as exc:
		log("err",FE["red"]+f"An error occured while trying to set an channel to a value: {exc}")
		log("info",FE["green"]+"This error got caught by the try/except block. to get the specific error message, you can simply use 'except Exception as exc:' to get the reason of the exception")
		dp.stopRender()
	log("info",FE["purple"]+"Exiting...")
