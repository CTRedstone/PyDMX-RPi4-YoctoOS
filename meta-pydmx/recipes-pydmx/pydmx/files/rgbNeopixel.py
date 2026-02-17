class predef_values():
	_boardAvailable = True

try:
	import board
	import neopixel #install through 'pip install rpi_ws281x adafruit-circuitpython-neopixel'
except:
	predef_values._boardAvailable = False
from pytools.logger import logfile
from pytools.variables import FE
from PIL import Image, ImageDraw, ImageFont

class disp64x32:
	class tools():
		def lerp_color(color1,color2,t):
			return tuple(int(color1[i] + (color2[i] - color1[i]) * t) for i in range(3))

	def tplRGB(self,color:tuple[int]) -> str:
		return f"[R:{color[0]} G:{color[1]} B:{color[2]}]"

	def load_image(self,filepath:str,size=(64,32)):
		image = Image.open(filepath)
		image = image.resize(size)
		return image

	def log(self,tpe:str,msg:str,**prtargs):
		color = FE["cyan"] if tpe in ("inf","info") else FE["blue"] if tpe == "debug" else FE["green"] if tpe in ("done","ok","okay") else FE["yellow"] if tpe == "warn" else FE["red"] if tpe == "err" else ""
		if self.debug == True or (self.debug == False and tpe != "debug"):
			logstr = f"[{str(self.masterModule)+'/' if self.masterModule != None else ''}RGBmatrix64x32] [{tpe.upper()}] {msg}"
			print(color+logstr+FE["reset"],**prtargs)
			logfile(f"{str(self.masterModule)+'/' if self.masterModule != None else ''}RGBmatrix64x32",f"[{tpe.upper()}] {msg}")

	def notActive(self,action:str):
		self.log("warn",f"Skipping display action {action} due to import errors while importing important packages")

	def __init__(self,**kwargs):
		"""
		Argument  | Type | Description
		----------+------+-------------------
		brightness| float| Describes how bright the Display should be
		boardPin  | str  | Name of the pin in the python board library
		masterMod | str  | Name of master module
		debug     | bool | Show debug log messages too
		"""

		self.available = predef_values._boardAvailable
		try: self.boardpin = kwargs["boardPin"]
		except KeyError: self.boardpin = "D18"
		try: self.masterModule = kwargs["masterMod"]
		except KeyError: self.masterModule = None
		try: self.debug = kwargs["debug"]
		except KeyError: self.debug = False

		if self.available:
			self.log("info","Initializing...")
			self.pixelPin = eval("board."+str(self.boardpin))
			self.log("debug","Set pixelpin to board."+str(self.boardpin))
			self.pixelNum = 2048
			self.log("debug",f"Set total number of pixels to {self.pixelNum} (64x32)")

			try: self.brightness = kwargs["brightness"]
			except KeyError: self.brightness = 0.4
			self.log("info",f"Set brightness level of display to {self.brightness}")

			self.log("info","Initializing Display...")
			self.disp = neopixel.NeoPixel(self.pixelPin,self.pixelNum,brightness=self.brightness,auto_write=False)
			self.log("ok","Set up display successfully")

			self.pixels = []
			for i in range(self.pixelNum): self.pixels.append((0,0,0))

			self.log("done","Initializing done...")
		else:
			self.log("warn","Seems like something failed while importing librarys for board control, skipping actions. This can happen if you either don't have the librarys installed or you are not on a device that supports these librarys.")

	def clearPixel(self):
		if self.available:
			self.log("info","Clearing pixel...")
			self.disp.fill((0,0,0))
			for i in range(self.pixelNum): self.pixels[i] = (0,0,0)
			self.log("done",f"Set all pixel back to {self.tplRGB((0,0,0))}")
		else: self.notActive("clearPixel")

	def setPixel(self,x:int,y:int,color:tuple[int],suppressLog=False,**logargs):
		if self.available:
			index = (y*64) + x
			try:
				self.disp[index] = color
				self.pixels[index] = color
				if not suppressLog: self.log("ok",f"Set color of pixel at [X:{x} Y:{y}] to {self.tplRGB(color)}",**logargs)
			except IndexError: self.log("err",f"Could not find Pixel on display: {x}x{y}")
		else: self.notActive("setPixel")

	def fillAllPixel(self,color:tuple[int]):
		if self.available:
			self.log("info",f"Filling all pixels with color {self.tplRGB(color)}")
			self.disp.fill(color)
			for i in range(self.pixelNum): self.pixels[i] = color
			self.log("ok","Task done")
		else: self.notActive("fillAllPixel")

	def displayImage(self,image,imgSize=(64,32),startAt=(0,0)):
		if self.available:
			for x in range(imgSize[0]):
				for y in range(imgSize[1]):
					r,g,b = image.getpixel((x+startAt[0],y+startAt[1]))
					self.setPixel(x+startAt[0],y+startAt[1],(r,g,b),suppressLog=True)
					if (x,y) == (63,31): eol = "\n"
					else: eol = "\r"
					self.log("info",f"Set pixel at [X:{x+startAt[0]} Y:{y+startAt[1]}] to {self.tplRGB((r,g,b))}       ",end=eol)
			self.log("done","Successfully drew Image")
		else: self.notActive("displayImage")

	def displayText(self,text:str,color:tuple[int],background:tuple[int],size=(64,32),font_size=11,font="/usr/share/fonts/truetype/freefont/FreeMono.ttf",startAt=(0,0)):
		if self.available:
			self.log("info","Generating background of Text")
			image = Image.new("RGB",size,background)
			draw = ImageDraw.Draw(image)
			font = ImageFont.truetype(font,font_size)
			self.log("done","Prepeared text background")

			self.log("info",f"Generating text onto Background ('{text}') with font size {font_size}")
			draw.textbbox(startAt,text,font=font, fill=color)[2:4]

			self.displayImage(image,imgSize=size,startAt=startAt)
			self.log("done","Drew text successfully")
		else: self.notActive("displayText")

	def displayGradientText(self,text:str,startcolor:tuple[int],endcolor:tuple[int],background:tuple[int],size=(64,32),font_size=11,font="/usr/share/fonts/truetype/freefont/FreeMono.ttf",startAt=(0,0)):
		if self.available:
			self.log("info","Generating background of gradient text")
			image = Image.new("RGB",size,background)
			draw = ImageDraw.Draw(image)
			font = ImageFont.truetype(font,font_size)
			self.log("done","Prepeared text background")

			self.log("info",f"Drawing text '{text}' in font size {font_size}...")

			self.log("debug",f"Generating color gradient, start color {self.tplRGB(startcolor)}, end color {self.tplRGB(endcolor)}")
			text_width,text_height = draw.textbbox((0,0),text,font=font)[2:4]
			gradient = [self.tools.lerp_color(startcolor,endcolor,i/text_width) for i in range(text_width)]
			self.log("debug","Generated color gradient")

			self.log("debug","Drawing text to background...")
			for i,char in enumerate(text):
				char_x = i*(text_width//len(text))
				color = gradient[char_x]
				draw.text((char_x,0), char, font=font, fill=color)
			self.log("debug","Drew text to background")

			self.displayImage(image,imgSize=size,startAt=startAt)

			self.log("done","Drew text successfully")
		else: self.notActive("displayGradientText")

	def renderPixel(self):
		if self.available:
			self.log("info","Rendering pixel...")
			self.disp.show()
			self.log("ok","Rendereing pixel done...")
		else: self.notActive("renderPixel")
