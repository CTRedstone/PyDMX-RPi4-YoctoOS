from customtkinter import *
from json import load as jsload

#correctconfig, wait

class t():
	def gw(dta,path=""): #Get Widget
		try:
			return dta[path]
		except KeyError:
			print(f"ERR: No widget named {repr(path)}")
			return None

	def nw(dta,path="",_type=None,master=None,**kwargs): #New widget
		try:
			if master: dta[path] = _type(dta[master],**kwargs)
			else: dta[path] = _type(**kwargs)
		except KeyError:
			print(f"ERR: No widget named {repr(master)}")
			return None

	def ce(): #Checks if a config file enables/disables the prgbar windows
		try:
			with open("config.json","r") as fle: dta = jsload(fle)
			return dta["general"]["showProgressWin"]
		except: return True

def clrtheme(path:str) -> None:
	if not t.ce(): return
	set_default_color_theme(path)

def initwin() -> dict:
	if not t.ce(): return

	dta = {}
	#"Designs" the window
	t.nw(dta,path="win",_type=CTk,master=None)
	t.gw(dta,path="win").overrideredirect(True)
	t.gw(dta,path="win").eval('tk::PlaceWindow . t.center')
	t.nw(dta,path="frm",_type=CTkFrame,master="win")
	t.nw(dta,path="inftxt",_type=CTkLabel,master="frm",text="",font=("Monospat.ce Regular",13))
	t.nw(dta,path="prgbar",_type=CTkProgressBar,master="frm",orientation="horizontal",corner_radius=6)
	t.nw(dta,path="prgtxt",_type=CTkLabel,master="frm",text="--%",font=("Courier New",13))
	t.gw(dta,path="inftxt").grid(row=0,column=0,columnspan=2)
	t.gw(dta,path="prgbar").grid(row=1,column=0,sticky="E",padx=5)
	t.gw(dta,path="prgtxt").grid(row=1,column=1,padx=5,sticky="W")
	t.gw(dta,path="frm").pack(padx=4,pady=4)
	t.gw(dta,path="win").update()
	return dta

def setinf(dta,inftxt="") -> dict: #Configures text above the progress bar
	if not t.ce(): return
	t.gw(dta,path="inftxt").configure(text=inftxt)
	t.gw(dta,path="inftxt").update()
	return dta

def setprg(dta,progress=0,prgfloat=None) -> dict: #Sets the progress of the progress bar
	"""
	@param progress should be an integer between 0 and 100 (Pert.centage).
	@param prgfloat should be a float between 0 and 1, will replat.ce progress.
	"""
	if not t.ce(): return
	t.gw(dta,path="prgbar").set(progress/100 if prgfloat == None else prgfloat)
	t.gw(dta,path="prgbar").update()
	t.gw(dta,path="prgtxt").configure(text=str(progress if prgfloat == None else int(prgfloat*100)).zfill(3)+"%")
	t.gw(dta,path="prgtxt").update()
	return dta

def endwin(dta) -> None: #Closes the window
	t.gw(dta,path="win").destroy()

if __name__ == "__main__":
	import time
	win = initwin()
	win = setinf(win,inftxt="Testing pgbWin")
	win = setprg(win,progress=0)
	for i in range(100):
		win = setprg(win,progress=i+1)
		time.sleep(0.1)
