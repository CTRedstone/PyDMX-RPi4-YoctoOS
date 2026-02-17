import time
import socket as sc
from pytools.logger import genLogLine as gLL
from pytools.variables import cFN

class dmxClient:
	def log(self,src:str,tpe:str,msg:str):
		print(gLL(f"{self.master}/dmxClient/{src}" if self.master != "" else f"dmxClient/{src}",tpe,msg))

	def notAvail(self,src:str): #If the server connection initialization doesn't work, this method will be called every time a method is used
		self.log(src,"err","Due to errors while prepearing/using dmxClient, it can not be used")

	def __init__(self,ip="127.0.0.1",port=9091,master=""):
		self.master = master
		self.enable = True
		self.aC = False
		self.log(cFN(),"info",f"Initializing dmxClient, target server: [IP:{ip} P:{port}]")
		try: #Prepeares connection to the dmxServer
			self.socket = sc.socket(sc.AF_INET,sc.SOCK_STREAM)
			self.target = (ip,port)
		except Exception as exc:
			self.log(cFN(),"fatal",f"Could not prepeare connection to server: {exc}")
			self.enable = False

	def connect(self): #Finally connects to the server
		if self.enable:
			self.log(cFN(),"info",f"Trying to connect to server [IP:{self.target[0]} P:{self.target[1]}]")
			try:
				self.socket.connect(self.target)
				self.log(cFN(),"ok","Connected to server")
			except Exception as exc:
				self.log(cFN(),"fatal",f"Could not connect to server: {exc}")
				self.enable = False
		else: self.notAvail(cFN())

	def stopConnection(self,timeout=0.0): #Closes the connection to the server
		if self.enable:
			self.log(cFN(),"warn",f"Closing connection in {timeout}s")
			time.sleep(timeout)
			if not self.aC:
				self.socket.close()
				self.log(cFN(),"ok","Connection to server closed")
			else: self.log(cFN(),"warn","Closing connection aborted")
			self.aC = False
		else:
			self.log(cFN(),"err","Client could not be prepeared proberly, so it can't be stopped")

	def abortClosing(self): #Stops the closing of Server, will only work if a timeout in dmxClient.stopConnection was set
		if self.enable:
			self.aC = True
			self.log(cFN(),"info","Trying to abort connection close...")
			self.log(cFN(),"tip","Note that aborting a connection close only can be performed after timeout in functioncall stopConnection is gone")
		else: self.notAvail(cFN())

	def getResponse(self): #Reads the response from server when a command was send
		if self.enable:
			self.log(cFN(),"info","Waiting for response from server...")
			resp = None
			resp = self.socket.recv(1024).decode("utf-8")
			self.log(cFN(),"ok",f"Got response from server: {resp}")
			return resp
		else: self.notAvail(cFN())

	def sendCommand(self,command:str,expectResponse=True): #Sends the command to the server, and if expectResponse is True, it will return the response, else it will skip that part
		if self.enable:
			self.log(cFN(),"info",f"Sending command to server: '{command}'{', expecting Response' if expectResponse else ''}")
			try:
				self.socket.sendall(command.encode("utf-8"))
				self.log(cFN(),"ok","Command sent correctly")
				if expectResponse: return self.getResponse()
			except Exception as exc:
				self.log(cFN(),"err",f"Could not send command: {exc}")
				if expectResponse: return ("ERR",f"client_err-{'_'.join(str(exc).split())}")
		else: self.notAvail(cFN())
