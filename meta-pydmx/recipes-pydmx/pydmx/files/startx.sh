#!/bin/sh
/usr/bin/xinit /usr/bin/openbox-session -- :0 vt1 -nolisten tcp &
sleep 2
DISPLAY=:0 /usr/bin/python3 /opt/pydmx/__main__.py.py
