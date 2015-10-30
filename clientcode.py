#!/usr/bin/python

import socket
import time
import datetime
import sys
from time import gmtime, strftime

serveraddress = ("149.171.37.223", 10000)
socks = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
	socks.sendto('',serveraddress)
	number_nonces = 1
	while number_nonces < 31:
		nonce, (serverIP, serverport) = socks.recvfrom(1024)
		sys.stdout.write("nonce received from server (%s) at port (%s)> %s\n" % (serverIP, serverport, nonce))
		timeEpoch = time.time() #
		timeEpochStr = "{:.5f}".format(timeEpoch)
		socks.sendto(nonce +'_' + timeEpochStr,(serverIP, serverport)) 
		timestampStr = datetime.datetime.fromtimestamp(timeEpoch).strftime('%Y-%m-%d %H:%M:%S.%f') 
		sys.stdout.write("nonce and timestamp (%s) sent back to server\n\n" % (timestampStr))
		number_nonces += 1
	sys.stdout.write("Start of new epoch\n\n")
	time.sleep(180)

