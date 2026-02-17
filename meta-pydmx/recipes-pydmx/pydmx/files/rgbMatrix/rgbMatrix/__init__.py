#predefined variables that are helping to make coding easier
class svars():
	available = True
	repavail = True

#Import stuff
from math import sqrt
from pytools.variables import cFN, FE
from pytools.logger import genLogLine as gLL
from json import load as jsload, dump as jsdump
try:
	from rgbMatrix.rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
	from PIL import ImageDraw,ImageFont
	import PIL
except ImportError as exc:
	svars.available = False
	print("Unable to import important librarys:",exc)
try:
	from tkinter import *
except:
	svars.repavail = False

#class for display with rows=32 columns=64
class matrixDisplay:
	class tools():
		def tplClr(color:tuple):
			return f"[R:{color[0]} G:{color[1]} B:{color[2]}]"

		def tplClrHex(color:tuple):
			r,g,b = str(hex(color[0])),str(hex(color[1])),str(hex(color[2]))
			return f"#{'0'+r[2:] if len(list(r[2:])) == 1 else r[2:]}{'0'+g[2:] if len(list(g[2:])) == 1 else g[2:]}{'0'+b[2:] if len(list(b[2:])) == 1 else b[2:]}"

		def tplPos(pos:tuple):
			return f"[X: {pos[0]} Y:{pos[1]}]"

		def state(src:bool):
			return "enabled" if src else "disabled"

		def strTpl(tpl:tuple):
			_lst = list(str(tpl))
			for i in range(len(_lst)):
				if _lst[i] == "[": _lst[i] = "("
				elif _lst[i] == "]": _lst[i] = ")"
			return ''.join(_lst)
		def imgToJson(imagepath:str,targetpath:str,size=(64,32),ignoreBlackPixel=False):
			img = PIL.Image.open(imagepath)
			img.resize(size)
			jsonfile = {"pixel":[],"data":{}}
			for x in range(size[1]):
				for y in range(size[0]):
					r,g,b = img.getpixel((x,y))[:3]
					if (ignoreBlackPixel and (r,g,b) == (0,0,0)):
						pass
					elif not ignoreBlackPixel or (ignoreBlackPixel and (r,g,b) != (0,0,0)):
						jsonfile["pixel"].append((x,y))
						jsonfile["data"][str((x,y))] = (r,g,b)
			with open(targetpath,"w+") as fle: jsdump(jsonfile,fle)

	def log(self,mth:str,tpe:str,msg:str,errhandling="red",eol="\n"):
		print(gLL(f"{self.masterMod+'/' if self.masterMod != '' else ''}rgbMatrix/matrixDisplay{'/'+mth if mth != '' else ''}",tpe,msg,debug=self.debug,errhandling=errhandling),end=eol)

	def notAvail(self,mth:str):
		self.log(mth,"warn","rgbMatrix is not available due to import errors")

	def __init__(self,rows=32,columns=64,chain_length=1,parallel=1,hardware_mapping="regular",disable_hardware_pulsing=True,brightness=50,masterMod="",debug=False,replaceIfUnavail=True,forceReplace=False):
		"""
		replaceIfUnavail parameter controls wether the display output should be converted to a tkinter window if matrixDisplay
		is not available (p.ex. due to iport errors)
		"""
		self.debug = debug
		self.masterMod = str(masterMod)
		self.rows = rows
		self.columns = columns
		self.chain_length = chain_length
		self.parallel = parallel
		self.hardware_mapping = hardware_mapping
		self.no_hardware_pulsing = disable_hardware_pulsing
		self.brightness = brightness
		if svars.available and forceReplace: svars.available = False
		self.replace = True if (replaceIfUnavail and svars.repavail) or (forceReplace and svars.repavail) else False
		self.current_img = None
		self.current_cnv = None

		if svars.available:
			self.opt = RGBMatrixOptions()
			self.opt.rows = self.rows
			self.opt.cols = self.columns
			self.opt.chain_length = self.chain_length
			self.opt.parallel = self.parallel
			self.opt.hardware_mapping = self.hardware_mapping
			self.opt.disable_hardware_pulsing = self.no_hardware_pulsing
			self.opt.brightness = self.brightness

			self.disp = RGBMatrix(options=self.opt)

			self.cnv = self.disp.CreateFrameCanvas()

			self.log(cFN(),"debug","Initialized RGBMatrix with the following values:")
			self.log(cFN(),"debug",f"rows/columns : {self.rows}/{self.columns}")
			self.log(cFN(),"debug",f"parallel/chain_length : {self.parallel}/{self.chain_length}")
			self.log(cFN(),"debug",f"hardware_mapping/no_hardware_pulsing : {self.hardware_mapping}/{self.no_hardware_pulsing}")
			self.log(cFN(),"debug",f"brightness : {self.brightness}")
		elif self.replace:
			self.dispRepElm = {}

			self.dispRepWin = Tk()
			self.dispRepWin.title(f"{self.rows}x{self.columns} Matrix Represent")
			self.dispRepElm["mfrm"] = Frame(self.dispRepWin,width=5*self.columns,height=5*self.rows,background="#FF0000")
			self.dispRepElm["mfrm"].pack(pady=5,padx=5)

			self.log(cFN(),"debug","Generating pixels in window for representation of matrixDisplay")
			for x in range(self.columns):
				for y in range(self.rows):
					#self.dispRep[(x,y)] = (0,0,0)
					self.dispRepElm[(x,y)] = Frame(self.dispRepElm["mfrm"],width=5,height=5,background="#000000")
					self.dispRepElm[(x,y)].grid(row=y,column=x)
					self.log(cFN(),"debug",f"Generating pixel {self.tools.tplPos((x,y))} for representation window  ",eol="\r")
			self.log(cFN(),"ok","Generated matrix Display representation window                              ")
			self.dispRepWin.update()
		else: self.notAvail(cFN())

	def quit(self):
		if svars.available:
			self.clearDisp()
		elif self.replace:
			try: self.dispRepWin.quit()
			except: pass
			try: self.dispRepWin.destroy()
			except: pass

	def renderDisp(self,no_log=False):
		if svars.available:
			if not no_log: self.log(cFN(),"info","Rendering display...")
			try: self.disp.Update(self.cnv)
			except: self.cnv = self.disp.SwapOnVSync(self.cnv)
		elif self.replace:
			if not no_log: self.log(cFN(),"info","Rendering display...")
			self.dispRepWin.update()
		else: self.notAvail(cFN())

	def setPixel(self,pos=(0,0),color=(255,255,255),directDraw=False,no_log=False):
		if not no_log: self.log(cFN(),"debug",f"Type of color / pos: {type(color)} / {type(pos)}")
		color = tuple(color)
		pos = tuple(pos)
		if svars.available and type(color) == tuple:
			if not no_log: self.log(cFN(),"info",f"Changing color of pixel at {self.tools.tplPos(pos)} to {self.tools.tplClr(color)}, directDraw {self.tools.state(directDraw)}")
			x,y = pos
			r,g,b = color
			try: self.cnv.SetPixel(x,y,r,g,b)
			except Exception as exc:
				self.log(cFN(),"err",f"Failed to change color of one pixel: {exc}")
				return
			if not no_log: self.log(cFN(),"ok","Changed pixelcolor")
			if directDraw: self.renderDisp()
		elif self.replace and type(color) == tuple:
			if not no_log: self.log(cFN(),"info",f"Changing color of pixel at {self.tools.tplPos(pos)} to {self.tools.tplClr(color)}, directDraw {self.tools.state(directDraw)}")
			try: self.dispRepElm[pos].configure(background=self.tools.tplClrHex(color))
			except Exception as exc:
				self.log(cFN(),"err",f"Failed to change color of one pixel: {exc}")
				return
			if not no_log: self.log(cFN(),"ok","Changed pixelcolor")
			if directDraw: self.renderDisp()
		else: self.notAvail(cFN())

	def generateImgFromJson(self,filepath="",unlistedPixelColor=(0,0,0),startAt=(0,0),directDraw=False,ignoreUnlistedPixel=True,ignoreBlackPixel=False):
		if svars.available or self.replace:
			self.log(cFN(),"info","Importing file")
			if filepath == "":
				self.log(cFN(),"err","Filename should not be empty")
				return
			try:
				with open(filepath,"r") as fle: img = jsload(fle)
			except Exception as exc:
				self.log(cFN(),"err",f"Could not load json image file: {exc}")
				return
			self.log(cFN(),"ok","File import done")

			mx = 0
			my = 0

			self.log(cFN(),"info",f"Generating image from path '{filepath}' for matrix display, directDraw {self.tools.state(directDraw)}, ignoreUnlistedPixel {self.tools.state(ignoreUnlistedPixel)}, ignoreBlackPixel {self.tools.state(ignoreBlackPixel)}{'unlistedPixelColor '+self.tools.tplClr(unlistedPixelColor) if not ignoreUnlistedPixel else ''}")
			if ignoreUnlistedPixel:
				for pxl in img["pixel"]:
					if pxl[0] > mx: mx = pxl[0]
					if pxl[1] > my: my = pxl[1]

					self.log(cFN(),"debug",f"Generating pixel {self.tools.tplPos(pxl)}     ",eol="\r")
					try:
						if ignoreBlackPixel and img["data"][self.tools.strTpl(pxl)] == (0,0,0):
							self.log(cFN(),"warn",f"Ignoring pixel at {self.tools.tplPos(pxl)} because function is ignoring black pixel",eol="\r")
						else:
							self.setPixel(pos=(pxl[0]+startAt[0],pxl[1]+startAt[1]),color=img["data"][self.tools.strTpl(pxl)],directDraw=False,no_log=True)
					except Exception as exc:
						self.log(cFN(),"err",f"Failed to change color of pixel at {self.tools.tplPos(pxl)}: {exc}")

			else:
				for x in range(self.columns):
					for y in range(self.rows):
						self.log(cFN(),"debug",f"Generating pixel {self.tools.tplPos((x,y))}     ",eol="\n")
						try:
							self.setPixel(pos=(x+startAt[0],y+startAt[1]),color=img["data"][self.tools.strTpl((x,y))],directDraw=False,no_log=True)
						except KeyError:
							self.setPixel(pos=(x+startAt[0],y+startAt[1]),color=unlistedPixelColor,directDraw=False,no_log=True)
						except Exception as exc:
							self.log(cFN(),"err",f"Failed to change color of pixel at {self.tools.tplPos((x,y))} to {self.tools.tplClr(img['data'][(x,y)])}: {exc}")
			self.log(cFN(),"ok","Generated image")
			if directDraw: self.renderDisp()
		else: self.notAvail(cFN())

	def generateSquare(self,pos1=(0,0),pos2=(0,0),color=(255,255,255),directDraw=False,directDrawLvl=2):
		"""
		only change option directDrawLvl if directDraw is enabled. You can choose 1 if
		you want to see how the square is generated. Choose 2 if you want to get square
		rendered when completely done
		"""
		if svars.available:
			self.log(cFN(),"info",f"Generating Square for display, pos1 {self.tools.tplPos(pos1)} and pos2 {self.tools.tplPos(pos2)} in color {self.tools.tplClr(color)}")
			self.log(cFN(),"debug",f"Distances of coordinates: {self.tools.tplPos((pos1[0]-pos2[0],pos1[1]-pos2[1]))}")
			for x in range(int(sqrt((pos2[0]-pos1[0])**2))):
				for y in range(int(sqrt((pos2[1]-pos1[1])**2))):
					self.setPixel(pos=(int(x),int(y)),color=color,no_log=True,directDraw=True if directDraw and directDrawLvl == 1 else False)
			if directDraw and directDrawLvl == 2: self.renderDisp()
		elif self.replace:
			self.log(cFN(),"info",f"Generating Square for display, pos1 {self.tools.tplPos(pos1)} and pos2 {self.tools.tplPos(pos2)} in color {self.tools.tplClr(color)}")
			self.log(cFN(),"debug",f"Distances of coordinates: {self.tools.tplPos((pos1[0]-pos2[0],pos1[1]-pos2[1]))}")
			for x in range(int(sqrt((pos2[0]-pos1[0])**2))):
				for y in range(int(sqrt((pos2[1]-pos1[1])**2))):
					self.setPixel(pos=(int(x),int(y)),color=color,no_log=True,directDraw=True if directDraw and directDrawLvl == 1 else False)
			if directDraw and directDrawLvl == 2: self.renderDisp()
		else: self.notAvail(cFN())

	def generateLine(self,pos1=(0,0),pos2=(0,0),color=(255,255,255),directDraw=False):
		if svars.available:
			self.log(cFN(),"info",f"Generating line from {self.tools.tplPos(pos1)} to {self.tools.tplPos(pos2)} with color {self.tools.tplClr(color)}")
			x1,y1 = pos1
			x2,y2 = pos2
			r,g,b = color
			try: graphics.DrawLine(self.cnv, x1,y1,x2,y2,graphics.Color(r,g,b))
			except Exception as exc:
				self.log(cFN(),"err",f"Generating line failed: {exc}")
				return
			self.log(cFN(),"ok","Generated line")
			if directDraw: self.renderDisp()
		else: self.notAvail(cFN())

	def generateImage(self,filepath="",size=(64,32),startAt=(0,0),directDraw=False):
		if svars.available or self.replace:
			if filepath == "":
				self.log(cFN(),"err","Filepath for image can not be empty")
				return
			self.log(cFN(),"info",f"Trying to load image from filepath '{filepath}' with size {self.tools.tplPos(size)}, start position at {self.tools.tplPos(startAt)}, directDraw {self.tools.state(directDraw)}")

			try:
				img = PIL.Image.open(filepath)
				img.resize(size)
			except Exception as exc:
				self.log(cFN(),"err",f"Prepearation of image failed: {exc}")
				return

			try:
				for x in range(img.width):
					for y in range(img.height):
						r,g,b = img.getpixel((x,y))[:3]
						self.setPixel(pos=(x+startAt[0],y+startAt[1]),color=(r,g,b),no_log=True)
			except Exception as exc:
				self.log(cFN(),"err",f"Failed to load image: {exc}")
				return
			self.log(cFN(),"ok","Loaded image")
			if directDraw: self.renderDisp()
		else: self.notAvail(cFN())

	def generateImageFromPIL(self,image,startAt=(0,0),directDraw=False,no_log=False):
		if svars.available or self.replace:
			if not no_log: self.log(cFN(),"info",f"Generating Image from PIL image object with image size of {self.tools.tplPos((image.width,image.height))}, starting at {self.tools.tplPos(startAt)}")
			try:
				for x in range(image.width):
					for y in range(image.height):
						r, g, b = image.getpixel((x,y))[:3]
						self.setPixel(pos=(x+startAt[0],y+startAt[1]), color=(r,g,b),no_log=True)
			except Exception as exc:
				self.log(cFN(),"err",f"Failed to generate image for display: {exc}")
				return
			if not no_log: self.log(cFN(),"ok","Generated image")
			if directDraw: self.renderDisp(no_log=no_log)
		else: self.notAvail(cFN())

	def generateText(self,text="",font="/usr/share/fonts/truetype/freefont/FreeMono.ttf",font_size=24,text_color=(255,255,255),bg_color=(0,0,0),directDraw=False,no_log=False):
		if svars.available or self.replace:
			if not no_log: self.log(cFN(),"info",f"Generating text '{text}' with font '{font}' in font size {font_size} in color {self.tools.tplClr(text_color)} at background color {self.tools.tplClr(bg_color)}, directDraw {self.tools.state(directDraw)}")

			if not no_log: self.log(cFN(),"debug","Loading font")
			try: _font = ImageFont.truetype(font,font_size)
			except Exception as exc:
				self.log(cFN(),"err",f"Could not load font due to the following exception: {exc}")
				return

			if not no_log: self.log(cFN(),"debug","Generating text background")
			try:
				_draw = ImageDraw.Draw(PIL.Image.new("RGB",(self.columns,self.rows),bg_color))
				text_width, text_height = _draw.textbbox((0,0),text,font=_font)[2:4]
				img = PIL.Image.new("RGB", (64,32), bg_color)
				_draw = ImageDraw.Draw(img)
			except Exception as exc:
				self.log(cFN(),"err",f"Failed to generate background of text: {exc}")
				return

			if not no_log: self.log(cFN(),"debug","Generating text")
			try:
				_draw.text(((64-text_width) // 2, (32-text_height) // 2), text, font=_font,fill=text_color)
			except Exception as exc:
				self.log(cFN(),"err",f"Failed to generate text onto background: {exc}")
				return
			if not no_log: self.log(cFN(),"ok","Generated text")
			self.generateImageFromPIL(img,directDraw=directDraw,no_log=True)
		else: self.notAvail(cFN())

	def generateScrollText(self,text="",scrollPos=0,text_color=(255,255,255),bg_color=(0,0,0),font_size=15,font="/usr/share/fonts/truetype/freefont/FreeMono.ttf",directDraw=True):
		if svars.available or self.replace:
			if text == "":
				self.log(cFN(),"err","Text can not be empty")
				return

			self.log(cFN(),"info",f"Generating text '{text}' with color {self.tools.tplClr(text_color)}, directDraw {self.tools.state(directDraw)}, at scrolling position {scrollPos}")

			self.generateText(text="  "*(len(text)-scrollPos)+text+"  "*scrollPos,text_color=text_color,bg_color=bg_color,font_size=font_size,font=font,directDraw=directDraw,no_log=True)
		else: self.notAvail(cFN())

	def clearDisp(self,directDraw=True):
		if svars.available:
			self.log(cFN(),"warn","Clearing display")
			self.cnv.Clear()
			if directDraw: self.renderDisp()
			self.log(cFN(),"ok","Cleared display")
		elif self.replace:
			self.log(cFN(),"warn","Clearing display")
			self.generateSquare(pos1=(0,0),pos2=(self.columns,self.rows),color=(0,0,0))
			if directDraw: self.renderDisp()
			self.log(cFN(),"ok","Cleared display")
		else: self.notAvail(cFN())
