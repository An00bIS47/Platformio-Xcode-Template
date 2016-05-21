#!/usr/bin/env python

import json
import subprocess
import sys
from os.path import expanduser

def getPorts():
    p = subprocess.Popen(["platformio", "serialports", "list", "--json-output"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out

def osascript(scpt):
    args = ["2", "2"]
    p = subprocess.Popen(["osascript", "-"] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(scpt)
    #print (p.returncode, stdout, stderr)
    return stdout

def buildScript(array, title, prompt):
    scpt = """
        on run {x, y}
            set asklist to ASLIST
            set selectedValue to {choose from list asklist with title "ASTITLE" with prompt "ASPROMPT" without multiple selections allowed}
        end run"""
    asklist = "{"

    for v in array:        #print v
        asklist += "\"" + v + "\","

    asklist = asklist[:-1] + "}"
    scpt = scpt.replace("ASLIST", asklist)
    scpt = scpt.replace("ASTITLE", title)
    scpt = scpt.replace("ASPROMPT", prompt)
    return scpt


def updateIni(iniFile, selectedPort):
    with open(iniFile,"r") as ini:
        newlines = []
        for line in ini.readlines():
            if (line.startswith("port =")) or (line.startswith("port=")):
                newlines.append("port = " + selectedPort + "\n")
            else:
                newlines.append(line)
    with open(iniFile, "w") as f:
        for line in newlines:
            f.write(line)

def main(argv):
    ports = []
    astitle = "PlatformIO Select Port:"
    jsonString=getPorts()
    allPorts = json.loads(jsonString)
    for port in allPorts:
        ports.append(port["description"])

    scpt = buildScript(ports, astitle, "Select the port:")

    selectedPort=osascript(scpt).strip()

    if selectedPort != "false":
        selectedPort=selectedPort.replace("/dev/cu.", "")        
        updateIni(sys.argv[1] + "/platformio.ini", selectedPort)

if __name__ == "__main__":
    main(sys.argv[1:])
