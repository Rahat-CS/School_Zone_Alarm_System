import socket
import sys

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('192.168.21.83', 10000)
from datetime import datetime

now = datetime.now()

current_time = now.strftime("%H:%M:%S")

message = current_time + ': This is the message.  It will be repeated.' 
bytesToSend = str.encode(message)

try:

    # Send data
    print ('sending "%s"' % message)
    sent = sock.sendto(bytesToSend, server_address)

    # Receive response
    print ('waiting to receive')
    data, server = sock.recvfrom(4096)
    print ('received "%s"' % data)

finally:
    print ('closing socket')
    sock.close()
