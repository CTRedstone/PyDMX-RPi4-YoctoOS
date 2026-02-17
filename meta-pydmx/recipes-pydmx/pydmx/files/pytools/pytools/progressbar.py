def gf(data,key): return data[key]
class progressbar:
	def __init__(self,**args):
		"""
		argument : means
		msteps   : means maximum lenght of progressbar
		left     : string character when the percentage of number not reached yet
		done     : string character when the percentage of number reached already
		msg      : msg to show in front of progress bar
		disable  : disable any logging

		Recommendent combinations of left and done:
		left : done
		..   : ##
		--   : **
		--   : ++
		     : >>
		.    : #
		-    : *
		-    : +
		     : >
		     : |
		"""
		self.msteps = gf(args,"msteps")
		self.leftchar = gf(args,"left")
		self.donechar = gf(args,"done")
		try: self.msg = gf(args,"msg")
		except KeyError: self.msg = "PROCESS"
		try: self.disable = args["disable"]
		except KeyError: self.disable = False
		self.at = 0
		self.lastlog = ""
		self.laststr = ""
	def reset(self):
		self.at = 0
		self.lastlog = ""
		self.laststr = ""
	def step(self,logmsg:str,amt:int,*args):
		"""fourth argument can be used with boolean to suppress prompt at beginning of log messages"""
		self.at = self.at + amt
		entstr = f"{self.msg} {self.at}/{self.msteps} [{self.donechar*self.at}{self.leftchar*(self.msteps-self.at)}]"
		if self.disable == False and logmsg != "": print(f"> {logmsg}{' '*(len(list(entstr))-len(list(logmsg)))}\n{self.msg} {str(self.at).zfill(len(str(self.msteps)))}/{self.msteps} [{self.donechar*self.at}{self.leftchar*(self.msteps-self.at)}]",end="\r")
		elif self.disable == False: print(f"{self.msg} {str(self.at).zfill(len(str(self.msteps)))}/{self.msteps} [{self.donechar*self.at}{self.leftchar*(self.msteps-self.at)}]",end="\r")
		self.lastlog = logmsg
		self.laststr = entstr
	def setstr(self,msg:str):
		self.laststr = f"{self.msg} {str(self.at).zfill(len(str(self.msteps)))}/{self.msteps} [{msg+self.leftchar*self.msteps}]"
		if self.disable == False: print(self.laststr,end="\r")
	def finish(self):
		if self.disable == False: print(self.laststr)
