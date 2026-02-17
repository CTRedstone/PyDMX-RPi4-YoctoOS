from json import load as jsload
import time

class digitalFontGen:
	def __init__(self,lineSpace=2,fontFile="fontstyle.json"):
		"""
		digital Font generator
		Arg. Name      | Type | Default          | Description
		---------------+------+------------------+--------------
		lineSpace      | int  | 2                | Amount of new (empty) lines between Lines of generated text
		fontFile       | str  | "fontstyle.json" | path to fontstyle file
		"""

		"""
		Arg. Name      : Type : Default      : Description
		----------------------------------------------------
		sizeMultiplier : int  : 1            : Multiply size of String
		appendNewLine  : bool : True         : Append newline character
		returnType     : str  : "returnList" : Can be "terminal"/"returnString"/"returnList"
		#end of comment

		try: self.sM = args["sizeMultiplier"]
		except KeyError: self.sM = 1

		try: self.NL = args["appendNewLine"]
		except KeyError: self.NL = True

		try: self.rT = args["returnType"]
		except KeyError: self.rT = "returnList"
		"""

		self.lineSpace = lineSpace
		self.fontFile = fontFile

		self.lines = []
		self.generated = []

	def newLine(self,*text):
		self.lines.append(' '.join(text))

	def resetLines(self): self.lines = []

	def appendToLine(self,line:int,text:str):
		try: self.lines[line] = self.lines[line] + text
		except IndexError: raise IndexError("Unknown linenumber in digitalFontGen for appendToLine: " + str(line))

	def changeLine(self,line:int,text:str):
		try: self.lines[line] = text
		except IndexError: raise IndexError("Unknown linenumber in digitalFontGen for changeLine: " + str(line))

	def generate(self,*colors):
		self.generated = [''.join(colors)]

		with open(self.fontFile,"r") as stylefle: style = jsload(stylefle)["digitFont"]

		for elm1 in self.lines:
			for i in range (7):
				for elm2 in list(elm1):
					try: self.generated.append(''.join(style[elm2.upper()][i])+"  ")
					except KeyError as exc: print(f"Character '{exc}' is not signed up yet")
				self.generated.append("\n")
			self.generated.append("\n"*self.lineSpace)
		self.generated.append("\033[0m")

	def _return(self,type:str):
		"""
		allowed types: "terminal"/"returnList"
		"""

		if type.lower() == "terminal":
			print(''.join(self.generated))
		elif type == "returnList":
			return self.generated

	class reconfigure():
		def sizeMultiplier(self,dest:int): self.sM = dest
		def appendNewLine(self,dest:bool): self.NL = dest
		def returnType(self,dest:str): self.rT = dest
		def resetLines(self): self.lines = []

class pixelFontGen:
	def __init__(self,lineSpace=2,fontFile="fontstyle.json"):
		"""
		Arg. Name      | Type | Default         | Description
		---------------+------+-----------------+--------------
		lineSpace      | int  | 2               | Amount of new (empty) lines between different lines of generated font
		fontFile       | str  | "fontfile.json" | path to fontstyle file
		"""

		self.lineSpace = lineSpace
		self.fontFile = fontFile

		self.lines = []
		self.generated = []

	def countdown(self,_time):
		for i in range (_time):
			self.resetLines()
			for e in range (4): self.newLine(" ")
			self.newLine("WAITING...")
			self.newLine(str(_time-i)+"S LEFT")
			self.generate()
			self._return("terminal")
			time.sleep(0.9995)
		self.resetLines()
		for i in range (4): self.newLine(" ")
		self.newLine("DONE...")
		self.newLine("0S LEFT")
		self.generate()
		self._return("terminal")
		self.resetLines()

	def _return(self,type:str):
		"""
		allowed types: "terminal"/"returnList"
		"""

		if type.lower() == "terminal":
			print(''.join(self.generated))
		elif type == "returnList":
			return self.generated

	def newLine(self,*text):
		self.lines.append(' '.join(text))

	def resetLines(self): self.lines = []

	def appendToLine(self,line:int,*text):
		try: self.lines[line] = self.lines[line] + ' '.join(text)
		except IndexError: raise IndexError("Invailid linenumber in pixelFontGen to append text: " + str(line))

	def changeLine(self,line:int,*text):
		try: self.lines[line] = ' '.join(text)
		except IndexError: raise IndexError("Invailid linenumber in pixelFontGen to change text: " + str(line))

	def generate(self,*colors):
		self.generated = [''.join(colors)]

		with open(self.fontFile,"r") as stylefle: style = jsload(stylefle)["pixelFont"] #recommendent character: "█"

		for elm1 in self.lines:
			for i in range (7):
				for elm2 in list(elm1):
					try: self.generated.append(''.join(style[elm2][i]) + "  ")
					except KeyError as exc: print(f"Character '{exc}' is not signed up yet")
				self.generated.append("\n")
			self.generated.append("\n"*self.lineSpace)
		self.generated.append("\033[0m")
