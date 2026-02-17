import prgbarWin as pbw

def cc():
	from json import load,dump
	with open("config.json","r") as cnf: config = load(cnf) #Load config file
	itms = [] #List for new Items
	itms2 = []
	names = []
	itmcnt = 0
	firstdouble = None
	pbw.clrtheme("black-orange.json")
	pgbw = pbw.initwin()
	pgbw = pbw.setinf(pgbw,inftxt="[PyDMX] Correcting Widget config")
	pgbw = pbw.setprg(pgbw)
	for item in config["window"]["elements"]:
		itmcnt += 1
		pgbw = pbw.setprg(pgbw,prgfloat=itmcnt/len(config["window"]["elements"]))
		if item in itms: #If the exact same data was existant before, the index of the double gets saved
			print(f"correctconfig: INFO: item {itmcnt}, already known (element has name \033[1m'{item['name'] if 'name' in list(item.keys()) else 'NONAME'}'\033[0m)")
			if firstdouble == None: firstdouble = itmcnt
			#del itms2[itms2.index(item)]
			#if "name" in item.keys() and item["name"] in names: del names[names.index(item["name"])]
		else:
			itms.append(item)
			#itms2.append(item)
			#if "name" in item.keys(): names.append(item["name"])
	pbw.endwin(pgbw)
	try:print(f"correctconfig: Totally {itmcnt} items, doubled {itmcnt-len(itms)}, {round(((itmcnt-len(itms))/itmcnt)*100,2)}% of total items doubled, first double detected at list position {firstdouble}")
	except ZeroDivisionError:
		print("correctconfig: Everything is fine!")
		return
	if firstdouble == None:
		print("correctconfig: Everything is fine!")
		return
	#print(f"Names of elements which are not doubled: {','.join(names)}")

	bfr = eval(f'config["window"]["elements"][:{firstdouble-1}]') #The Data of widgets gets shortned to the number where the first doubled data was discovered
	print(f"correctconfig: Resulted length of elements now: {len(bfr)}")
	config["window"]["elements"] = bfr
	with open("config.json","w+") as cnf: dump(config,cnf) #The config file gets saved again
	print("correctconfig: File saved")
