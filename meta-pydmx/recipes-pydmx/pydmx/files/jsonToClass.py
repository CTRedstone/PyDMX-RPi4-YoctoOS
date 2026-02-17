from random import randint
from copy import deepcopy as dc

class classes(): ...

def rclassname():
	lst = []
	for i in range(1024):
		lst.append(str(randint(0,9)))
	return "_" + ''.join(lst)

def typecheck(_rc,path:list,jsonelm):
	#if type(json) != dict: raise TypeError(f"Invailid type for typecheck: {type(json)}")
	global rc,jelm
	rc = dc(_rc)
	jelm = dc(jsonelm)
	if type(jsonelm) in (str,int,float,bool):
		exec(f"{'.'.join(path)} = jelm")
	elif type(jsonelm) == list:
		lstpath = dc(path)
		lstpath.append(f"listitems")
		rcn = rclassname()
		exec(f"{'.'.join(lstpath)} = jsonelm")
		for i in range(len(jsonelm)):
			npath = dc(path)
			npath.append(f"listitem{i}")
			rcn = rclassname()
			exec(f"from copy import deepcopy as dc\nclass {rcn}(): ...\n{'.'.join(npath)} = dc({rcn})")
			typecheck(_rc,npath,jsonelm[i])
	elif type(jsonelm) == dict:
		for key in list(jsonelm.keys()):
			npath = dc(path)
			npath.append(key if type(key) == str and key.upper() != key.lower() else "_"+key if type(key) == str and key.upper() == key.lower() else "num"+str(key))
			rcn = rclassname()
			exec(f"from copy import deepcopy as dc\nclass {rcn}(): ...\n{'.'.join(npath)} = dc({rcn})")
			typecheck(_rc,npath,jsonelm[key])

def convert(rootclass,json):
	if type(json) == list: raise TypeError("Can not convert roottype list to classes")
	elif type(json) != dict: raise TypeError(f"Can not convert roottype {type(dict)} to classes")

	typecheck(rootclass,["rc"],json)
