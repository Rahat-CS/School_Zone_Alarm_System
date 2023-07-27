import socket
import sys
from battery import Battery, GetBattLvl,GetLogs,GetSignctrNum,GetCallSchedule
from display import Display, GetDisplaySystem,GetDisplayVOlt,GetDisplayElementCur
from alarm import GetAlarmRing, GetAlarmStat
TCP_IP_PORT = 8007
UDP_PORT = 10080
def GetServerIP(UDPPortNo):
    serverAddress = '127.0.0.1'
    return serverAddress

def GetSignId():
    signId = '577-0402'
    return signId

def GetStatus():
    status = '82'
    return status

# ... Other functions (GetLogs, GetSignctrNum) go here ...

# Get TCP/IP Server Address
host = GetServerIP(UDP_PORT)
port = TCP_IP_PORT  # The port used by the server

szasSrv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
szasSrv.connect((host, port))

firstMsg = GetSignId() + ";" + GetStatus()

print(firstMsg)

szasSrv.sendall(firstMsg.encode())
session = True

while session:
    data = szasSrv.recv(1024)
    reply = "Error"

    # reformat received data including removing carriage return, line feed, etc., and decode to string
    data = data.strip().decode()

    print("Request: ", data)
    match data:
        case '<BTT?>':
            reply = GetBattLvl()

        case '<LOG?>':
            reply = GetLogs()

        case '<ADN?>':
            reply = GetSignctrNum()

        case '<END>':
            reply = '<ACK>'
            session = False

        case '<ITT?>':
            reply = GetCallSchedule()

        case '<DIS>':
            reply = GetDisplaySystem(0)

        case '<ALR>':
            reply = GetAlarmStat()

        case '<DIP>':
            reply = GetDisplayVOlt()

        case '<ESC?>':
            reply = GetDisplayElementCur()

        case _:
            reply = 'Unknown Req'
    szasSrv.sendall(reply.encode())

print("Session has ended")
