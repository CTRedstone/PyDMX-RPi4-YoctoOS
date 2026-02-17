import requests

class vars():
    svrAddr = None
    svrPort = None
    svrAuth = None
    svrUser = "tmp"
    svrApi = "nouse"
    svrPortCall = True
    nA = {"value":"Server Connection not initialized"}

def genAddr(route:str): #Generates the Webaddress for serveraccess with auth code
    return f"http://{vars.svrAddr}{':'+str(vars.svrPort) if vars.svrPortCall else ''}/auth/{vars.svrAuth}{route}"

def avail(): return False if vars.svrAddr == None else True #Checks if the Connection got initialized already

def initConnection(addr:str,port=None,user="tmp",apikey="57011775879609982748744976979491543174906912157392739747944194985323410135758917609097663236693078570737574414714417448319455133388095300041963663793196078923855783256544861547856679448068889432829308902564710477058371919746063401451317178394474509340176916638637960508088635873433743756819678387254334242430539894437048054085407308729114937610145794097088689487514756523027089563889151109833515166747343343313077122850705156897998281305821426915736101654486950604513033683434770518785569502253441180856447514895"):
    vars.svrAddr = addr
    vars.svrPort = port
    vars.svrPortCall = True if port != None else False
    vars.svrUser = user if user != None else vars.svrUser
    vars.svrApi = apikey if apikey != None else vars.svrApi
    #Request a connect key from server
    try: vars.svrAuth = requests.get(f"http://{addr}:{port}/connect" if vars.svrPortCall else f"http://{vars.svrAddr}/connect").json()["value"]
    except: vars.svrAuth = requests.post(f"http://{addr}:{port}/connect" if vars.svrPortCall else f"http://{vars.svrAddr}/connect",json={"user":vars.svrUser,"apikey":vars.svrApi}).json()["value"]
    if " " in list(vars.svrAuth):
        vars.svrAuth = None
        raise TypeError("Connect response from server was unexpected/faulty - Was the userdata correct?")

def closeConnection(): #Removes Server connection again
    if not avail(): return vars.nA
    resp = requests.get(genAddr("/close")).json()
    vars.svrAddr = None
    vars.svrPort = None
    vars.svrAuth = None
    return resp

def sendMessage(msg:str,path:str): #simple POST request, only with the option of the "value" parameter in data
    if not avail(): return vars.nA
    return requests.post(genAddr(path),json={"value":msg}).json()

def sendData(data:dict,path:str): #POST request, with fully custom data
    if not avail(): return vars.nA
    return requests.post(genAddr(path),json=data).json()

def callPath(path:str): #simple GET request
    if not avail(): return vars.nA
    return requests.get(genAddr(path)).json()
