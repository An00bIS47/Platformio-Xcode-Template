#!/usr/bin/env python

import json
import subprocess
import sys
from os.path import expanduser

def getBoards():
    p = subprocess.Popen(["platformio", "boards", "--json-output"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out

def getVendors(jsonString):
    vendors=[]

    ab = json.loads(jsonString)
    #print json.dumps(boards, indent=4, sort_keys=True)
    for b in ab:
        for key, value in b.iteritems():
            if value["vendor"] not in vendors:
              vendors.append(value["vendor"])
    return sorted(vendors)

def getBoardsFromVendor(jsonString, vendor):
    boards=[]

    ab = json.loads(jsonString)
    #print json.dumps(ab, indent=4, sort_keys=True)
    for b in ab:
        for key, value in b.iteritems():
            if value["vendor"] == vendor:
                boards.append(value)
    return sorted(boards)

def getBoardFromName(jsonString, name):
    boards=[]

    ab = json.loads(jsonString)
    #print json.dumps(ab, indent=4, sort_keys=True)
    for b in ab:
        for key, value in b.iteritems():
            if value["name"] == name:
                value["type"] = key
                boards.append(value)
    return sorted(boards)

def osascript(scpt):
    args = ["2", "2"]
    p = subprocess.Popen(["osascript", "-"] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(scpt)
    #print (p.returncode, stdout, stderr)
    return stdout

def buildScript(array, title, prompt):
    scpt = '''
        on run {x, y}
            set asklist to ASLIST
            set selectedValue to {choose from list asklist with title "ASTITLE" with prompt "ASPROMPT" without multiple selections allowed}
        end run'''
    asklist = "{"

    for v in array:        #print v
        asklist += "\"" + v + "\","

    asklist = asklist[:-1] + "}"
    scpt = scpt.replace("ASLIST", asklist)
    scpt = scpt.replace("ASTITLE", title)
    scpt = scpt.replace("ASPROMPT", prompt)
    return scpt

def main(argv):
    boards=[]
    home = expanduser("~")
    templatePlist = home + "/Library/Developer/Xcode/Templates/Project Templates/PlatformIO/PlatformIO Project.xctemplate/TemplateInfo.plist"

    astitle = "PlatformIO Add Board:"

    jsonString="[" + getBoards() + "]"

    vendors = getVendors(jsonString)
    scpt = buildScript(vendors, astitle, "Select the board vendor:")
    try:
        vendor=osascript(scpt).strip()
    except IndexError:
        sys.exit(1)
        
    boardsDict = getBoardsFromVendor(jsonString, vendor)
    boardsList = []
    for b in boardsDict:
        boardsList.append(b["name"])

    scpt = buildScript(sorted(boardsList), astitle, "Select your board:")
    try:
        board=osascript(scpt).strip()
    except IndexError:
        sys.exit(1)


    board = getBoardFromName(jsonString, board)[0]
    #pprint(board)

    if len(board["frameworks"]) > 1:
        scpt = buildScript(sorted(board["frameworks"]), astitle, "Select the framework:")
        try:
            fw=osascript(scpt).strip()
        except IndexError:
            sys.exit(1)
    else:
        fw = board["frameworks"][0]


    if "name" in board:
        print "BOARD_NAME:       " + board["name"]
    if "type" in board:
        print "TYPE:             " + board["type"]
    if "vendor" in board:
        print "VENDOR:           " + board["vendor"]
    if "platform" in board:
        print "PLATFORM:         " + board["platform"]

    print "FRAMEWORK:        " + fw
    if "mcu" in board["build"]:
        print "MCU:              " + board["build"]["mcu"]
    if "extra_flags" in board["build"]:
        print "EXTRA_FLAGS:      " + board["build"]["extra_flags"]
    if "core" in board["build"]:
        print "CORE:             " + board["build"]["core"]
    if "f_cpu" in board["build"]:
        print "F_CPU:            " + str(board["build"]["f_cpu"])
    if "variant" in board["build"]:
        print "VARIANT:          " + board["build"]["variant"]
    if "f_flash" in board["build"]:
        print "F_FLASH:          " + str(board["build"]["f_flash"])
    if "maximum_ram_size" in board["upload"]:
        print "MAXIMUM_RAM_SIZE: " + str(board["upload"]["maximum_ram_size"])
    if "maximum_size" in board["build"]:
        print "MAXIMUM_SIZE:     " + str(board["build"]["maximum_size"])
    if "speed" in board["build"]:
        print "SPEED:            " + str(board["build"]["speed"])


    iniString = "\n[env:{0}]\nplatform = {1}\nframework = {2}\nboard = {3}\n".format(board["type"], board["platform"], fw, board["type"])
    print iniString
    with open(sys.argv[1] + "/platformio.ini", "a") as pioIni:
        pioIni.write(iniString)

    scpt = """
        on run {x, y}
            display dialog "Do you want to add this board to the PlatformIO Xcode template?" with title "PlatformIO Add Board" with icon file (POSIX file "/Applications/Xcode.app/Contents/Resources/xcode-project_Icon.icns" as text)
        end run"""

    answer=osascript(scpt).strip()

    if answer == "button returned:OK":
        subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\" dict", templatePlist])
        subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\" dict", templatePlist])
        subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"IO_FRAMEWORK\" string " + fw + "", templatePlist])
        if "mcu" in board["build"]:
            subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"PIO_MCU\" string " + board["build"]["mcu"] + "", templatePlist])
        if "platform" in board:
            subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"PIO_PLATFORM\" string " + board["platform"] + "", templatePlist])
        if "type" in board:
            subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"PIO_BOARD\" string " + board["type"] + "", templatePlist])
        if "maximum_size" in board["build"]:
            subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"PIO_MAXIMUM_SIZE\" string " + str(board["build"]["maximum_size"]) + "", templatePlist])
        if "maximum_ram_size" in board["upload"]:
            subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"PIO_MAXIMUM_RAM_SIZE\" string " + str(board["upload"]["maximum_ram_size"]) + "", templatePlist])
        if "core" in board["build"]:
            subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"PIO_CORE\" string " + board["build"]["core"] + "", templatePlist])
        if "extra_flags" in board["build"]:
            subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"PIO_EXTRA_FLAGS\" string " + board["build"]["extra_flags"] + "", templatePlist])
        if "f_cpu" in board["build"]:
            subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"PIO_F_CPU\" string " + str(board["build"]["f_cpu"]) + "", templatePlist])
        if "variant" in board["build"]:
            subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"PIO_VARIANT\" string " + board["build"]["variant"] + "", templatePlist])
        if "speed" in board["build"]:
            subprocess.call(["/usr/libexec/PlistBuddy", "-c", "Add :Options:0:Units:\"" +  board["name"]  +  "\":\"Macros\":\"PIO_SPEED\" string " + str(board["build"]["speed"]) + "", templatePlist])

    print "Done!"

if __name__ == "__main__":
    main(sys.argv[1:])
