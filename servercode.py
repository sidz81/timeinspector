#!/usr/bin/python

import socket
import struct
import time
import datetime
import sys
import pexpect
from time import gmtime, strftime

# We want unbuffered stdout so we can provide live feedback for
# each TTL. You could also use the "-u" flag to Python.
class flushfile(file):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()

sys.stdout = flushfile(sys.stdout)

def mytraceroute(dest_name):
    dest_addr = socket.gethostbyname(dest_name)
    port = 33434
    max_hops = 30
    icmp = socket.getprotobyname('icmp')
    udp = socket.getprotobyname('udp')
    ttl = 1
    curr_addr = None
    curr_name = None
    closest_router = list()

    while True:
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
        
        # Build the GNU timeval struct (seconds, microseconds)
        timeout = struct.pack("ll", 5, 0)
        
        # Set the receive timeout so we behave more like regular traceroute
        recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeout)
        
        recv_socket.bind(("", port))
        sys.stdout.write(" %d  " % ttl)
        send_socket.sendto("", (dest_name, port))
        finished = False
        tries = 3
	stars = 0

        while not finished and tries > 0:
            try:
                _, curr_addr = recv_socket.recvfrom(512)
                finished = True
                curr_addr = curr_addr[0]
                try:
                    curr_name = socket.gethostbyaddr(curr_addr)[0]
                except socket.error:
                    curr_name = curr_addr
            except socket.error as (errno, errmsg):
                tries = tries - 1
                sys.stdout.write("* ")
		stars +=1
        
        send_socket.close()
        recv_socket.close()
        
        if not finished:
            pass
        
        if curr_addr is not None and stars is not 3:
            curr_host = "%s (%s)" % (curr_name, curr_addr)
	    closest_router.append(curr_addr)

        else:
            curr_host = ""
        sys.stdout.write("%s\n" % (curr_host))

        ttl += 1
        if curr_addr == dest_addr or ttl > max_hops:
		
            break
    closest_router.reverse()
    
    return closest_router

if __name__ == "__main__":
	serveraddress = ("149.171.37.223", 10000)
	sockr = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sockr.bind(serveraddress)
	closest_router = list()
	first_nonce = 1001
	while True:
		data, (clientIP, clientport) = sockr.recvfrom(1024)
		sys.stdout.write("client IP: %s\n" % (clientIP))
		sys.stdout.write("client port: %s\n" % (clientport))
		nonce_sent = first_nonce
		max_nonces = nonce_sent + 30
		while nonce_sent < max_nonces:
			data = str(nonce_sent)
			sockr.sendto(data,(clientIP, clientport))
			sys.stdout.write("nonce sent> %s\n" % (nonce_sent))
			nonce_clientTime, (clientIP, clientport) = sockr.recvfrom(1024)
			nonce_received, clientEpochtimeStr = nonce_clientTime.split("_",1)
			serverEpochtime = time.time()
			serverEpochtime = float("{:.5f}".format(serverEpochtime))
			serverEpochtimeStr = "{:.5f}".format(serverEpochtime)
			serverTime = datetime.datetime.fromtimestamp(serverEpochtime).strftime('%Y-%m-%d %H:%M:%S.%f')
			clientEpochtime = float(clientEpochtimeStr)
			clientTime = datetime.datetime.fromtimestamp(clientEpochtime).strftime('%Y-%m-%d %H:%M:%S.%f')   
			sys.stdout.write("nonce received back> %s\n" % (nonce_received))
			sys.stdout.write("client time received> %s\n" % (clientTime))      
			sys.stdout.write("server time> %s\n" % (serverTime))
			with open("serverLog.csv", "a") as myfile:
		    		myfile.write(clientIP + ", " +nonce_received + ", " +clientEpochtimeStr+ ", " +clientTime +", " +serverEpochtimeStr+ ", " +serverTime+ "\n")
		    		myfile.close()
			if nonce_sent != max_nonces:
				time.sleep(5)
				nonce_sent +=1
				first_nonce = nonce_sent
			else:
				break

		sys.stdout.write("Starting traceroute to the client IP (%s)\n" % (clientIP))

		closest_router = mytraceroute(clientIP)
		i=0
		if closest_router[i] == clientIP:
			i=1
		else:
			pass

		while 1:
			sys.stdout.write("closest router> %s\n" % (closest_router[i]))
			sys.stdout.write("Pinging the closest router (%s) to the client\n" % (closest_router[i]))
			ping_argument = 'ping -c 5'+' '+ closest_router[i]

			child = pexpect.spawn(ping_argument)
			linefinal = ''

			while 1:
				line = child.readline()
	       	 		if not line: break
				sys.stdout.write("%s\n" % (line))
				linefinal = line
			if linefinal[0] != 'r':
				sys.stdout.write("No ping reply. Updating the closest router\n")
				i+=1
			else:	
				first_half, last_half = linefinal.split("=")
				rttmin, avgrtt, maxrtt, mdevrtt = last_half.split("/")
				with open("serverLog.csv", "a") as myfile:
					myfile.write(", " + ", "+ ", "+", "+ ", "+ ", " +avgrtt + ", " + maxrtt +"\n")	
					myfile.close()
				break
