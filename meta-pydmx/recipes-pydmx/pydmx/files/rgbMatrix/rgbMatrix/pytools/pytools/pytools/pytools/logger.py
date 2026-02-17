from string import *

def logfile(prcnme:str,msg:str,**args):
	"""
	Use argument colors if you want to have a colored log, do this like in pytools.string.format
	"""
	with open(".log","a") as fle: fle.write(format(f"[{prcnme}] {msg}",**args))

def clearLogFile():
	with open(".log","w+") as fle: fle.write("")

def logTerminal(prcnme:str,msg:str,**args):
	"""
	Use argument colors if you want to have a colored log, do this like in pytools.string.format
	"""
	printf(f"[{prcnme}] {msg}",**args)

def readLogFile(mode:str):
	"""
	Mode "return" or "print"
	"""
	_return = []
	with open(".log","r") as fle:
		for line in fle.readlines(): _return.append(line)
	if mode == "print":
		for line in _return: print(line)
	elif mode == "return": return _return
	else: raise InvailidArgumentException(f"Unknown option for mode of readLogFile: '{mode}'")
