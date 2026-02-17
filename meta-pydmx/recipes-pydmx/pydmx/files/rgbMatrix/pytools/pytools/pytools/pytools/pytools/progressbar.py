from pytools.string import adjustStrLen
class progressbar:
	def __init__(self,**args):
		"""
		Param steps configures the amount of steps the loading bar should maximal have
		Param text configures the first label of the task
		Param maxsymb configures the maximal lenght of the labeltext
		Param style chooses the style (0,1,2,...) ["==","=>",">>","-","->","|","|>"]
		"""
		self.steps = args["steps"]
		try: self.text = args["text"]
		except KeyError: self.text = "Loading..."
		try: self.maxsymb = args["maxsymb"]
		except KeyError: self.maxsymb = 10
		try: self.style = args["style"]
		except KeyError: self.style = 5
		self.var = 0
	def draw(self):
		styles = ["==","=>",">>","--","->","||","|>"]
		print(f"{adjustStrLen(self.text,self.maxsymb)} [{styles[self.style][0]*self.var+styles[self.style][1]}{' '*(self.steps-self.var)} ]]",end="\r")
	def update(self,**args):
		"""
		You can update: text, style, change (-> add to bar)
		"""
		try: self.text = args["text"]
		except KeyError: pass
		try: self.style = args["style"]
		except KeyError: pass
		try: self.var += int(args["change"])
		except KeyError: pass
		self.draw()
	def exit(self,method):
		"""
		method can be: "clear" to clear the progress bar, "behold" to keep the progress bar
		"""
		if method == "clear": print(adjustStrLen("")+"   "+" "*self.steps)
		elif method == "behold": print("")
		else: raise InvailidArgumentException(f"Could not resolve exit method for progressbar: '{method}'")
