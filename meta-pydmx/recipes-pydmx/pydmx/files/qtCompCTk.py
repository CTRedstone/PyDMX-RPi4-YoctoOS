"""
Ai Request:
Please give me a short explanation of the python3 <WIDGETNAME> widget with it's most important parameters, methods and styling arguments
"""

#CTk compatible PyQT (Arguments)
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QStyle, QCheckBox, QSlider, QTextEdit, QComboBox
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtCore import Qt, QObject, QEvent
import tkinter as tk
from copy import deepcopy as dc
from datetime import datetime
from random import randint
import json

with open(".qtCompCTk.log","w+") as fle: fle.write("") #Clear log file

def log(*txt,tpe=None,src=None):
    """
    Logs entered txt into the file .qtCompCTk.log with a timestamp
    """
    spc1 = (42-len(f"[qtCompCTk/{src}"))*" "
    spc2 = (7-len(f"{tpe.upper() if tpe in ('error','info','debug','fatal','warn','okay','done') else 'unknown'}"))*" "
    with open(".qtCompCTk.log","a") as fle: fle.write(f"[{datetime.now()} qtCompCTk/{src}{spc1}] {tpe.upper()}{spc2}: {''.join(txt)}\n")

def getScreenSize():
    size = QGuiApplication.primaryScreen().size()
    return {"width":size.width(),"height":size.height()}

class qtCompCTkErrs():
    class orientationError(Exception): ...
    class layoutError(Exception): ...
    class existanceError(Exception): ...

class qtCompCTkHelps():
    _theme_data = {}

    class events():
        evnames = { #Mappings for Qt Event types
            "mouse-single": QEvent.Type.MouseButtonPress,
            "mouse-double": QEvent.Type.MouseButtonDblClick,
            "mouse-move": QEvent.Type.MouseMove,
            "keypress": QEvent.Type.KeyPress
        }

        noargevnmes = ( #Events, which don't have an extra argument (for qtCompCTkHelps.KeyFilter.eventFilter)
            "mouse-single",
            "mouse-double",
            "mouse-move"
        )

        QEVENT_NAMES = {v: k for k, v in QEvent.__dict__.items() if isinstance(v, QEvent.Type)} #QtEventNames for qtCompCTkHelps.qtKeytoKey

    class kg():
        generated = []
        def genkey(): #Generates random strings with length of 10 numbers
            key = ""
            for i in range(10):
                key += str(randint(0,9))
            while key in qtCompCTkHelps.kg.generated:
                key = ""
                for i in range(10):
                    key += str(randint(0,9))
            qtCompCTkHelps.kg.generated.append(dc(key))
            return dc(key)

    def keyToQtkey(id:str): #A simple keyname will be converted into the corresponding Qt.Key Class (for qtCompCTkHelps.KeyFilter.eventFilter)
        return eval(f"Qt.Key.Key_{id[1:-1] if id[0] == '<' and id[-1:] == '>' else id}")

    def qtKeyToKey(qtkey:Qt.Key): #Will return the name of the Qt.Key class 
        return qtkey.__name__ if len(qtkey.__name__) == 1 else f"<{qtkey.__name__}>"

    class KeyFilter(QObject):
        def eventFilter(self, obj, event): #Will be called on every event in the Window/on widgets, reads properties of Widgets for reaction
            try:
                if event.type() == qtCompCTkHelps.events.evnames[obj.cmdtrigger[0]] and obj.cmdtrigger[0] in qtCompCTkHelps.events.noargevnmes:
                    obj.cmd(*obj.cmdargs,**obj.cmdkwargs)
                elif (event.type() == qtCompCTkHelps.events.evnames[obj.cmdtrigger[0]] and obj.cmdtrigger[0] == "keypress") and event.key() == qtCompCTkHelps.keyToQtkey(obj.cmdtrigger[1]):
                    obj.cmd(*obj.cmdargs,**obj.cmdkwargs)
                else:
                    #log(f"No command matching requirements found",src="eventFilter",tpe="warn")
                    return False
                log(f"Event of type {repr(event.type())} -> {repr(qtCompCTkHelps.events.QEVENT_NAMES.get(event.type(), 'Unknown('+str(event.type())+')'))} got triggered in {repr(obj)}, cmdtrigger requirements of widget are {repr(obj.cmdtrigger)}",src=f"{obj.__name__}/evFlt",tpe="info")
                log(f"Corresponding command ({repr(obj.cmd)}) executed",src=f"{obj.__name__}/evFlt",tpe="okay")
            except: pass
            return False

class ThemeManager:
    _theme_data = {}

    @classmethod
    def set_color_theme(self,theme_file:str): #Loads a theme file globaly
        try:
            with open(theme_file,"r") as f:
                self._theme_data = json.load(f)
                print(f"[Theme] Loaded theme from {theme_file}")
        except Exception as exc:
            print(f"[Theme] Failed to load theme: {e}")
            self._theme_data = {}
        qtCompCTkHelps._theme_data = self._theme_data

    @classmethod
    def load(self, cls, theme_file: str): #Loads a theme file
        try:
            with open(theme_file, "r") as f:
                cls._theme_data = json.load(f)
                print(f"[Theme] Loaded theme from {theme_file}")
        except Exception as e:
            print(f"[Theme] Failed to load theme: {e}")
            cls._theme_data = {}

    @classmethod
    def get(self, cls, key: str, category="color"): #Reads the value of a style variable from a widget
        return cls._theme_data.get(category, {}).get(key)

    @classmethod
    def resolve(self, cls, user_value, theme_key, category="color"): #Looks if a value is already in the theme and if the user_value is not empty. If it is, the default value will be used
        return user_value if user_value is not None else cls.get(theme_key, category)
        
    @classmethod
    def set(self, cls, style_values=[]): #Reloads a widget's style from values named in style_values
        bfr = {}
        for elm in list(style_values.keys()): #Read the values of the style variables
            bfr[elm] = eval(f"str(cls.{style_values[dc(elm)]})" + str("+'px'" if elm in ("border_radius") else ""))
            if bfr[elm] in (None,""): del bfr[elm]
        style_str = "; ".join(f"{k}: {v}" for k, v in bfr.items() if v) #Converts the styles into a string
        try: cls.setStyleSheet(style_str)
        except: pass

class App(QApplication):
    def __init__(self):
        super().__init__([])

class CTk(QMainWindow):
    childs = []
    geomanage = None
    layout = None
    updated = False
    evfilter = qtCompCTkHelps.KeyFilter
    stylevars = {"bg_color":"bg_color","color":"text_color"}

    def __getattr__(self,name):
        def wrong_attribute(*args,**kwargs):
            print(f"\033[33m\033[1mUnknown function of {self.__name__} called: '{name}'\033[0m")
        return wrong_attribute

    def __init__(self,*args,application=None,centered=True,bg_color="",text_color=""):
        super().__init__(*args)

        #Init vars
        self.__name__ = "QMainWindow-" + qtCompCTkHelps.kg.genkey()
        if centered: self.center()
        self.application = application

        #Def central widget
        self.cw = QWidget()
        self.setCentralWidget(self.cw)

        #Init properties
        self.bg_color = bg_color
        self.text_color = text_color
        _theme_data = dc(qtCompCTkHelps._theme_data)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    def removeWidget(self,widget):
        try:
            """
            try: print(f"TRYING TO REMOVE {repr(widget.__name__)} FROM {repr(self.__name__)}")
            except: pass
            """
            if self.layout != None: self.layout.removeWidget(widget)
            widget.deleteLater()
            #del self.childs[self.childs.index(widget)]
        except: pass
    
    def readdWidget(self,widget):
        if widget not in self.childs: raise qtCompCTkErrs.existanceError(f"Widget {repr(widget.__name__)} is not already a child of widget {repr(self.__name__)}")
        widget._add_to_master()
    
    def mainloop(self):
        self.cw.setLayout(self.layout)
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
        self.show()
        if self.application != None: self.application.exec_()
    
    def update(self):
        if not self.updated: self.cw.setLayout(self.layout)
    
    def title(self,*args):
        self.setWindowTitle(*args)

    def geometry(self,*args):
        try:
            if "+" not in args[0]:
                _args = list(args[0].split("x"))
                for i in range(len(_args)): _args[i] = int(_args[i])
                self.resize(*_args)
            else: self.setGeometry(*args)
        except: pass
    
    def center(self):
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())
    
    def destroy(self):
        log("Ending window (destroying)",src=self.__name__+"/destroy",tpe="warn")
        super().destroy()
        log("Window destroyed",src=self.__name__+"/destroy",tpe="okay")

class CTkFrame(QWidget):
    childs = []
    geomanage = None
    layout = None
    cmdtrigger = None
    cmd = None
    cmdargs = ()
    cmdkwargs = {}
    stylevars = {}

    def __init__(self,master:QWidget,corner_radius=0,command=type,cmdargs=(),cmdkwargs={},**kwargs):
        super().__init__()

        #Init vars
        self.__name__ = "QWidget-" + qtCompCTkHelps.kg.genkey()
        self.master = master
        self.master.childs.append(self)
        self.cmd = command
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        self.geomanage_args = []

        #Init properties
        self.evflt = qtCompCTkHelps.KeyFilter()
        self.installEventFilter(self.evflt) #Starts the event manager for commands etc.
        _theme_data = dc(qtCompCTkHelps._theme_data)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    #updates Layout if a widget is configured in the layout
    def update(self):
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
    
    #pack/grid will create a new Layout in the master widget if there is none, else it will only add the widget to it
    def pack(self,direction=["v","h"],**kwargs):
        if self.master.geomanage not in (None,"box/pack"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'box/pack' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            if direction not in ("v","h"): raise qtCompCTkErrs.orientationError(f"Invailid orientation {repr(direction)} for pack geometry manager")
            self.master.geomanage = "box/pack"
            self.master.layout = QVBoxLayout() if direction == "v" else QHBoxLayout() if direction == "h" else None
        self.master.layout.addWidget(self)
    
    def grid(self,row=0,column=0,rowspan=1,columnspan=1,**kwargs):
        if self.master.geomanage not in (None,"grid"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'grid' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            self.master.geomanage = "grid"
            self.master.layout = QGridLayout()
        self.geomanage_args = [row,column,rowspan,columnspan]
        self.master.layout.addWidget(self, row, column, rowspan, columnspan)

    def _add_to_master(self):
        if self.master.geomanage == "grid":
            self.master.layout.addWidget(self, *self.geomanage_args)
        elif self.master.geomanage == "box/pack":
            self.master.layout.addWidget(self)
        else: raise qtCompCTkErrs.layoutError(f"Unknown master geomanager: {repr(self.master.geomanage)}")
    
    #bind bindes a command to a specific event onto the element
    def bind(self,act:str,cmd,evtype="keypress",cmdargs=(),cmdkwargs={}):
        self.cmd = cmd
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        #def bind(self,evtype:["mouse-single","mouse-double","mouse-move","keypress"],act:str,cmd,cmdargs=(),cmdkwargs={}):
        
        if "<Button-" in act: evtype = "mouse-single"

        if evtype != "keypress":
            self.cmdtrigger = (evtype)
        else:
            self.cmdtrigger = (evtype,act)
        
        log(f"New command bound to Widget {repr(self.__name__)} with cmdargs {repr(cmdargs)} and kwargs {repr(kwargs)}",src=self.__name__,tpe="debug")
    
    #Configures the value of an existing variable of this widget
    def configure(self,**kwargs):
        for key in list(kwargs.keys()):
            exec(f"self.{key} = {repr(kwargs[key])}",{"self":self})

class CTkScrollableFrame(QWidget):
    childs = []
    geomanage = None
    layout = None
    cmdtrigger = None
    cmd = None
    cmdargs = ()
    cmdkwargs = {}
    stylevars = {}

    def __init__(self,master:QWidget,corner_radius=0,command=type,cmdargs=(),cmdkwargs={},**kwargs):
        super().__init__()

        #Init vars
        self.__name__ = "QWidget-" + qtCompCTkHelps.kg.genkey()
        self.master = master
        self.master.childs.append(self)
        self.cmd = command
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        self.geomanage_args = []

        #Init properties
        self.evflt = qtCompCTkHelps.KeyFilter()
        self.installEventFilter(self.evflt) #Starts the event manager for commands etc.
        _theme_data = dc(qtCompCTkHelps._theme_data)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    #updates Layout if a widget is configured in the layout
    def update(self):
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
    
    #pack/grid will create a new Layout in the master widget if there is none, else it will only add the widget to it
    def pack(self,direction=["v","h"],**kwargs):
        if self.master.geomanage not in (None,"box/pack"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'box/pack' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            if direction not in ("v","h"): raise qtCompCTkErrs.orientationError(f"Invailid orientation {repr(direction)} for pack geometry manager")
            self.master.geomanage = "box/pack"
            self.master.layout = QVBoxLayout() if direction == "v" else QHBoxLayout() if direction == "h" else None
        self.master.layout.addWidget(self)
    
    def grid(self,row=0,column=0,rowspan=1,columnspan=1,**kwargs):
        if self.master.geomanage not in (None,"grid"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'grid' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            self.master.geomanage = "grid"
            self.master.layout = QGridLayout()
        self.geomanage_args = [row,column,rowspan,columnspan]
        self.master.layout.addWidget(self, row, column, rowspan, columnspan)

    def _add_to_master(self):
        if self.master.geomanage == "grid":
            self.master.layout.addWidget(self, *self.geomanage_args)
        elif self.master.geomanage == "box/pack":
            self.master.layout.addWidget(self)
        else: raise qtCompCTkErrs.layoutError(f"Unknown master geomanager: {repr(self.master.geomanage)}")
    
    #bind bindes a command to a specific event onto the element
    def bind(self,act:str,cmd,evtype="keypress",cmdargs=(),cmdkwargs={}):
        self.cmd = cmd
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs

        if "<Button-" in act: evtype = "mouse-single"
        
        if evtype != "keypress":
            self.cmdtrigger = (evtype)
        else:
            self.cmdtrigger = (evtype,act)
        
        log(f"New command bound to Widget {repr(self.__name__)} with cmdargs {repr(cmdargs)} and kwargs {repr(kwargs)}",src=self.__name__,tpe="debug")
    
    #Configures the value of an existing variable of this widget
    def configure(self,**kwargs):
        for key in list(kwargs.keys()):
            exec(f"self.{key} = {repr(kwargs[key])}",{"self":self})

class CTkLabel(QLabel):
    childs = []
    geomanage = None
    layout = None
    cmdtrigger = None
    cmd = None
    cmdargs = ()
    cmdkwargs = {}
    #            Qt Name   | Varname
    stylevars = {"bg_color":"bg_color","color":"text_color"}

    def __init__(self,master:QWidget,text="",bg_color="",text_color="",**kwargs):
        super().__init__()

        #Init vars
        self.__name__ = "QLabel-" + qtCompCTkHelps.kg.genkey()
        self.master = master
        self.master.childs.append(self)
        self.text_color = text_color
        self.bg_color = bg_color
        self.geomanage_args = []

        #Init properties
        self.setText(text)
        self.evflt = qtCompCTkHelps.KeyFilter()
        self.installEventFilter(self.evflt)
        _theme_data = dc(qtCompCTkHelps._theme_data)
        ThemeManager.set(self, style_values=self.stylevars)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    #updates Layout if a widget is configured in the layout
    def update(self):
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
    
    def pack(self,direction=["v","h"],**kwargs):
        if self.master.geomanage not in (None,"box/pack"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'box/pack' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            if direction not in ("v","h"): raise qtCompCTkErrs.orientationError(f"Invailid orientation {repr(direction)} for pack geometry manager")
            self.master.geomanage = "box/pack"
            self.master.layout = QVBoxLayout() if direction == "v" else QHBoxLayout() if direction == "h" else None
        self.master.layout.addWidget(self)
    
    def grid(self,row=0,column=0,rowspan=1,columnspan=1,**kwargs):
        if self.master.geomanage not in (None,"grid"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'grid' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            self.master.geomanage = "grid"
            self.master.layout = QGridLayout()
        self.geomanage_args = [row,column,rowspan,columnspan]
        self.master.layout.addWidget(self, row, column, rowspan, columnspan)

    def _add_to_master(self):
        if self.master.geomanage == "grid":
            self.master.layout.addWidget(self, *self.geomanage_args)
        elif self.master.geomanage == "box/pack":
            self.master.layout.addWidget(self)
        else: raise qtCompCTkErrs.layoutError(f"Unknown master geomanager: {repr(self.master.geomanage)}")
    
    def bind(self,act:str,cmd,evtype="keypress",cmdargs=(),cmdkwargs={}):
        self.cmd = cmd
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        
        if "<Button-" in act: evtype = "mouse-single"
        
        if evtype != "keypress":
            self.cmdtrigger = (evtype)
        else:
            self.cmdtrigger = (evtype,act)
        
    def get(self):
        return self.text()
    
    #Configures the value of an existing variable of this widget
    def configure(self,**kwargs):
        for key in list(kwargs.keys()):
            exec(f"self.{key} = {repr(kwargs[key])}",{"self":self})

class CTkButton(QPushButton):
    childs = []
    geomanage = None
    layout = None
    cmdtrigger = None
    cmd = None
    cmdargs = ()
    cmdkwargs = {}
    stylevars = {"color":"text_color","bg_color":"bg_color"}

    def __init__(self,master:QWidget,text="",fg_color="",text_color="",corner_radius=0,bg_color="",command=type,cmdargs=(),cmdkwargs={},**kwargs):
        super().__init__()

        #Init vars
        self.__name__ = "QPushButton-" + qtCompCTkHelps.kg.genkey()
        self.master = master
        self.master.childs.append(self)
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.clcmd = command
        self.clcmdargs = cmdargs
        self.clcmdkwargs = cmdkwargs
        self.geomanage_args = []

        #Init properties
        self.setText(text)
        self.clicked.connect(lambda:self.clcmd(*self.clcmdargs,**self.clcmdkwargs))
        self.evflt = qtCompCTkHelps.KeyFilter()
        self.installEventFilter(self.evflt)
        _theme_data = dc(qtCompCTkHelps._theme_data)
        ThemeManager.set(self,style_values=self.stylevars)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    #updates Layout if a widget is configured in the layout
    def update(self):
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
    
    def pack(self,direction=["v","h"],**kwargs):
        if self.master.geomanage not in (None,"box/pack"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'box/pack' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            if direction not in ("v","h"): raise qtCompCTkErrs.orientationError(f"Invailid orientation {repr(direction)} for pack geometry manager")
            self.master.geomanage = "box/pack"
            self.master.layout = QVBoxLayout() if direction == "v" else QHBoxLayout() if direction == "h" else None
        self.master.layout.addWidget(self)
    
    def grid(self,row=0,column=0,rowspan=1,columnspan=1,**kwargs):
        if self.master.geomanage not in (None,"grid"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'grid' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            self.master.geomanage = "grid"
            self.master.layout = QGridLayout()
        self.geomanage_args = [row,column,rowspan,columnspan]
        self.master.layout.addWidget(self, row, column, rowspan, columnspan)

    def _add_to_master(self):
        if self.master.geomanage == "grid":
            self.master.layout.addWidget(self, *self.geomanage_args)
        elif self.master.geomanage == "box/pack":
            self.master.layout.addWidget(self)
        else: raise qtCompCTkErrs.layoutError(f"Unknown master geomanager: {repr(self.master.geomanage)}")
    
    def bind(self,act:str,cmd,evtype="keypress",cmdargs=(),cmdkwargs={}):
        self.cmd = cmd
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        
        if "<Button-" in act: evtype = "mouse-single"
        
        if evtype != "keypress":
            self.cmdtrigger = (evtype)
        else:
            self.cmdtrigger = (evtype,act)
    
    #Configures the value of an existing variable of this widget
    def configure(self,**kwargs):
        for key in list(kwargs.keys()):
            exec(f"self.{key} = {repr(kwargs[key])}",{"self":self})

class CTkEntry(QLineEdit):
    childs = []
    geomanage = None
    layout = None
    cmdtrigger = None
    cmd = None
    cmdargs = ()
    cmdkwargs = {}
    stylevars = {"color":"text_color","bg_color":"bg_color"}

    def __init__(self,master:QWidget,text="",placeholder_text="",fg_color="",bg_color="",corner_radius=0,text_color="",**kwargs):
        super().__init__()

        #Init vars
        self.__name__ = "QLineEdit-" + qtCompCTkHelps.kg.genkey()
        self.master = master
        self.master.childs.append(self)
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.geomanage_args = []

        #Init properties
        self.setText(text)
        self.setPlaceholderText(placeholder_text)
        self.evflt = qtCompCTkHelps.KeyFilter()
        self.installEventFilter(self.evflt)
        _theme_data = dc(qtCompCTkHelps._theme_data)
        ThemeManager.set(self,style_values=self.stylevars)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    #updates Layout if a widget is configured in the layout
    def update(self):
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
    
    def pack(self,direction=["v","h"],**kwargs):
        if self.master.geomanage not in (None,"box/pack"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'box/pack' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            if direction not in ("v","h"): raise qtCompCTkErrs.orientationError(f"Invailid orientation {repr(direction)} for pack geometry manager")
            self.master.geomanage = "box/pack"
            self.master.layout = QVBoxLayout() if direction == "v" else QHBoxLayout() if direction == "h" else None
        self.master.layout.addWidget(self)
    
    def grid(self,row=0,column=0,rowspan=1,columnspan=1,**kwargs):
        if self.master.geomanage not in (None,"grid"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'grid' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            self.master.geomanage = "grid"
            self.master.layout = QGridLayout()
        self.geomanage_args = [row,column,rowspan,columnspan]
        self.master.layout.addWidget(self, row, column, rowspan, columnspan)

    def _add_to_master(self):
        if self.master.geomanage == "grid":
            self.master.layout.addWidget(self, *self.geomanage_args)
        elif self.master.geomanage == "box/pack":
            self.master.layout.addWidget(self)
        else: raise qtCompCTkErrs.layoutError(f"Unknown master geomanager: {repr(self.master.geomanage)}")
    
    def bind(self,act:str,cmd,evtype="keypress",cmdargs=(),cmdkwargs={}):
        self.cmd = cmd
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        
        if "<Button-" in act: evtype = "mouse-single"
        
        if evtype != "keypress":
            self.cmdtrigger = (evtype)
        else:
            self.cmdtrigger = (evtype,act)
        
    def get(self):
        return self.text()
    
    #Configures the value of an existing variable of this widget
    def configure(self,**kwargs):
        for key in list(kwargs.keys()):
            exec(f"self.{key} = {repr(kwargs[key])}",{"self":self})

class CTkCheckBox(QCheckBox):
    childs = []
    geomanage = None
    layout = None
    cmdtrigger = None
    cmd = None
    cmdargs = ()
    cmdkwargs = {}
    stylevars = {"switch_color":"fg_color","switch_button_color":"button_color","color":"text_color","bg_color":"bg_color"}

    def __init__(self,master:QWidget,text="",fg_color="",bg_color="",button_color="",text_color="",corner_radius=0,command=type,cmdargs=(),cmdkwargs={},**kwargs):
        super().__init__()

        #Init vars
        self.__name__ = "QCheckBox-" + qtCompCTkHelps.kg.genkey()
        self.master = master
        self.master.childs.append(self)
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.button_color = button_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.cmd = command
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        self.geomanage_args = []

        #Init properties
        self.setText(text)
        self.evflt = qtCompCTkHelps.KeyFilter()
        self.installEventFilter(self.evflt) #Starts the event manager for commands etc.
        _theme_data = dc(qtCompCTkHelps._theme_data)
        ThemeManager.set(self,style_values=self.stylevars)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    #updates Layout if a widget is configured in the layout
    def update(self):
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
    
    #pack/grid will create a new Layout in the master widget if there is none, else it will only add the widget to it
    def pack(self,direction=["v","h"],**kwargs):
        if self.master.geomanage not in (None,"box/pack"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'box/pack' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            if direction not in ("v","h"): raise qtCompCTkErrs.orientationError(f"Invailid orientation {repr(direction)} for pack geometry manager")
            self.master.geomanage = "box/pack"
            self.master.layout = QVBoxLayout() if direction == "v" else QHBoxLayout() if direction == "h" else None
        self.master.layout.addWidget(self)
    
    def grid(self,row=0,column=0,rowspan=1,columnspan=1,**kwargs):
        if self.master.geomanage not in (None,"grid"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'grid' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            self.master.geomanage = "grid"
            self.master.layout = QGridLayout()
        self.geomanage_args = [row,column,rowspan,columnspan]
        self.master.layout.addWidget(self, row, column, rowspan, columnspan)

    def _add_to_master(self):
        if self.master.geomanage == "grid":
            self.master.layout.addWidget(self, *self.geomanage_args)
        elif self.master.geomanage == "box/pack":
            self.master.layout.addWidget(self)
        else: raise qtCompCTkErrs.layoutError(f"Unknown master geomanager: {repr(self.master.geomanage)}")
    
    #bind bindes a command to a specific event onto the element
    def bind(self,act:str,cmd,evtype="keypress",cmdargs=(),cmdkwargs={}):
        self.cmd = cmd
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        
        if "<Button-" in act: evtype = "mouse-single"
        
        if evtype != "keypress":
            self.cmdtrigger = (evtype)
        else:
            self.cmdtrigger = (evtype,act)
        
        log(f"New command bound to Widget {repr(self.__name__)} with cmdargs {repr(cmdargs)} and kwargs {repr(kwargs)}",src=self.__name__,tpe="debug")
    
    def get(self):
        return self.isChecked()

    #Configures the value of an existing variable of this widget
    def configure(self,**kwargs):
        for key in list(kwargs.keys()):
            exec(f"self.{key} = {repr(kwargs[key])}",{"self":self})

class CTkSlider(QSlider):
    childs = []
    geomanage = None
    layout = None
    cmdtrigger = None
    cmd = None
    cmdargs = ()
    cmdkwargs = {}
    #            Qt Name   | Varname
    stylevars = {} #{}

    def __init__(self,master:QWidget,orientation="vertical",value=0,from_=0,to=100,number_of_steps=100,**kwargs):
        if orientation not in ("horizontal","vertical"): raise qtCompCTkErrs.orientationError(f"Orientation {repr(orientation)} is invailid for a QSlider")
        super().__init__(Qt.Vertical if orientation == "vertical" else Qt.Horizontal)

        #Init vars
        self.__name__ = "QSlider-" + qtCompCTkHelps.kg.genkey()
        self.master = master
        self.master.childs.append(self)
        self.geomanage_args = []

        #Init properties
        self.setValue(value)
        self.setMinimum(from_)
        self.setMaximum(to)
        self.setTickInterval(int((to-from_)/number_of_steps))
        self.evflt = qtCompCTkHelps.KeyFilter()
        self.installEventFilter(self.evflt)
        _theme_data = dc(qtCompCTkHelps._theme_data)
        ThemeManager.set(self, style_values=self.stylevars)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    #updates Layout if a widget is configured in the layout
    def update(self):
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
    
    def set(self,value):
        self.setValue(value)
    
    def pack(self,direction=["v","h"],**kwargs):
        if self.master.geomanage not in (None,"box/pack"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'box/pack' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            if direction not in ("v","h"): raise qtCompCTkErrs.orientationError(f"Invailid orientation {repr(direction)} for pack geometry manager")
            self.master.geomanage = "box/pack"
            self.master.layout = QVBoxLayout() if direction == "v" else QHBoxLayout() if direction == "h" else None
        self.master.layout.addWidget(self)
    
    def grid(self,row=0,column=0,rowspan=1,columnspan=1,**kwargs):
        if self.master.geomanage not in (None,"grid"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'grid' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            self.master.geomanage = "grid"
            self.master.layout = QGridLayout()
        self.geomanage_args = [row,column,rowspan,columnspan]
        self.master.layout.addWidget(self, row, column, rowspan, columnspan)

    def _add_to_master(self):
        if self.master.geomanage == "grid":
            self.master.layout.addWidget(self, *self.geomanage_args)
        elif self.master.geomanage == "box/pack":
            self.master.layout.addWidget(self)
        else: raise qtCompCTkErrs.layoutError(f"Unknown master geomanager: {repr(self.master.geomanage)}")
    
    def bind(self,act:str,cmd,evtype="keypress",cmdargs=(),cmdkwargs={}):
        self.cmd = cmd
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        
        if "<Button-" in act: evtype = "mouse-single"
        
        if evtype != "keypress":
            self.cmdtrigger = (evtype)
        else:
            self.cmdtrigger = (evtype,act)
        
    def get(self):
        return self.value()
    
    #Configures the value of an existing variable of this widget
    def configure(self,**kwargs):
        for key in list(kwargs.keys()):
            exec(f"self.{key} = {repr(kwargs[key])}",{"self":self})

class CTkTextbox(QTextEdit):
    childs = []
    geomanage = None
    layout = None
    cmdtrigger = None
    cmd = None
    cmdargs = ()
    cmdkwargs = {}
    stylevars = {"background-color":"bg_color","color":"text_color"}

    def __init__(self,master:QWidget,orientation="vertical",state="normal",bg_color="",text_color="",**kwargs):
        if orientation not in ("horizontal","vertical"): raise qtCompCTkErrs.orientationError(f"Orientation {repr(orientation)} is invailid for a QSlider")
        super().__init__() #Qt.Vertical if orientation == "vertical" else Qt.Horizontal)

        #Init vars
        self.__name__ = "QTextEdit-" + qtCompCTkHelps.kg.genkey()
        self.master = master
        self.master.childs.append(self)
        self.geomanage_args = []

        #Init properties
        self.bg_color = bg_color
        self.text_color = text_color
        self.state = state
        self.evflt = qtCompCTkHelps.KeyFilter()
        self.installEventFilter(self.evflt)
        _theme_data = dc(qtCompCTkHelps._theme_data)
        ThemeManager.set(self, style_values=self.stylevars)
        self.setReadOnly(True if state == "disabled" else False)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    #updates Layout if a widget is configured in the layout
    def update(self):
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
    
    def pack(self,direction=["v","h"],**kwargs):
        if self.master.geomanage not in (None,"box/pack"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'box/pack' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            if direction not in ("v","h"): raise qtCompCTkErrs.orientationError(f"Invailid orientation {repr(direction)} for pack geometry manager")
            self.master.geomanage = "box/pack"
            self.master.layout = QVBoxLayout() if direction == "v" else QHBoxLayout() if direction == "h" else None
        self.master.layout.addWidget(self)
    
    def grid(self,row=0,column=0,rowspan=1,columnspan=1,**kwargs):
        if self.master.geomanage not in (None,"grid"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'grid' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            self.master.geomanage = "grid"
            self.master.layout = QGridLayout()
        self.geomanage_args = [row,column,rowspan,columnspan]
        self.master.layout.addWidget(self, row, column, rowspan, columnspan)

    def _add_to_master(self):
        if self.master.geomanage == "grid":
            self.master.layout.addWidget(self, *self.geomanage_args)
        elif self.master.geomanage == "box/pack":
            self.master.layout.addWidget(self)
        else: raise qtCompCTkErrs.layoutError(f"Unknown master geomanager: {repr(self.master.geomanage)}")
    
    def bind(self,act:str,cmd,evtype="keypress",cmdargs=(),cmdkwargs={}):
        self.cmd = cmd
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        
        if "<Button-" in act: evtype = "mouse-single"
        
        if evtype != "keypress":
            self.cmdtrigger = (evtype)
        else:
            self.cmdtrigger = (evtype,act)
        
    def get(self):
        return self.toPlainText()

    def set(self,index:None,text:str,*args,**kwargs):
        txt = self.get()
        txtl = list(txt)
        txtl.insert(index,text)
        txt = ''.join(txtl)
        self.setPlainText(txt)
    
    def delete(self,first_ind,*args,last_ind=None,**kwargs):
        txt = self.get()
        if last_ind != tk.END:
            txt = txt[first_ind:]
            if last_ind != None: txt = txt[:(0-last_ind-first_ind)]
            self.setPlainText(txt)
        else: self.clear()
    
    #Configures the value of an existing variable of this widget
    def configure(self,**kwargs):
        for key in list(kwargs.keys()):
            exec(f"self.{key} = {repr(kwargs[key])}",{"self":self})
        self.setReadOnly(True if self.state == "disabled" else False)

class CTkOptionMenu(QComboBox):
    childs = []
    geomanage = None
    layout = None
    cmdtrigger = None
    cmd = None
    cmdargs = ()
    cmdkwargs = {}
    stylevars = {"color":"text_color","bg_color":"bg_color"}

    def __init__(self,master:QWidget,values=["No items available"],bg_color="",text_color="",**kwargs):
        super().__init__()

        #Init vars
        self.__name__ = "QComboBox-" + qtCompCTkHelps.kg.genkey()
        self.master = master
        self.master.childs.append(self)
        self.bg_color = bg_color
        self.text_color = text_color
        self.geomanage_args = []

        #Init properties
        self.values = values
        self.addItems(values)
        self.evflt = qtCompCTkHelps.KeyFilter()
        self.installEventFilter(self.evflt)
        _theme_data = dc(qtCompCTkHelps._theme_data)
        ThemeManager.set(self,style_values=self.stylevars)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    #updates Layout if a widget is configured in the layout
    def update(self):
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
    
    def pack(self,direction=["v","h"],**kwargs):
        if self.master.geomanage not in (None,"box/pack"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'box/pack' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            if direction not in ("v","h"): raise qtCompCTkErrs.orientationError(f"Invailid orientation {repr(direction)} for pack geometry manager")
            self.master.geomanage = "box/pack"
            self.master.layout = QVBoxLayout() if direction == "v" else QHBoxLayout() if direction == "h" else None
        self.master.layout.addWidget(self)
    
    def grid(self,row=0,column=0,rowspan=1,columnspan=1,**kwargs):
        if self.master.geomanage not in (None,"grid"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'grid' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            self.master.geomanage = "grid"
            self.master.layout = QGridLayout()
        self.geomanage_args = [row,column,rowspan,columnspan]
        self.master.layout.addWidget(self, row, column, rowspan, columnspan)

    def _add_to_master(self):
        if self.master.geomanage == "grid":
            self.master.layout.addWidget(self, *self.geomanage_args)
        elif self.master.geomanage == "box/pack":
            self.master.layout.addWidget(self)
        else: raise qtCompCTkErrs.layoutError(f"Unknown master geomanager: {repr(self.master.geomanage)}")
    
    def bind(self,act:str,cmd,evtype="keypress",cmdargs=(),cmdkwargs={}):
        self.cmd = cmd
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        
        if "<Button-" in act: evtype = "mouse-single"
        
        if evtype != "keypress":
            self.cmdtrigger = (evtype)
        else:
            self.cmdtrigger = (evtype,act)
        
    def get(self):
        return self.currentText()
    
    #Configures the value of an existing variable of this widget
    def configure(self,**kwargs):
        for key in list(kwargs.keys()):
            exec(f"self.{key} = {repr(kwargs[key])}",{"self":self})
        self.clear()
        self.addItems(self.values)

class CTkSwitch(QCheckBox):
    childs = []
    geomanage = None
    layout = None
    cmdtrigger = None
    cmd = None
    cmdargs = ()
    cmdkwargs = {}
    #            Qt Name   | Varname
    stylevars = {"bg_color":"bg_color"}

    def __init__(self,master:QWidget,text="",bg_color="",**kwargs):
        super().__init__()

        #Init vars
        self.__name__ = "QCheckBox-" + qtCompCTkHelps.kg.genkey()
        self.master = master
        self.master.childs.append(self)
        self.bg_color = bg_color
        self.geomanage_args = []

        #Init properties
        self.setText(text)
        self.evflt = qtCompCTkHelps.KeyFilter()
        self.installEventFilter(self.evflt)
        _theme_data = dc(qtCompCTkHelps._theme_data)
        ThemeManager.set(self, style_values=self.stylevars)

        #Done
        log(f"Initialized new {repr(self.__name__)}",src=self.__name__,tpe="info")
    
    #updates Layout if a widget is configured in the layout
    def update(self):
        for elm in self.childs:
            if elm.layout != None: elm.setLayout(elm.layout)
            try: elm.update()
            except: pass
    
    def pack(self,direction=["v","h"],**kwargs):
        if self.master.geomanage not in (None,"box/pack"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'box/pack' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            if direction not in ("v","h"): raise qtCompCTkErrs.orientationError(f"Invailid orientation {repr(direction)} for pack geometry manager")
            self.master.geomanage = "box/pack"
            self.master.layout = QVBoxLayout() if direction == "v" else QHBoxLayout() if direction == "h" else None
        self.master.layout.addWidget(self)
    
    def grid(self,row=0,column=0,rowspan=1,columnspan=1,**kwargs):
        if self.master.geomanage not in (None,"grid"): raise qtCompCTkErrs.layoutError(f"Geometry manager 'grid' is not compatible with {repr(self.master.geomanage)}")
        if self.master.geomanage == None:
            self.master.geomanage = "grid"
            self.master.layout = QGridLayout()
        self.geomanage_args = [row,column,rowspan,columnspan]
        self.master.layout.addWidget(self, row, column, rowspan, columnspan)

    def _add_to_master(self):
        if self.master.geomanage == "grid":
            self.master.layout.addWidget(self, *self.geomanage_args)
        elif self.master.geomanage == "box/pack":
            self.master.layout.addWidget(self)
        else: raise qtCompCTkErrs.layoutError(f"Unknown master geomanager: {repr(self.master.geomanage)}")
    
    def bind(self,act:str,cmd,evtype="keypress",cmdargs=(),cmdkwargs={}):
        self.cmd = cmd
        self.cmdargs = cmdargs
        self.cmdkwargs = cmdkwargs
        
        if "<Button-" in act: evtype = "mouse-single"
        
        if evtype != "keypress":
            self.cmdtrigger = (evtype)
        else:
            self.cmdtrigger = (evtype,act)
        
    def get(self):
        return 1 if self.isChecked() else 0

    def select(self):
        self.setChecked(True)
    
    def deselect(self):
        self.setChecked(False)
    
    #Configures the value of an existing variable of this widget
    def configure(self,**kwargs):
        for key in list(kwargs.keys()):
            exec(f"self.{key} = {repr(kwargs[key])}",{"self":self})
