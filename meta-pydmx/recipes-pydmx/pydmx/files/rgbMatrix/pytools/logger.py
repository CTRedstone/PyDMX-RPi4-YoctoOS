from string import *
from variables import FE

def genLogLine(prc:str,tpe:str,msg:str,debug=True,errhandling="yellow"):
	tpe = tpe.lower()
	color = FE["cyan"] if tpe in ("inf","info") else FE["blue"] if tpe == "debug" and debug == True else FE["green"] if tpe in ("ok","okay","done") else FE["yellow"] if tpe in ("warn","warning") or (errhandling == "yellow" and tpe in ("err","error")) else FE["red"] if tpe == "fatal" or (errhandling == "red" and tpe in ("warn","warning")) else ""
	if debug or tpe != "debug": return f"{color}[{prc}] [{tpe.upper()}] {msg}{FE['reset']}"
	else: return "\r"

def logfile(prcnme:str,msg:str,**args):
	"""
	Use argument colors if you want to have a colored log, do this like in pytools.string.format
	"""
	with open(".log","a") as fle: fle.write(format(f"[{prcnme}] {msg}\n",**args))

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
