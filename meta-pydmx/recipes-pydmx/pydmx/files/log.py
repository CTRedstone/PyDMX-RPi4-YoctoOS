class vars():
	logfile = True
	progname = ""
	logid = 0
	logfilepath = "log.html"
	ended = False

def write_log_to_file(state:bool): vars.logfile = state

def set_log_file_path(path:str): vars.logfilepath = path

def set_program_name(name:str): vars.progname = name

def init_logfile(title="Logfile"):
	with open(vars.logfilepath,"w+",encoding="UTF-8") as fle:
		fle.write(f"""
<head>
	<title>Log of '"""+vars.progname+"""'</title>
	<style>
		body{background-color:black;font-family:Monospace}
		button{font-size:11px;font-family:Monospace;background-color:black;color:white}
	</style>
	<script>
		function highlightline(lineid) {
			let span = document.getElementById("s-"+lineid);
			let btn = document.getElementById("b-"+lineid);
			if(span.style.backgroundColor == "") {
				if(span.style.color == "red") {
					span.style.backgroundColor = "darkred";
				} else if(span.style.color == "orange") {
					span.style.backgroundColor = "orangered";
				} else if(span.style.color == "lime") {
					span.style.backgroundColor = "green";
				} else if(span.style.color == "cyan") {
					span.style.backgroundColor = "darkcyan";
				} else if(span.style.color == "blue") {
					span.style.backgroundColor = "blueviolet";
				} else if(span.style.color == "white") {
					span.style.backgroundColor = "gray";
				} else {
					span.style.backgroundColor = "red";
				}
				btn.style.backgroundColor = "darkred";
			} else {
				span.style.backgroundColor = "";
				btn.style.backgroundColor = "";
			}
		}
	</script>
</head>
<body>
<h2 style="color:white">"""+title+"""</h2>""")

def log(src:str,tpe:str,txt:str): #Log function for GUI functions
	vars.logid += 1
	clr = "31" if tpe.lower() in ("err","error","fatal") else "32" if tpe.lower() in ("okay") else "33" if tpe.lower() in ("warn","warning") else "36" if tpe.lower() in ("info") else "34" if tpe.lower() in ("debug") else "0"
	mdclr = "red" if tpe.lower() in ("err","error","fatal") else "lime" if tpe.lower() in ("okay") else "orange" if tpe.lower() in ("warn","warning") else "cyan" if tpe.lower() in ("info") else "blue" if tpe.lower() in ("debug") else "white"
	print(f"\033[{clr}m[{vars.progname}/{src}] {tpe.upper()}: {txt}\033[0m")
	try:
		with open(vars.logfilepath,"a",encoding="UTF-8") as fle:
			LB = "\n"
			fle.write(f"<button onclick='highlightline(\"{vars.logid}\")' id='b-{vars.logid}'><b>H</b></button><span style='color:white'> {vars.logid}: </span><span style='color:{mdclr}' id='s-{vars.logid}'><b>[{vars.progname}/{src}]</b> <i><b>{tpe.upper()}</b></i>: {'<br>'.join(txt.split(LB))}</span><br>\n")
	except: pass

def end_log_file():
	vars.ended = True
	with open(vars.logfilepath,"a",encoding="UTF-8") as fle: fle.write("</body")
