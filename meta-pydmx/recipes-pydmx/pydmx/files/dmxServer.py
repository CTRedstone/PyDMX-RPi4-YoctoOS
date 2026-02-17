import time
import socket
import inspect
from pytools.logger import genLogLine as gLL
from pytools.variables import cFN
from copy import deepcopy as dc
from threading import Thread

try:
	with open(".serverlog","w+") as fle: fle.write("")
except: pass

class dmxServer:
	class exceptions():
		class invailidTypeException(Exception): ...
		class invailidAddressException(Exception): ...
		class uncriticalException(Exception): ...
		class serverException(Exception): ...
		class commandException(Exception): ...

	def log(self,src:str,tpe:str,msg:str,eol="\n"):
		print(gLL(f"dmxServer/{src}",tpe,msg),end=eol)
		try:
			with open(".serverlog","a") as fle:
				fle.write(str(gLL(f"dmxServer/{src}",tpe,msg))+"\n")
		except: pass

	class commands():
		"""
		Ignoring the "commands" class name, this class contains the hole command syntax.
		Function calls are separated by spaces instead of dots, and also the arguments just follow the path
		and are separated with spaces. Values get set by key='value'
		Values shouldn't contain spaces
		"""
		class render():
			def start(self):
				self.dp.render()
				return ("OK","rendered")

			def stop(self):
				self.dp.stopRender()
				return ("OK","stop_render")

			def pause(self):
				self.dp.pauseRender()
				return ("OK","pause_render")

			def _continue(self):
				self.dp.continueRender()
				return ("OK","continue_render")

			def startLoop(self):
				Thread(target=self.dp.renderloop).start()
				return ("OK","renderloop_started_in_new_thread")

		class effect():
			def new(self,type="default",universe="0",addr="1",start="0",end="0",speed="50",name="",stepsInHigh="0",stepsInLow="0",offset="0",autoStop="0"):
				if type == "none": return ("ERR","effect_type_not_specified")

				if f"{name+universe+addr if name != '' else type+universe+addr}" not in list(self.fxThreads.keys()):
					_ret = self.dp.generators.baseFX(self.dp,name,int(universe),int(addr),int(start),int(end),float(speed),int(stepsInHigh),int(stepsInLow),type,float(offset),autoStop=bool(int(autoStop)))
					if _ret.split(":") == "failed": return _ret
	
					self.fxThreads[f"{name if name != '' else type}"] = Thread(target=self.dp.effectRender,args=(name,int(universe),int(addr),type))
					self.fxThreads[f"{name if name != '' else type}"].daemon = True
					self.fxThreads[f"{name if name != '' else type}"].start()
	
					return ("OK","generated_effect")
				else: return ("ERR","Already_Existing")
			
			def new_multiple(self,type="default",fixtures="[(0,1)]",start="0",end="0",speed="50",name="",stepsInHigh="0",stepsInLow="0",offset="0",offset_per_fixture="0",autoStop="0"):
				if type == "none": return ("ERR","effect_type_not_specified")
				
				for fixt in eval(fixtures):
					if f"{name+str(fixt) if name != '' else type+str(fixt)}" in list(self.fxThreads.keys()): return ("ERR","Already_Existing")
				
				_ret = self.dp.generators.baseFX_moreFixtures(self.dp,name,eval(fixtures),int(start),int(end),float(speed),int(stepsInHigh),int(stepsInLow),type,float(offset),float(offset_per_fixture),autoStop=bool(int(autoStop)))
				if _ret.split(":") == "failed": return _ret
				for fixt in eval(fixtures):
					self.fxThreads[f"{name+str(fixt) if name != '' else type+str(fixt)}"] = Thread(target=self.dp.effectRender,args=(name,fixt[0],fixt[1],type))
					self.fxThreads[f"{name+str(fixt) if name != '' else type+str(fixt)}"].daemon = True
					self.fxThreads[f"{name+str(fixt) if name != '' else type+str(fixt)}"].start()
	
				return ("OK","generated_effects")

			def trigger(self,type="none",name="none",universe="0",addr="1"):
				self.dp.triggerFX(int(universe),int(addr),type,name)
				return ("OK",f"trigger_effect_to {self.dp.getFXstate(int(universe),int(addr),type,name)}")
			
			def trigger_multiple(self,type="none",name="none",fixtures="[(0,1)]"):
				"""_ret = self.dp.triggerFX_multiple(eval(fixtures),type,name)
				if _ret.split(":") == "failed": return _ret"""
				for fixt in eval(fixtures):
					self.dp.triggerFX(fixt[0],fixt[1],type,name)
				return ("OK",f"triggered_effects")

			def getState(self,type="none",name="none",universe="0",addr="1"):
				_ret = self.dp.getFXstate(int(universe),int(addr),type,name)
				return ("OK",f"state:{_ret}")

		class channels():
			def setChannel(self,universe="0",addr="1",value="0",fade="0.75"):
				self.dp.setChannel(int(universe),int(addr),int(value),float(fade))
				return ("OK","changed_channel_value")

			def blackout(self):
				self.dp.blackout()
				return ("OK","introduced_blackout")

			def allOff(self):
				self.dp.allOff()
				return ("OK","set_all_channels_to_0")

			def getChannel(self,universe="0",addr="1"):
				#try:
				var = self.dp.getAddr(int(universe),int(addr))
				return ("OK",f"get_channel_return_{var}")
				#except Exception as exc:
					#return ("ERR",f"get_addr_failed-{'_'.join(str(exc).split())}")

	def tplAddr(self,addr): #Returns a simple view of a (ip,port) tuple or dictonary as a string
		return f"[IP:{addr[0]} P:{addr[1]}]"

	def __init__(self,PyDmxClass,ip="127.0.0.1",port=9091,maxConnection=5,stopEvent=None,**commandParserVariables):
		"""
		Initializes the Server for dmx control with olaTerminal.
		@param ip defines the IP the server is running at
		@param port defines the port the server is running at
		@param maxConnections defines how many clients can connect to the server at maximum
		@param stopEvent takes a threading event and will stop the server if it is set
		"""
		self.log(cFN(),"info",f"Initializing server at {self.tplAddr((ip,port))}, maxConnections {maxConnection}")
		self.dp = PyDmxClass
		self.fxThreads = {}
		self.enableStopEvent = True if stopEvent != None else False
		self.stopEvent = stopEvent
		if type(port) != int or int(port) < 1 or int(port) > 35676: raise self.exceptions.invailidAddressException(f"Port {port} is invailid")
		self.serverAddr = (ip,port)
		self.maxConnection = 5
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.comm_threads = {"#connections":[]}

		self.cPV = commandParserVariables
		self.log(cFN(),"ok","Initialized")

	def commandParser(self,data=None): #Parses a command string into the executable function for dmxServer.commands
		if data in (None,False): raise self.exceptions.commandException("Argument data of commandParser is None or False - should be string")

		self.log(cFN(),"info",f"Trying to parse data to command: {data}")

		args = []
		kwargs = []
		cmdpath = []
		expressions = data.split()

		for elm in expressions: #In every word of the command, will be checked if it is a keyword/normal argument for command
			self.log(cFN(),"info",f"Processing expression '{elm}' of data",eol="\r")
			if "=" in list(dc(elm)):
				self.log(cFN(),"debug","Detected expression to be a keyword argument",eol="\r")
				kwargs.append(elm)
			elif "'" in list(dc(elm)) or '"' in list(dc(elm)) or "(" in list(dc(elm)) or "[" in list(dc(elm)):
				self.log(cFN(),"debug","Detected expression to be a normal argument",eol="\r")
				args.append(elm)
			else:
				self.log(cFN(),"debug","Detected expression to be a part of the command path",eol="\r")
				cmdpath.append(elm)
		self.log(cFN(),"ok",f"Parsed command successfully: args={args} kwargs={kwargs} cmdpath={cmdpath}")

		command = f"self.commands.{'.'.join(cmdpath)}(self{',' if (args,kwargs) != ([],[]) else ''}{','.join(args)}{',' if args != [] and kwargs != [] else ''}{','.join(kwargs)})" #Adds up everything sorted by the lines above to the final command
		self.log(cFN(),"info",f"Executing command: \"{command}\"")
		try: _ret = eval(command) #Executes the command and stores the return value in _ret
		except Exception as exc:
			self.log(cFN(),"err",f"Executing command returned an Exception: {exc}")
			return ("ERR",f"parser_error-{'_'.join(str(exc).split())}")
		if _ret not in (None,"",False):
			self.log(cFN(),"ok",f"Function returned accepted response: {_ret}")
			return _ret
		else:
			self.log(cFN(),"ok","No vailid response was given, returning without responding")
			return None

	def startServer(self): #Starts the server
		self.log(cFN(),"info","Starting server...")
		try:
			self.server.bind(self.serverAddr)
			self.server.listen(self.maxConnection)
			self.log(cFN(),"ok","Server started")
		except Exception as exc:
			self.log(cFN(),"fatal",f"Starting server failed: {exc}")
			raise self.exceptions.serverException(exc)
			return

		if self.enableStopEvent: #Runs the stopEventHandler in a new thread if enabled
			self.log(cFN(),"info","Starting stop event handler")
			self.sEH = Thread(target=self.stopEventHandler,args=self.stopEvent)
			self.sEH.deamon = True
			self.sEH.start()
			self.log(cFN(),"okay","")

		self.log(cFN(),"debug","Initializing loop for client communication controll")
		while True: #Constantly waits for new clients, then starts a clientServerCommunication in a thread where it checks for commands in every connection
			client_socket, client_addr = self.server.accept()
			self.log(cFN(),"info",f"New Client connected: {self.tplAddr(client_addr)} - Starting new communication thread")
			self.comm_threads["#connections"].append(client_addr)
			self.comm_threads[client_addr] = Thread(target=self.clientServerCommunication,args=(client_socket,client_addr))
			self.comm_threads[client_addr].daemon = True
			self.comm_threads[client_addr].start()

	def clientServerCommunication(self,client_socket,client_addr): #While the client has not signed out, This function will stay in contact checking for commands and executing them
		self.log(cFN(),"info",f"New client communication started with address {self.tplAddr(client_addr)}")
		noreply = False
		while True and client_addr in self.comm_threads["#connections"]:
			data = client_socket.recv(1024).decode("utf-8") #Read message content
			if not data: break
			self.log(cFN(),"info",f"Recieved new message/command: \"{data}\"")
			if data.split()[0] == "!noreply":
				noreply = True
				data = ' '.join(data.split()[1:])
			_ret = self.commandParser(data) #Parse and execute command
			if _ret != None and _ret != "":
				self.log(cFN(),"debug",f"CommandParser returned answer which is not empty and not None: {_ret} - using it to respond to request")
				try:
					if not noreply: client_socket.sendall(f"{_ret[0]} {_ret[1]}".encode('utf-8')) #returns result
				except Exception as exc:
					self.log(cFN(),"err",f"Failed to respond to request: {exc} - stopping connection to client")
					break
		try: del self.comm_threads[client_addr]
		except KeyError: pass
		try: del self.comm_threads["#connections"][client_addr]
		except KeyError: pass
		self.log(cFN(),"warn",f"Exiting from clientServerCommunication thread with {self.tplAddr(client_addr)} and closing connection to named client. This can be caused by a failed try to respond or an invailid message/command sent by client")
		client_socket.close()

	def getConnections(self,getType="return"): #Returns the connections signed for clientServerCommunication
		"""
		getType can be: "return" or "print"
		"""

		_return = []
		for elm in self.comm_threads["#connections"]: _return.append(elm)

		if getType == "print": print('\n'.join(_return))
		elif getType == "return": return _return
		else: raise self.exceptions.invailidTypeException(f"Type '{getType}' is invailid as returntype of dmxServer.getConnections()")

	def closeConnection(self,addr:str): #Closes a connection to addr
		if addr == "": raise self.exceptions.invailidAddressException(f"Address can not be empty")
		elif addr not in self.comm_threads["#connections"]:
			raise self.exceptions.invailidAddressException(f"Connection to address '{addr}' can not be closed because there is no connection to such an address")
		self.log(cFN(),"info",f"Closing connection to ip {addr}")
		try: del self.comm_threads["#connections"][addr]
		except KeyError: pass
		try: self.comm_threads[addr].close()
		except Exception as exc: raise self.exceptions.uncriticalException(f"INFO: Connection to address '{addr}' seems to be already closed")
		try: del self.comm_threads[addr]
		except KeyError: pass

	def stopServer(self,wait=0.0): #Stops the server
		if wait != 0.0: self.log(cFN(),"warn",f"Stopping server in {wait}s...")
		else: self.log(cFN(),"warn","Stopping server...")
		time.sleep(wait)
		_exc = []
		try:
			for elm in self.comm_threads["#connections"]: #Stops every clientServerCommunication thread
				self.log(cFN(),"debug",f"Address '{elm}' found - stopping communication with client")
				try:
					self.comm_threads[elm].stop()
					del self.comm_threads[elm]
					del self.comm_threads["#connections"][elm]
					self.log(cFN(),"ok",f"Closed connection to address '{elm}'")
				except Exception as exc:
					self.log(cFN(),"err",f"Failed to close connection to client '{elm}': {exc}")
		except Exception as exc: _exc.append(str(exc))
		finally:
			try:
				self.log(cFN(),"info","Closing server...")
				self.server.close() #Closes the server
				self.log(cFN(),"ok","Server successfully closed and stopped, exiting")
			except Exception as exc: _exc.append(str(exc))
			finally:
				if _exc != []:
					self.log(cFN(),"fatal",f"Could not stop the server in the right way due to the following errors: {';'.join(_exc)}")
					raise self.exceptions.serverException("Could not stop Server the right way: "+';'.join(_exc))

	def stopEventHandler(self,event):
		self.log(cFN(),"ok","stopEventHandler is running...")
		while not event.is_set(): pass
		self.log(cFN(),"ok","stop event is set - closing server")
		self.stopServer()

def reloadHelpFile(): #Reads the tree of commands in dmxServer.commands and outputs it in dmxServer.help.txt
	out = []
	maindir = dir(dmxServer.commands)
	for elm1 in maindir:
		if elm1[0]+elm1[1] == "__": pass
		else:
			dir1 = dir(eval(f"dmxServer.commands.{elm1}"))
			cnt2 = 0
			for elm2 in dir1:
				if elm2[0]+elm2[1] == "__": pass
				else:
					cnt2 += 1
					dir2 = dir(eval(f"dmxServer.commands.{elm1}.{elm2}"))
					cnt3 = 0
					for elm3 in dir2:
						if elm3[0]+elm3[1] == "__": pass
						else: cnt3 += 1
					if cnt3 == 0:
						args = ''.join(''.join(str(inspect.signature(eval(f"dmxServer.commands.{elm1}.{elm2}"))).split("self, ")).split("self"))
						out.append(f"{elm1} {elm2} {args}")
			if cnt2 == 0:
				args = ''.join(''.join(str(inspect.signature(eval(f"dmxServer.commands.{elm1}"))).split("self, ")).split("self"))
				out.append(f"{elm1} {args}")
	with open("dmxServer.help.txt","w+") as fle: fle.write("\n".join(out))
