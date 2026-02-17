from pytools.variables import FE
def format(*string,**args) -> str:
	"""
	Use param "colors" to define where which color/effect should be applied: reset, bold, darker, curved, underlined, clrinvert, gray, red, green, yellow, purple, cyan, blue
	Do this the following way: {<int before which char it should be inserted>:"name"}
	"""
	try: _colors = args["colors"]
	except KeyError: _colors = {0:"reset"}
	_lstring = list(string)
	for i in range (len(_lstring)):
		try:
			_lstring[i] = FE[_colors[i]] + _lstring[i]
		except KeyError: pass
	return ''.join(_lstring)

def printf(*string,**args):
	"""
	Usage of param "colors" like in the format function, use param pargs as dictonary with all print parameters
	"""
	try: print(format(' '.join(string),**args),**args["pargs"])
	except: print(' '.join(string))

def inputf(*string,**args):
	"""
	Usage of param "colors" like in the format function
	"""
	try: return input(format(' '.join(string),**args))
	except: return input(' '.join(string))

def matchPattern(string:str,pattern:str) -> bool:
	"""
	Looks if the string matches a pattern. The pattern has to be string to - all characters that are allowed are included in that string without spaces etc.j
	"""
	for elm in list(string):
		if elm not in list(pattern): return False
	return True

def includeChar(string:str,char:str) -> tuple:
	"""
	Checks if one character (char) is in the string and returns a tuple of: (<bool if the character is in the string or not>,<list of all indexes of character in string>
	"""
	_return0 = False
	_return1 = []
	for i in range (len(list(string))):
		elm = list(string)[i]
		if elm == char: _return0 = True
		if elm == char: _return1.append(i)
	return (_return0,_return1)

def rem0b(string:str) -> str:
	"""
	Input should be a binary string (like "0b10011")
	"""
	_return = []
	for i in range (len(list(string))-2):
		_return.append(list(string)[i+2])
	return ''.join(_return)

def adjustStrLen(string:str,mlen:int) -> str:
	if len(string) > mlen: return string[:mlen]
	elif len(string) < mlen: return string.ljust(mlen)
	else: return string
