# PingClient.py
# Date: 23/06/2019
	# Simple UDP implementation to ping a server using UDP

# NOTE: I used Python3.7.3 available on CSE for this Exercise

from socket import *
import sys
import time
import datetime

try:
	if len(sys.argv) != 3: # Require 3 argv to be valid
		print ("Invalid input")
	serverHost, serverPort = sys.argv[1], int(sys.argv[2])
except:
	print ("some invalid input or something...")
	sys.exit()

rttList = []

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(1) # wait at most 1 second for a reply

for sequence in range(10):
	start = time.time() * 1000 # converting to milliseconds
	message = f"PING {str(sequence)} {datetime.datetime.now()} \r\n"
	clientSocket.sendto(message.encode('utf-8'),(serverHost, serverPort)) # Need to encode using utf-8
	try:
		modifiedMessage, serverAddress = clientSocket.recvfrom(2048) # serverAddress is address of socket sending the data
		rtt = (time.time() * 1000) - start
		rttList.append(rtt)
		print (f"ping to {serverHost}, seq = {sequence}, rtt = {rtt} ms")
	except: # timeout raises error if over the time
		print (f"ping to {serverHost}, seq = {sequence}, time out") # I assume time out is not included in RTT average so not appending to List

if rttList: # Assuming we get at least one response
	print (f"minimum rtt = {min(rttList)} ms")
	print (f"maximum rtt = {max(rttList)} ms")
	print (f"average rtt = {sum(rttList) / len(rttList)} ms")
else: # Listis empty and no reply
	print ("No response to any ping. 100% packet loss")

clientSocket.close()