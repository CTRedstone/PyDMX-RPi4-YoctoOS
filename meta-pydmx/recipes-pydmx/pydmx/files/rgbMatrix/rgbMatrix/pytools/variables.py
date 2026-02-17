import sys
__main__ = "__main__"
FONTEFFECTS = {"reset":"\033[0m","bold":"\033[1m","darker":"\033[2m","curved":"\033[3m","underlined":"\033[4m","clrinvert":"\033[7m","gray":"\033[30m","red":"\033[31m","green":"\033[32m","yellow":"\033[33m","blue":"\033[34m","purple":"\033[35m","cyan":"\033[36m","white":"\033[37m"}
FE = FONTEFFECTS
currentFunctionName = lambda n=0: sys._getframe(n + 1).f_code.co_name
currentFuncName = currentFunctionName
cFN = currentFuncName
