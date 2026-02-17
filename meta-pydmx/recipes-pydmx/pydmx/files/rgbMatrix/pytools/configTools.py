from json import load as jsload, dump as jsdump

def load(filepath:str):
	with open(filepath,"r") as fle: _return = jsload(fle)
	return _return

def save(filepath:str,config):
	with open(filepath,"w+") as fle: jsdump(config,fle)
