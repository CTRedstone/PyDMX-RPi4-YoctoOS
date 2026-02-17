def rlen(lst:list) -> int:
	"""
	Returns the right lenght of a list, counted up from 0
	"""
	return len(lst) - 1

def striplines(lst:list) -> list:
	"""
	Removes special characters (like Tabs or newlines) from every item
	"""
	for elm in lst:
		for char in list(elm):
			if char == "\n" or char == "\t": char = ""
	return lst

def remChar(lst:list,rem:str) -> list:
	"""
	Removes in rem specivied character from all items in list
	"""
	for elm in lst:
		for char in list(elm):
			if char == rem: char == ""
	return lst
